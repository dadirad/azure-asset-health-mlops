# Cost Notes (Azure)

## Purpose
This document highlights the primary cost drivers for the Asset Health Anomaly Detection reference implementation and practical levers to control spend. Milestone A runs locally. Milestones B/C introduce Azure services.

## Primary cost drivers (typical)
### 1) Compute for training and feature engineering
- If using Azure ML compute or Databricks clusters, compute hours are the main driver.
- Costs increase with higher data volume, larger feature windows, and retraining frequency.

**Controls**
- Start with small SKUs and scale only when needed.
- Schedule/auto-terminate compute where possible.
- Use incremental feature builds and avoid full reprocessing.

### 2) Online inference / API hosting
- Container Apps costs are driven by:
  - CPU/memory requested
  - number of replicas (scale-out)
  - request volume and concurrency

**Controls**
- Set conservative CPU/memory requests and tune after measuring.
- Configure scale-to-zero for low-traffic demo environments (if acceptable).
- Use batching or asynchronous scoring for high-volume scenarios.

### 3) Data ingestion and storage
- Event Hub / messaging costs depend on throughput and retention.
- Storage depends on retention period, write frequency, and data format.

**Controls**
- Use compressed columnar formats for historical telemetry (for example Parquet/Delta).
- Define retention tiers (hot/warm/cold) and archive older data.
- Keep raw telemetry immutable; store derived features separately.

### 4) Observability (Application Insights / Log Analytics)
- Cost is driven by telemetry volume (logs, traces, metrics) and retention.

**Controls**
- Set sampling for high-volume request traces.
- Reduce noisy logs; log structured summaries rather than full payloads.
- Tune retention to match operational needs.

## Cost-aware architecture decisions (reference)
- Prefer unsupervised baselines early to reduce labeling and iterative training overhead.
- Use deterministic feature engineering to reduce repeated experimentation waste.
- Separate batch processing from online scoring to keep the API lightweight.

## “Demo environment” guidance
For a portfolio/demo deployment:
- Keep training local or on minimal compute.
- Deploy scoring with minimal resources.
- Enable monitoring with limited retention and sampling.
- Document the path to scale, rather than running full-scale services continuously.
