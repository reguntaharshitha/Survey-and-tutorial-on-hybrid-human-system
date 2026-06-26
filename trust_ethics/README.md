# Trust & Confidence Training

This folder contains the training utilities to build a confidence-calibration model and update trust metrics stored in the database.

Files added:
- `trust_ml.py` — trainer implementation (creates `trust_ethics/models/confidence_model.joblib`).
- `management/commands/train_confidence.py` — management command to run training and update trust metrics.

Requirements
- The project `requirements.txt` already includes `scikit-learn`, `pandas`, and `joblib`.
- Run this command from the project root (the directory with `manage.py`) so Django settings are loaded.

Usage

- Train model (recommended):

```powershell
cd d:\project11_survay_tutorial_HAI\hais_project1
python manage.py train_confidence
```

- Train and update trust metrics for all users (may take time):

```powershell
python manage.py train_confidence --update-all
```

- Train and then update one user by id:

```powershell
python manage.py train_confidence --update-user 123
```

- Skip training and only update (requires existing saved model):

```powershell
python manage.py train_confidence --no-train --update-user 123
```

Notes
- The trainer uses historical `Feedback` linked to `AIResponse` as a proxy for "ground truth" (ratings or agreement/correction). If no such feedback exists, training will fail with a helpful message.
- Trained model stored at: `trust_ethics/models/confidence_model.joblib`
- You can schedule training via cron/Celery or run manually after a period of new feedback has accumulated.

Next steps (optional):
- Add a unit test ensuring `build_dataset` handles empty datasets gracefully.
- Add a periodic Celery task to retrain daily/weekly.
