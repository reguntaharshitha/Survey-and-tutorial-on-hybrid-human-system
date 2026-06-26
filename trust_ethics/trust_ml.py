import os
import joblib
import logging
import numpy as np
import pandas as pd
from django.conf import settings
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from feedback.models import Feedback
from user_interaction.models import AIResponse, UserInput
from .models import TrustMetric
from django.contrib.auth import get_user_model
import re

logger = logging.getLogger(__name__)


class ConfidenceTrainer:
    """Train a regressor to predict the "true" confidence of AI outputs.

    It uses historical feedback (ratings or agreement/correction) as a proxy
    for ground-truth correctness and trains a model that maps response-level
    features to a calibrated confidence score in [0,1].
    """

    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler()
        self.calibrator = None
        self.vectorizer = None
        self.model_dir = os.path.join(settings.BASE_DIR, 'trust_ethics', 'models')
        self.model_path = os.path.join(self.model_dir, 'confidence_model.joblib')
        self.latest_name = 'confidence_model_latest.joblib'
        os.makedirs(self.model_dir, exist_ok=True)
        self.load_model()

    def load_model(self):
        # prefer latest copy if present
        latest_path = os.path.join(self.model_dir, getattr(self, 'latest_name', 'confidence_model_latest.joblib'))
        path_to_load = None
        if os.path.exists(latest_path):
            path_to_load = latest_path
        elif os.path.exists(self.model_path):
            path_to_load = self.model_path

        if path_to_load:
            try:
                data = joblib.load(path_to_load)
                self.model = data.get('model')
                self.scaler = data.get('scaler', self.scaler)
                self.calibrator = data.get('calibrator', None)
                self.vectorizer = data.get('vectorizer', None)
                self.model_path = path_to_load
            except Exception:
                logger.exception('Failed to load model from %s', path_to_load)
                self.model = None

    def build_dataset(self):
        """Build a training DataFrame from Feedback and AIResponse records.

        Features considered:
        - raw_confidence: AIResponse.confidence_score (model-provided)
        - response_length: number of characters in response_data
        - reasoning_length: number of characters in reasoning
        - timestamp_hour: hour of day (may capture diurnal variation)
        - time_since_input: seconds between input and response (if available)

        Target:
        - rating in [0,1] if available (rating 1-5 scaled to 0-1)
        - agreement -> 1.0, correction -> 0.0 when rating missing
        """
        rows = []
        texts = []

        qs = Feedback.objects.select_related('ai_response', 'user').filter(ai_response__isnull=False)
        for fb in qs:
            ar = fb.ai_response
            # derive target
            if fb.rating is not None:
                target = max(0.0, min(1.0, (fb.rating - 1) / 4.0))
            else:
                if fb.feedback_type == 'agreement':
                    target = 1.0
                elif fb.feedback_type == 'correction':
                    target = 0.0
                else:
                    # skip if no useful target
                    continue

            response_text = (ar.response_data or '')
            reasoning_text = (ar.reasoning or '')
            # simple text-derived features
            words = re.findall(r"\w+", response_text)
            word_count = len(words)
            avg_word_len = float(np.mean([len(w) for w in words]) if words else 0.0)
            punctuation_count = len(re.findall(r"[\.!?,;:]", response_text))
            stopword_fraction = 0.0
            # basic heuristics for complexity
            complexity = avg_word_len * (1 + punctuation_count / (word_count + 1))
            input_ts = None
            input_obj = getattr(ar, 'user_input', None)
            if input_obj is not None and input_obj.timestamp is not None:
                input_ts = input_obj.timestamp
            time_since_input = None
            if input_ts is not None and ar.timestamp is not None:
                time_since_input = (ar.timestamp - input_ts).total_seconds()

            row = {
                'raw_confidence': float(getattr(ar, 'confidence_score', 0.0) or 0.0),
                'response_length': len(response_text),
                'reasoning_length': len(reasoning_text),
                'word_count': word_count,
                'avg_word_len': avg_word_len,
                'punctuation_count': punctuation_count,
                'text_complexity': complexity,
                'timestamp_hour': ar.timestamp.hour if ar.timestamp else 0,
                'time_since_input': time_since_input if time_since_input is not None else 0.0,
                'user_id': fb.user.id,
                'target': float(target),
            }
            rows.append(row)
            texts.append(response_text)

        if not rows:
            return None

        df = pd.DataFrame(rows)

        # Build text-derived vector features: prefer SentenceTransformer if available
        try:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv('SENT_TRANSFORMER_MODEL', 'all-MiniLM-L6-v2')
            embedder = SentenceTransformer(model_name)
            embeddings = embedder.encode(texts, show_progress_bar=False)
            emb_df = pd.DataFrame(embeddings)
            emb_df.columns = [f'emb_{i}' for i in range(emb_df.shape[1])]
            df = pd.concat([df.reset_index(drop=True), emb_df.reset_index(drop=True)], axis=1)
            self.vectorizer = ('sbert', model_name)
        except Exception:
            # fallback: TF-IDF (keeps model dependency light)
            tfidf = TfidfVectorizer(max_features=200, stop_words='english')
            Xtf = tfidf.fit_transform(texts).toarray()
            tfdf = pd.DataFrame(Xtf, columns=[f'tfidf_{i}' for i in range(Xtf.shape[1])])
            df = pd.concat([df.reset_index(drop=True), tfdf.reset_index(drop=True)], axis=1)
            self.vectorizer = ('tfidf_obj', tfidf)

        return df

    def train(self, test_size=0.2, random_state=42):
        df = self.build_dataset()
        if df is None or df.empty:
            raise RuntimeError('No training data available. Collect feedback linked to AI responses.')
        # include numeric features and any vectorized text columns
        base_cols = ['raw_confidence', 'response_length', 'reasoning_length', 'timestamp_hour', 'time_since_input',
                     'word_count', 'avg_word_len', 'punctuation_count', 'text_complexity']
        text_cols = [c for c in df.columns if c.startswith('emb_') or c.startswith('tfidf_')]
        X = df[base_cols + text_cols].copy()
        y = df['target'].values

        # scale numeric features into 0-1 range for stability
        to_scale = ['response_length', 'reasoning_length', 'time_since_input', 'word_count', 'avg_word_len', 'punctuation_count', 'text_complexity']
        X[to_scale] = self.scaler.fit_transform(X[to_scale])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

        # Use a robust regressor
        model = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=random_state)
        model.fit(X_train, y_train)

        # Calibrate predictions using isotonic regression for better probability calibration
        try:
            preds = model.predict(X_train)
            iso = IsotonicRegression(out_of_bounds='clip')
            iso.fit(preds, y_train)
            self.calibrator = iso
        except Exception:
            self.calibrator = None

        # versioned save
        ts = pd.Timestamp.utcnow().strftime('%Y%m%dT%H%M%SZ')
        version_path = os.path.join(self.model_dir, f'confidence_model_{ts}.joblib')
        latest_path = os.path.join(self.model_dir, self.latest_name)
        save_obj = {'model': model, 'scaler': self.scaler, 'calibrator': self.calibrator}
        if isinstance(self.vectorizer, tuple) and self.vectorizer[0] == 'tfidf_obj':
            save_obj['vectorizer'] = self.vectorizer[1]
        else:
            save_obj['vectorizer'] = self.vectorizer
        joblib.dump(save_obj, version_path)
        # also keep a latest copy
        joblib.dump(save_obj, latest_path)
        self.model_path = latest_path
        self.model = model

        # Compute simple evaluation
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        logger.info(f"ConfidenceTrainer.train finished: train_r2={train_score:.4f} test_r2={test_score:.4f} saved_version={version_path}")
        return {'train_r2': train_score, 'test_r2': test_score}

    def predict_confidence(self, ai_response: AIResponse):
        if self.model is None:
            self.load_model()
        if self.model is None:
            # Fallback: return raw confidence if no trained model
            return float(getattr(ai_response, 'confidence_score', 0.0) or 0.0)

        response_text = (ai_response.response_data or '')
        reasoning_text = (ai_response.reasoning or '')
        input_obj = getattr(ai_response, 'user_input', None)
        time_since_input = 0.0
        if input_obj is not None and input_obj.timestamp and ai_response.timestamp:
            time_since_input = (ai_response.timestamp - input_obj.timestamp).total_seconds()

        words = re.findall(r"\w+", response_text)
        word_count = len(words)
        avg_word_len = float(np.mean([len(w) for w in words]) if words else 0.0)
        punctuation_count = len(re.findall(r"[\.!?,;:]", response_text))
        complexity = avg_word_len * (1 + punctuation_count / (word_count + 1))

        feat = {
            'raw_confidence': float(getattr(ai_response, 'confidence_score', 0.0) or 0.0),
            'response_length': len(response_text),
            'reasoning_length': len(reasoning_text),
            'timestamp_hour': ai_response.timestamp.hour if ai_response.timestamp else 0,
            'time_since_input': time_since_input,
            'word_count': word_count,
            'avg_word_len': avg_word_len,
            'punctuation_count': punctuation_count,
            'text_complexity': complexity,
        }

        X = pd.DataFrame([feat])
        # apply scaler to the same columns
        to_scale = ['response_length', 'reasoning_length', 'time_since_input', 'word_count', 'avg_word_len', 'punctuation_count', 'text_complexity']
        X[to_scale] = self.scaler.transform(X[to_scale])

        # If vectorizer is a TF-IDF object, transform response text and add columns
        if isinstance(self.vectorizer, tuple) and self.vectorizer[0] == 'tfidf_obj':
            tfidf = self.vectorizer[1]
            try:
                vec = tfidf.transform([response_text]).toarray()
                tfcols = [f'tfidf_{i}' for i in range(vec.shape[1])]
                for i, col in enumerate(tfcols):
                    X[col] = vec[0, i]
            except Exception:
                # if transform fails, proceed without tfidf features
                pass

        pred = self.model.predict(X)[0]
        # Clip into [0,1]
        pred = float(max(0.0, min(1.0, pred)))
        # apply calibrator if present
        if self.calibrator is not None:
            try:
                pred = float(self.calibrator.predict([pred])[0])
            except Exception:
                pass

        logger.debug(f"Predicted calibrated confidence {pred:.3f} for AIResponse id={getattr(ai_response, 'id', 'unknown')}")
        return pred

    def list_saved_models(self):
        files = []
        for fn in os.listdir(self.model_dir):
            if fn.startswith('confidence_model_') and fn.endswith('.joblib'):
                files.append(fn)
        files.sort(reverse=True)
        return files

    def rollback_to(self, filename):
        path = os.path.join(self.model_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        data = joblib.load(path)
        # write to latest
        latest_path = os.path.join(self.model_dir, self.latest_name)
        joblib.dump(data, latest_path)
        self.load_model()
        return latest_path

    def update_trust_metrics_for_user(self, user_id, metric_type='ai_output_confidence'):
        """Aggregate recent AI responses for a user and write/update TrustMetric rows."""
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise

        # fetch recent AIResponses for the user
        ai_responses = AIResponse.objects.select_related('user_input').filter(user_input__session__user=user).order_by('-timestamp')[:100]
        if not ai_responses:
            return None

        confidences = []
        for ar in ai_responses:
            c = self.predict_confidence(ar)
            confidences.append(c)

        avg_confidence = float(np.mean(confidences))
        std_confidence = float(np.std(confidences))

        # create a TrustMetric entry
        tm = TrustMetric.objects.create(
            user=user,
            metric_type=metric_type,
            value=avg_confidence,
            confidence=1.0 - std_confidence,  # higher std reduces confidence of the metric
        )
        return {'avg_confidence': avg_confidence, 'std_confidence': std_confidence, 'trust_metric_id': tm.id}


# singleton
trainer = ConfidenceTrainer()
