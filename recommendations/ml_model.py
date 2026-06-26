import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import os
from django.conf import settings

class RecommendationEngine:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = os.path.join(settings.BASE_DIR, 'recommendations', 'models', 'recommendation_model.joblib')
        self.load_model()
    
    def load_model(self):
        """Load trained model if exists, otherwise create new one"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
            else:
                self.train_initial_model()
        except:
            self.train_initial_model()
    
    def train_initial_model(self):
        """Train initial model with sample data"""
        # Sample user behavior data
        np.random.seed(42)
        n_samples = 1000
        
        # Generate sample features: [interaction_frequency, decision_confidence, emotional_variability, learning_speed]
        X = np.random.randn(n_samples, 4)
        X[:, 0] = np.random.exponential(2, n_samples)  # Interaction frequency (positive)
        X[:, 1] = np.random.beta(2, 2, n_samples)      # Decision confidence (0-1)
        X[:, 2] = np.random.gamma(2, 1, n_samples)     # Emotional variability
        X[:, 3] = np.random.normal(0.5, 0.2, n_samples) # Learning speed
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Cluster users into 4 behavior types
        self.model = KMeans(n_clusters=4, random_state=42)
        self.model.fit(X_scaled)
        
        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
    
    def predict_user_cluster(self, user_features):
        """Predict which cluster the user belongs to"""
        if self.model is None:
            self.load_model()
        
        features_scaled = self.scaler.transform([user_features])
        cluster = self.model.predict(features_scaled)[0]
        return cluster
    
    def generate_recommendations(self, user_features, user_history=None):
        """Generate personalized recommendations based on user features"""
        cluster = self.predict_user_cluster(user_features)
        
        # Recommendation templates for each cluster
        recommendations = {
            0: [  # Analytical users
                "Try breaking down complex problems into smaller, manageable tasks",
                "Use systematic decision-making frameworks for important choices",
                "Document your reasoning process for future reference"
            ],
            1: [  # Intuitive users
                "Trust your initial instincts but validate with data",
                "Practice mindfulness to enhance intuitive decision-making",
                "Balance quick decisions with periodic reflection"
            ],
            2: [  # Emotional users
                "Develop emotional awareness in decision contexts",
                "Practice separating emotional responses from logical analysis",
                "Use emotional signals as data points, not drivers"
            ],
            3: [  # Methodical users
                "Experiment with more flexible approaches occasionally",
                "Set time limits for decision-making to avoid over-analysis",
                "Incorporate creative brainstorming sessions"
            ]
        }
        
        cluster_recommendations = recommendations.get(cluster, [
            "Continue exploring different decision-making approaches",
            "Balance analysis with action",
            "Regularly review and adjust your strategies"
        ])
        
        return cluster_recommendations

# Singleton instance
recommendation_engine = RecommendationEngine()