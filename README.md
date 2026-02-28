# Azure Asset Health MLOps

End-to-end Azure reference implementation for asset health anomaly detection: telemetry ingestion, feature engineering, Isolation Forest baseline, API scoring, observability, and an EAM work-order integration pattern.

## What this repository demonstrates
- Deterministic feature engineering pipeline for equipment telemetry (time-windowed features)
- Unsupervised anomaly detection baseline (Isolation Forest) with repeatable training and saved model artifacts
- API-ready scoring interface (local CLI first, then FastAPI service)
- Production-minded practices: tests, versioned artifacts, logging/observability hooks, and runbook-style documentation

## Target use case
Detect abnormal asset behavior early using telemetry signals such as vibration, temperature, pressure, current, and operating mode. Convert anomaly signals into actionable maintenance outputs (for example, a work-order payload suitable for EAM/CMMS integration).

## Architecture (high level)
**Telemetry Source** → **Feature Pipeline** → **Model Training** → **Model Artifacts** → **Scoring API** → **Monitoring/Alerts** → **EAM Work Order Payload**

> Implementation starts locally (Milestone A), then progresses to a containerized API and Azure deployment.

## Repository structure
- `src/` — feature engineering, training, and prediction scripts
- `api/` — API service (FastAPI) for online scoring (Milestone B)
- `tests/` — unit tests (feature pipeline and scoring contracts)
- `docs/` — architecture notes, runbook, security, and cost considerations
- `data/` — local datasets or generated sample telemetry (optional)

## Milestones
### Milestone A: Local baseline (current)
- Train Isolation Forest on synthetic or public telemetry dataset
- Save model artifacts and feature schema metadata
- Provide `predict.py` for local scoring
- Add unit tests for the feature pipeline

### Milestone B: API + container
- Wrap scoring in a FastAPI endpoint (`POST /score`)
- Dockerize the service for consistent execution

### Milestone C: Azure deployment + observability
- Deploy scoring service to Azure Container Apps (fast path)
- Add Application Insights telemetry and basic alerting
- Add CI pipeline for tests and container build/deploy

## Quickstart
Quickstart steps will be added after Milestone A scripts are committed:
- `src/train.py`
- `src/predict.py`
- `tests/test_features.py`
