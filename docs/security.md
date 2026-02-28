# Security and Governance Notes

## Scope
This document summarizes the security posture and governance considerations for the Asset Health Anomaly Detection reference implementation. Milestone A runs locally. Milestones B/C introduce an API and Azure deployment.

## Data handling
- **Telemetry sensitivity:** Treat asset telemetry as potentially sensitive operational data (may reveal production capacity, process performance, or safety conditions).
- **PII:** The reference data contract does not require PII. Avoid adding operator/user identifiers unless required, and document purpose/retention if added.
- **Integrity:** Prefer immutable raw telemetry storage and append-only processing to support auditability.

## Identity and access (Azure target state)
- **Service identity:** Use **Managed Identity** for the scoring service (Container Apps) to access Azure resources.
- **Secrets:** Store secrets in **Azure Key Vault**. Do not hardcode keys or connection strings in code or configs.
- **Least privilege:** Use RBAC roles scoped to only required resources (Key Vault secrets access, storage read, logging write).

## API security (Milestone B/C)
- **Authentication:** Require auth for the scoring endpoint (for example, Entra ID / OAuth2) rather than anonymous access.
- **Authorization:** Restrict who can call scoring (app/workflow identities). Separate read-only monitoring roles from deployer roles.
- **Input validation:** Enforce schema validation on requests (required fields, numeric ranges, timestamp parsing).
- **Rate limiting:** Add throttling to reduce abuse and protect downstream dependencies.

## Logging and monitoring
- **Centralized telemetry:** Use Application Insights (Milestone C) for request traces, exceptions, and performance metrics.
- **Audit trails:** Log model version, threshold policy, and bucket timestamp for each scoring request.
- **Alerting:** Alert on elevated error rates, latency spikes, and unexpected changes in anomaly volume.

## Model risk considerations
- **Training-serving consistency:** The feature pipeline is deterministic and versioned via metadata to reduce mismatch risk.
- **Threshold governance:** Threshold is stored as an explicit policy in `models/metadata.json`. Changing thresholds should be treated as a controlled configuration change.
- **Data drift:** Add simple drift proxies over time (feature distribution checks) and review anomaly rate trends.

## Abuse and failure scenarios
- **Poisoning / manipulation:** If telemetry is attacker-controlled, an adversary could attempt to shift distributions. Mitigations include integrity controls on ingestion, anomaly rate monitoring, and separating “alert” from “action” via human approval gates.
- **Denial of service:** Protect scoring endpoint with auth + throttling + request size limits.
- **False positives/negatives:** Treat scoring as decision support. Route high-severity signals to review workflows before automated maintenance actions.

## Recommended hardening steps (future)
- Add signed/hashed telemetry ingestion for integrity (where feasible)
- Implement model registry + approval workflow for production releases
- Add regression tests for scoring outputs and contract compatibility
- Add structured logs for SIEM ingestion (security monitoring)
