# Architecture

## Goal
Detect abnormal asset behavior from telemetry (vibration, temperature, pressure, rpm, etc.) and emit an actionable maintenance signal that can be integrated with an EAM/CMMS workflow (for example, a work order payload).

## Reference architecture (Milestone A → C)
**Telemetry Source** → **Feature Engineering** → **Model Training** → **Model Artifacts** → **Scoring Service** → **Observability** → **EAM Integration**

### Components
- **Telemetry Source (simulated / dataset)**
  - Input records: `asset_id`, `timestamp`, and sensor values
- **Feature Engineering (src/features.py)**
  - Time-bucket aggregation (default 5 minutes)
  - Statistical features per sensor (mean/std/min/max)
  - Delta features (change in mean over time)
  - Missingness features
- **Model Training (src/train.py)**
  - Baseline: Isolation Forest for unsupervised anomaly detection
  - Output: versioned model artifact + metadata (feature schema, threshold policy)
- **Scoring Interface (src/predict.py)**
  - Loads model + metadata
  - Scores incoming telemetry windows
  - Returns anomaly score + decision + work-order payload stub
- **Observability (Milestone C)**
  - Application Insights for logs, request metrics, and basic alerting
- **EAM/CMMS Integration Pattern**
  - Output contract produces a `work_order_payload` JSON object suitable for downstream posting to an EAM API or message bus

## Data contract (input)
Each telemetry record must include:
- `asset_id` (string)
- `timestamp` (ISO-8601 string or datetime)
- One or more numeric sensor fields (for example: `temp_c`, `vibration`, `pressure_bar`, `rpm`)

## Output contract (scoring result)
- `asset_id`
- `bucket_start`
- `anomaly_score_last`
- `is_anomalous_last`
- `threshold`
- `work_order_payload` (integration stub)

## Design decisions (high level)
- **Unsupervised baseline first**: avoids label dependency while enabling early value and quick iteration.
- **Deterministic feature pipeline**: ensures training-serving consistency and testability.
- **Threshold policy stored as metadata**: makes scoring behavior explicit and versioned.
- **API-ready scoring**: CLI first (fast iteration), then FastAPI + Container Apps (production-oriented path).
