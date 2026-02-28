# Architecture Decisions (ADRs)

This document records key architecture decisions for the Azure Asset Health MLOps reference implementation. Each decision includes context, the choice made, and tradeoffs.

---

## ADR-001: Start with unsupervised anomaly detection baseline
**Status:** Accepted  
**Context:** Predictive maintenance datasets often lack reliable failure labels early in a project. We need a working baseline that can deliver value quickly and provide operational feedback.  
**Decision:** Use **Isolation Forest** as the initial anomaly detection model.  
**Consequences / Tradeoffs:**
- Pros: works without labels; fast to train; easy to explain; good first milestone.
- Cons: anomaly score requires calibration; may produce false positives; less specific than supervised failure prediction.

---

## ADR-002: Deterministic feature engineering as a first-class component
**Status:** Accepted  
**Context:** Training-serving skew is a common failure mode in production ML.  
**Decision:** Implement a deterministic, testable feature pipeline (`src/features.py`) and include unit tests validating schema and determinism.  
**Consequences / Tradeoffs:**
- Pros: reduces skew risk; supports repeatability; improves maintainability.
- Cons: requires upfront engineering effort; feature changes must be managed carefully.

---

## ADR-003: Threshold policy stored in metadata
**Status:** Accepted  
**Context:** Anomaly detection requires a decision boundary to trigger alerts or downstream actions. Thresholds must be explicit and versioned.  
**Decision:** Store threshold policy (percentile and computed threshold value) in `models/metadata.json` alongside the model artifact.  
**Consequences / Tradeoffs:**
- Pros: transparent scoring behavior; supports controlled changes and rollback.
- Cons: threshold may need environment-specific calibration; percentiles may not generalize.

---

## ADR-004: Container Apps as the first Azure deployment target
**Status:** Accepted  
**Context:** We want the fastest path to a deployable, demoable scoring service that still reflects real solution architecture patterns.  
**Decision:** Deploy the scoring service as a containerized API (FastAPI) to **Azure Container Apps** in Milestone C.  
**Consequences / Tradeoffs:**
- Pros: fast delivery; standard microservice pattern; easy integration with enterprise systems; clear observability story.
- Cons: model registry/promotion workflows require additional work; less “Azure ML platform” centric.

---

## ADR-005: Azure ML managed endpoints as an enhancement path
**Status:** Proposed  
**Context:** Many enterprise environments require governed model lifecycles (registry, approvals, staged rollout).  
**Decision:** Add an optional deployment path using **Azure ML managed online endpoints** after the Container Apps path is established.  
**Consequences / Tradeoffs:**
- Pros: strong MLOps signal; native registry/versioning; controlled releases.
- Cons: more setup; longer time-to-first-demo.

---

## ADR-006: EAM/CMMS integration via a work-order payload contract
**Status:** Accepted  
**Context:** The value of predictive maintenance is realized only when signals become actionable operations (inspection, maintenance, work orders).  
**Decision:** Standardize output to include a `work_order_payload` stub that can be posted to an EAM API or message bus.  
**Consequences / Tradeoffs:**
- Pros: demonstrates integration readiness; decouples scoring from action; supports human approval gates.
- Cons: real EAM integration details vary (SAP, Maximo, ServiceNow); requires adapter mapping per target system.

---

## ADR-007: Observability via Application Insights
**Status:** Accepted  
**Context:** Production ML requires visibility into failures, latency, and behavior shifts (anomaly volume).  
**Decision:** Use **Application Insights** for traces, exceptions, request metrics, and basic alerting in Milestone C.  
**Consequences / Tradeoffs:**
- Pros: integrates with Azure-native monitoring; supports dashboards and alerts.
- Cons: telemetry volume can drive cost; requires sampling/tuning.
