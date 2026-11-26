from datetime import datetime, timezone

from features.engineering import FEATURE_COLUMNS, extract_features_from_edit
from tests.conftest import make_edit


class TestExtractFeatures:
    def test_basic_features(self):
        edit = make_edit(
            edit_size_delta=50,
            length_old=1000,
            length_new=1050,
            comment_length=9,
            is_bot=False,
            is_anonymous=False,
            is_minor=False,
            namespace=0,
            timestamp=datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc),
        )
        features = extract_features_from_edit(edit)

        assert features["edit_size_delta"] == 50
        assert features["abs_edit_size_delta"] == 50
        assert features["length_old"] == 1000
        assert features["length_new"] == 1050
        assert features["comment_length"] == 9
        assert features["is_bot"] == 0
        assert features["is_anonymous"] == 0
        assert features["is_minor"] == 0
        assert features["namespace"] == 0
        assert features["hour_of_day"] == 14
        assert features["day_of_week"] == 5  # Saturday
        assert features["is_large_deletion"] == 0
        assert features["is_new_page"] == 0
        assert features["has_comment"] == 1

    def test_large_deletion(self):
        edit = make_edit(edit_size_delta=-1000)
        features = extract_features_from_edit(edit)
        assert features["is_large_deletion"] == 1

    def test_new_page(self):
        edit = make_edit(length_old=0, length_new=500, edit_size_delta=500)
        features = extract_features_from_edit(edit)
        assert features["is_new_page"] == 1

    def test_no_comment(self):
        edit = make_edit(comment="", comment_length=0)
        features = extract_features_from_edit(edit)
        assert features["has_comment"] == 0

    def test_anonymous_feature(self):
        edit = make_edit(is_anonymous=True)
        features = extract_features_from_edit(edit)
        assert features["is_anonymous"] == 1

    def test_all_feature_columns_present(self):
        edit = make_edit()
        features = extract_features_from_edit(edit)
        for col in FEATURE_COLUMNS:
            assert col in features, f"Missing feature: {col}"

    def test_size_ratio(self):
        edit = make_edit(length_old=100, edit_size_delta=-50)
        features = extract_features_from_edit(edit)
        assert features["size_ratio"] == 0.5

    def test_size_ratio_zero_length(self):
        edit = make_edit(length_old=0, edit_size_delta=100)
        features = extract_features_from_edit(edit)
        # Should not divide by zero
        assert features["size_ratio"] == 100.0
