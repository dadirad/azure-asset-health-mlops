# Runbook (Operations)

## Purpose
This runbook describes how to train the baseline model, score telemetry, and validate behavior with tests. It also defines expected failure modes and basic troubleshooting steps.

## Local operations (Milestone A)

### Train the model
- Expected outputs:
  - `models/isolation_forest.joblib`
  - `models/metadata.json`
  - `sample_payload.json` (generated if you run training locally)

### Score telemetry
- Input: JSON list of telemetry records
- Output: anomaly score and `work_order_payload` stub

### Run tests
- Focus: feature pipeline determinism, schema, and required inputs

## Failure modes and troubleshooting

### Missing artifacts
**Symptom:** scoring fails with “Missing model file” or “Missing metadata file”
- **Cause:** training has not been run to generate artifacts
- **Fix:** run training (Milestone A) to regenerate `models/` artifacts

### Input schema errors
**Symptom:** “Missing required column(s)” or timestamp parse errors
- **Cause:** `asset_id`/`timestamp` missing or timestamp not parseable
- **Fix:** validate input schema; ensure ISO-8601 timestamps

### Unexpected NaNs / empty feature output
**Symptom:** model scoring returns no buckets or errors on empty data
- **Cause:** too few rows in a bucket or sensor fields missing
- **Fix:** increase input rows per asset; verify sensor columns are present

### Model behavior questions
**Symptom:** too many alerts or too few alerts
- **Cause:** threshold policy not calibrated to environment
- **Fix:** adjust percentile in training; consider per-asset thresholds; add simple drift checks

## Production notes (Milestone C)
Planned operational controls once deployed:
- Application Insights logging and basic alerting
- Versioned model artifacts and rollback to prior model versions
- Authentication and authorization for scoring endpoint
- Rate limiting and request validation
