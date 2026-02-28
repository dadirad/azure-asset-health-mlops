from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd

from src.features import FeatureConfig, build_features


MODEL_PATH = Path("models/isolation_forest.joblib")
META_PATH = Path("models/metadata.json")


def load_metadata() -> Dict[str, Any]:
    if not META_PATH.exists():
        raise FileNotFoundError(f"Missing metadata file: {META_PATH}. Run src/train.py first.")
    return json.loads(META_PATH.read_text())


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing model file: {MODEL_PATH}. Run src/train.py first.")
    return joblib.load(MODEL_PATH)


def score(telemetry_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    meta = load_metadata()
    model = load_model()

    telemetry = pd.DataFrame(telemetry_records)
    feats = build_features(telemetry, config=FeatureConfig(window_minutes=int(meta["feature_window_minutes"])))
    feature_cols = meta["feature_columns"]

    # Align feature columns (defensive)
    for c in feature_cols:
        if c not in feats.columns:
            feats[c] = 0.0

    X = feats[feature_cols].copy()

    normality = model.decision_function(X)
    anomaly_score = (-1.0) * normality

    threshold = float(meta["anomaly_threshold"])
    is_anomalous = anomaly_score >= threshold

    # Summarize last bucket (most recent) for the primary result
    feats_sorted = feats.sort_values(["asset_id", "bucket_start"])
    last_row = feats_sorted.iloc[-1]

    result = {
        "asset_id": str(last_row["asset_id"]),
        "bucket_start": str(last_row["bucket_start"]),
        "anomaly_score_last": float(anomaly_score[-1]),
        "is_anomalous_last": bool(is_anomalous[-1]),
        "threshold": threshold,
        "buckets_scored": int(len(anomaly_score)),
        "work_order_payload": {
            "asset_id": str(last_row["asset_id"]),
            "detected_at": str(last_row["bucket_start"]),
            "signal": "asset_health_anomaly",
            "severity": "high" if bool(is_anomalous[-1]) else "low",
            "recommended_action": "Inspect asset and review recent telemetry trend",
            "model": {
                "type": meta.get("model_type"),
                "threshold": threshold,
            },
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Score telemetry records for asset anomaly detection.")
    parser.add_argument("--input", required=True, help="Path to JSON file containing telemetry records (list).")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    records = json.loads(in_path.read_text())
    if not isinstance(records, list) or len(records) == 0:
        raise ValueError("Input JSON must be a non-empty list of telemetry records.")

    out = score(records)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
