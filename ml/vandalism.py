from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from features.engineering import FEATURE_COLUMNS, extract_features_from_edit

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "vandalism_xgb.joblib"


class VandalismClassifier:
    def __init__(self, model: XGBClassifier | None = None):
        self.model = model

    @classmethod
    def train(
        cls,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> "VandalismClassifier":
        """Train an XGBoost classifier for vandalism detection."""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Handle class imbalance
        n_neg = (y_train == 0).sum()
        n_pos = (y_train == 1).sum()
        scale_pos_weight = n_neg / max(n_pos, 1)

        model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            random_state=random_state,
            eval_metric="logloss",
        )
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        report = classification_report(y_test, y_pred, target_names=["clean", "vandalism"])
        logger.info(f"Vandalism classifier report:\n{report}")

        return cls(model=model)

    def save(self, path: Path | None = None):
        path = path or MODEL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        logger.info(f"Model saved to {path}")

    @classmethod
    def load(cls, path: Path | None = None) -> "VandalismClassifier":
        path = path or MODEL_PATH
        if not path.exists():
            raise FileNotFoundError(f"No model found at {path}")
        model = joblib.load(path)
        return cls(model=model)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return vandalism probability for each row."""
        return self.model.predict_proba(X)[:, 1]

    def predict_single(self, edit) -> float:
        """Score a single Edit object. Returns vandalism probability."""
        features = extract_features_from_edit(edit)
        X = pd.DataFrame([features], columns=FEATURE_COLUMNS)
        proba = self.model.predict_proba(X)[0, 1]
        return float(proba)
