from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from features.engineering import FEATURE_COLUMNS
from ml.vandalism import VandalismClassifier
from tests.conftest import make_edit


def _make_training_data(n_clean=100, n_vandalism=20):
    """Generate synthetic training data."""
    rng = np.random.RandomState(42)
    rows = []
    labels = []

    for _ in range(n_clean):
        rows.append({
            "edit_size_delta": rng.randint(-200, 200),
            "abs_edit_size_delta": rng.randint(0, 200),
            "length_old": rng.randint(500, 10000),
            "length_new": rng.randint(500, 10000),
            "comment_length": rng.randint(5, 100),
            "is_bot": rng.choice([0, 1], p=[0.7, 0.3]),
            "is_anonymous": 0,
            "is_minor": rng.choice([0, 1]),
            "namespace": 0,
            "hour_of_day": rng.randint(0, 24),
            "day_of_week": rng.randint(0, 7),
            "size_ratio": rng.uniform(0, 0.3),
            "is_large_deletion": 0,
            "is_new_page": 0,
            "has_comment": 1,
        })
        labels.append(0)

    for _ in range(n_vandalism):
        rows.append({
            "edit_size_delta": rng.randint(-5000, -500),
            "abs_edit_size_delta": rng.randint(500, 5000),
            "length_old": rng.randint(500, 10000),
            "length_new": rng.randint(0, 500),
            "comment_length": rng.randint(0, 3),
            "is_bot": 0,
            "is_anonymous": 1,
            "is_minor": 0,
            "namespace": 0,
            "hour_of_day": rng.randint(0, 24),
            "day_of_week": rng.randint(0, 7),
            "size_ratio": rng.uniform(0.5, 10.0),
            "is_large_deletion": 1,
            "is_new_page": 0,
            "has_comment": 0,
        })
        labels.append(1)

    X = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    y = pd.Series(labels, name="is_vandalism")
    return X, y


class TestVandalismClassifier:
    def test_train_and_predict(self):
        X, y = _make_training_data()
        clf = VandalismClassifier.train(X, y, test_size=0.2)

        proba = clf.predict(X)
        assert len(proba) == len(X)
        assert all(0 <= p <= 1 for p in proba)

    def test_predict_single(self):
        X, y = _make_training_data()
        clf = VandalismClassifier.train(X, y)

        edit = make_edit(
            edit_size_delta=-3000,
            is_anonymous=True,
            comment="",
            comment_length=0,
            length_old=5000,
            length_new=2000,
            timestamp=datetime(2024, 6, 15, 3, 0, tzinfo=timezone.utc),
        )
        score = clf.predict_single(edit)
        assert 0 <= score <= 1

    def test_save_and_load(self, tmp_path):
        X, y = _make_training_data()
        clf = VandalismClassifier.train(X, y)

        model_path = tmp_path / "test_model.joblib"
        clf.save(model_path)

        loaded = VandalismClassifier.load(model_path)
        proba_original = clf.predict(X)
        proba_loaded = loaded.predict(X)
        np.testing.assert_array_almost_equal(proba_original, proba_loaded)

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            VandalismClassifier.load(tmp_path / "nonexistent.joblib")

    def test_class_imbalance_handling(self):
        # Highly imbalanced data (5% positive)
        X, y = _make_training_data(n_clean=190, n_vandalism=10)
        clf = VandalismClassifier.train(X, y)
        # Should still produce probabilities
        proba = clf.predict(X)
        assert proba.max() > 0.3  # model should detect at least some vandalism
