from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd


REQUIRED_RAW_COLUMNS = ["asset_id", "timestamp"]


@dataclass(frozen=True)
class FeatureConfig:
    """
    Feature engineering config for asset telemetry.

    window_minutes:
        The aggregation window in minutes for time-bucketed features.
    min_rows_per_bucket:
        Buckets with fewer rows than this are dropped.
    """
    window_minutes: int = 5
    min_rows_per_bucket: int = 3


def _ensure_required_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_RAW_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}")


def _coerce_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce", utc=True)
    if out["timestamp"].isna().any():
        raise ValueError("One or more rows have invalid 'timestamp' values.")
    return out


def build_features(
    telemetry_df: pd.DataFrame,
    *,
    config: FeatureConfig = FeatureConfig(),
    sensor_columns: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """
    Build deterministic, time-bucketed features per asset.

    Input schema:
      - asset_id (str)
      - timestamp (datetime or parseable string)
      - sensor columns (float/int)

    Output schema (example):
      - asset_id
      - bucket_start
      - <sensor>__mean, __std, __min, __max
      - <sensor>__delta_mean (mean - previous mean per asset)
      - missing_ratio (fraction of NaNs among sensor fields)
      - row_count (rows in bucket)
    """
    if telemetry_df is None or telemetry_df.empty:
        raise ValueError("telemetry_df is empty.")

    _ensure_required_columns(telemetry_df)
    df = _coerce_timestamp(telemetry_df)

    # Identify sensor columns
    if sensor_columns is None:
        sensor_columns = [
            c for c in df.columns
            if c not in ("asset_id", "timestamp")
        ]
    sensor_columns = list(sensor_columns)

    if not sensor_columns:
        raise ValueError("No sensor columns found. Provide sensor_columns or include sensor fields.")

    # Coerce sensors numeric
    work = df[["asset_id", "timestamp"] + sensor_columns].copy()
    for c in sensor_columns:
        work[c] = pd.to_numeric(work[c], errors="coerce")

    # Missingness feature at raw-row level
    work["missing_ratio_row"] = work[sensor_columns].isna().mean(axis=1)

    # Bucket timestamps
    window = f"{int(config.window_minutes)}min"
    work["bucket_start"] = work["timestamp"].dt.floor(window)

    # Aggregate
    agg_map = {c: ["mean", "std", "min", "max"] for c in sensor_columns}
    agg_map["missing_ratio_row"] = ["mean"]
    agg_map["timestamp"] = ["count"]

    grouped = (
        work.groupby(["asset_id", "bucket_start"], as_index=False)
        .agg(agg_map)
    )

    # Flatten columns
    flat_cols: List[str] = ["asset_id", "bucket_start"]
    for col in grouped.columns[2:]:
        # columns are tuples after agg: (name, stat)
        if isinstance(col, tuple):
            name, stat = col
            if name == "timestamp" and stat == "count":
                flat_cols.append("row_count")
            elif name == "missing_ratio_row" and stat == "mean":
                flat_cols.append("missing_ratio")
            else:
                flat_cols.append(f"{name}__{stat}")
        else:
            flat_cols.append(str(col))

    grouped.columns = flat_cols

    # Drop low-volume buckets
    grouped = grouped[grouped["row_count"] >= int(config.min_rows_per_bucket)].copy()

    # Delta features: per asset, for each sensor mean
    mean_cols = [f"{c}__mean" for c in sensor_columns if f"{c}__mean" in grouped.columns]
    grouped.sort_values(["asset_id", "bucket_start"], inplace=True)

    for mc in mean_cols:
        grouped[f"{mc}__delta"] = grouped.groupby("asset_id")[mc].diff()

    # Clean up infinities
    grouped.replace([np.inf, -np.inf], np.nan, inplace=True)

    # For baseline, fill remaining NaNs with 0 in feature columns only
    feature_cols = [c for c in grouped.columns if c not in ("asset_id", "bucket_start")]
    grouped[feature_cols] = grouped[feature_cols].fillna(0.0)

    return grouped


def get_feature_columns(features_df: pd.DataFrame) -> List[str]:
    """Return model-ready feature columns from the engineered feature frame."""
    if features_df is None or features_df.empty:
        raise ValueError("features_df is empty.")
    cols = [c for c in features_df.columns if c not in ("asset_id", "bucket_start")]
    if not cols:
        raise ValueError("No feature columns found.")
    return cols
