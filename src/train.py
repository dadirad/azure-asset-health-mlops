from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.features import FeatureConfig, build_features, get_feature_columns


ARTIFACT_DIR = Path("models")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def generate_synthetic_telemetry(
    *,
    n_assets: int = 5,
    hours: int = 12,
    freq_seconds: int = 30,
    anomaly_rate: float = 0.02,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic telemetry suitable for anomaly detection demos.
    Produces a mix of normal behavior and injected anomalies (spikes/drift).
    """
    rng = np.random.default_rng(seed)
    rows = []
    start = pd.Timestamp.utcnow().floor("min")

    asset_ids = [f"A-{i:03d}" for i in range(1, n_assets + 1)]
    n_points = int((hours * 3600) / freq_seconds)

    for asset_id in asset_ids:
        base_temp = rng.normal(60, 3)
        base_vib = rng.normal(1.5, 0.2)
        base_press = rng.normal(35, 2)
        base_rpm = rng.normal(1800, 50)

        drift = 0.0

        for i in range(n_points):
            ts = start + pd.Timedelta(seconds=i * freq_seconds)

            # gradual drift occasionally
            if rng.random() < 0.001:
                drift += rng.normal(0.02, 0.01)

            temp = base_temp + drift + rng.normal(0, 0.7)
            vib = base_vib + rng.normal(0, 0.05)
            press = base_press + rng.normal(0, 0.4)
            rpm = base_rpm + rng.normal(0, 10)

            is_anom = rng.random() < anomaly_rate
            if is_anom:
                # spike anomalies
                temp += rng.normal(12, 3)
                vib += rng.normal(1.2, 0.3)
                press += rng.normal(6, 2)
                rpm += rng.normal(250, 80)

            rows.append(
                {
                    "asset_id": asset_id,
                    "timestamp": ts.isoformat(),
                    "temp_c": float(temp),
                    "vibration": float(vib),
                    "pressure_bar": float(press),
                    "rpm": float(rpm),
                }
            )

    df = pd.DataFrame(rows)

    # Inject missingness bursts
    mask = rng.random(len(df)) < 0.01
    df.loc[mask, "vibration"] = np.nan

    return df


def train_isolation_forest(X: pd.DataFrame, seed: int = 42) -> IsolationForest:
    model = IsolationForest(
        n_estimators=250,
        contamination="auto",
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X)
    return model


def compute_threshold(scores: np.ndarray, percentile: float = 95.0) -> float:
    # Higher score means "more anomalous" in our convention below.
    return float(np.percentile(scores, percentile))


def main() -> None:
    # 1) Generate or load telemetry
    telemetry = generate_synthetic_telemetry()

    # 2) Feature engineering
    feats = build_features(telemetry, config=FeatureConfig(window_minutes=5, min_rows_per_bucket=3))
    feature_cols = get_feature_columns(feats)
    X = feats[feature_cols].copy()

    # 3) Train baseline model
    model = train_isolation_forest(X)

    # 4) Score training data to set a threshold policy
    # IsolationForest: decision_function higher is more normal.
    # We convert to anomaly_score where higher is more anomalous.
    normality = model.decision_function(X)
    anomaly_score = (-1.0) * normality
    threshold = compute_threshold(anomaly_score, percentile=95.0)

    # 5) Persist artifacts
    model_path = ARTIFACT_DIR / "isolation_forest.joblib"
    meta_path = ARTIFACT_DIR / "metadata.json"

    joblib.dump(model, model_path)

    metadata: Dict = {
        "model_type": "IsolationForest",
        "feature_columns": feature_cols,
        "feature_window_minutes": 5,
        "threshold_percentile": 95.0,
        "anomaly_threshold": threshold,
        "training_rows": int(X.shape[0]),
        "created_utc": pd.Timestamp.utcnow().isoformat(),
    }

    meta_path.write_text(json.dumps(metadata, indent=2))

    # 6) Write a small sample payload for prediction demo (single asset slice)
    sample = telemetry[telemetry["asset_id"] == telemetry["asset_id"].iloc[0]].head(40)
    Path("sample_payload.json").write_text(sample.to_json(orient="records", indent=2))

    print("Training complete.")
    print(f"Saved model: {model_path}")
    print(f"Saved metadata: {meta_path}")
    print("Wrote: sample_payload.json")


if __name__ == "__main__":
    main()
