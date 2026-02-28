import pandas as pd
import pytest

from src.features import FeatureConfig, build_features, get_feature_columns


def _sample_df():
    return pd.DataFrame(
        [
            {"asset_id": "A-001", "timestamp": "2026-01-01T00:00:00Z", "temp_c": 60.0, "vibration": 1.4},
            {"asset_id": "A-001", "timestamp": "2026-01-01T00:00:30Z", "temp_c": 60.5, "vibration": 1.5},
            {"asset_id": "A-001", "timestamp": "2026-01-01T00:01:00Z", "temp_c": 61.0, "vibration": None},
            {"asset_id": "A-001", "timestamp": "2026-01-01T00:01:30Z", "temp_c": 60.7, "vibration": 1.6},
            {"asset_id": "A-001", "timestamp": "2026-01-01T00:02:00Z", "temp_c": 60.2, "vibration": 1.4},
        ]
    )


def test_build_features_outputs_expected_columns():
    df = _sample_df()
    feats = build_features(df, config=FeatureConfig(window_minutes=1, min_rows_per_bucket=1))
    assert "asset_id" in feats.columns
    assert "bucket_start" in feats.columns
    assert "row_count" in feats.columns
    assert "missing_ratio" in feats.columns
    assert "temp_c__mean" in feats.columns
    assert "vibration__mean" in feats.columns


def test_get_feature_columns_excludes_identifiers():
    df = _sample_df()
    feats = build_features(df, config=FeatureConfig(window_minutes=1, min_rows_per_bucket=1))
    cols = get_feature_columns(feats)
    assert "asset_id" not in cols
    assert "bucket_start" not in cols
    assert len(cols) > 0


def test_build_features_is_deterministic_for_same_input():
    df = _sample_df()
    feats1 = build_features(df, config=FeatureConfig(window_minutes=1, min_rows_per_bucket=1))
    feats2 = build_features(df, config=FeatureConfig(window_minutes=1, min_rows_per_bucket=1))
    pd.testing.assert_frame_equal(feats1.reset_index(drop=True), feats2.reset_index(drop=True))


def test_build_features_raises_on_missing_required_columns():
    df = pd.DataFrame([{"timestamp": "2026-01-01T00:00:00Z", "temp_c": 60.0}])
    with pytest.raises(ValueError):
        build_features(df)
