# ADR-002: Prometheus Observability Integrated Into Unified Incident Context

**Date:** 2026-05-15  
**Status:** Accepted  
**Decision Type:** Architecture / Observability Engineering  
**Owners:** Autonomous Ops Platform Engineering  

---

# Context

Autonomous Ops Platform was designed to evolve beyond isolated troubleshooting scripts into a unified operational intelligence platform for SRE, Kubernetes operations, DevOps, and autonomous incident response.

A major architectural objective of the platform is:

**AI agents should reason on complete operational context rather than fragmented infrastructure signals.**

During early implementation, Prometheus observability integration was introduced as a standalone utility.

Implementation location:

```text
app/tools/prometheus/metrics_tools.py
```

Initial execution model:

```bash
python -m app.tools.prometheus.metrics_tools
```

Operator interaction:

```text
Enter pod name:
Enter namespace:
```

The utility then queried Prometheus for selected metrics.

This approach validated basic observability integration, but it represented a prototype-oriented design rather than platform architecture.

---

# Problem Statement

The standalone Prometheus model created multiple architectural and operational problems.

---

## Fragmented Operational Workflow

Prometheus metrics required manual execution outside the core incident workflow.

Workflow became:

```text
Detect incident
    ↓
Collect Kubernetes signals
    ↓
Manually query Prometheus
    ↓
Copy results mentally
    ↓
Run AI reasoning
```

This introduced unnecessary human dependency.

---

## Broken Context Engineering Model

The platform architecture aims to normalize all relevant infrastructure signals before AI reasoning begins.

Standalone Prometheus querying violated this principle.

AI agents received incomplete context.

Example missing signals:

- memory pressure telemetry
- CPU telemetry
- restart counters
- observability correlation signals

This reduced reasoning quality.

---

## Human Dependency Risk

Operational intelligence should not depend on manual operator enrichment.

Manual steps create:

- inconsistency
- human error
- incomplete RCA context
- slower incident response
- poor automation maturity

---

## Layering Violation Risk

An alternative considered was moving Prometheus calls into RCA or remediation agents.

This would have caused architectural coupling between:

- infrastructure collection
- observability querying
- AI reasoning

This violates clean system layering.

---

## Platform Evolution Constraint

Future observability integrations will include:

- Prometheus
- Grafana metadata
- Datadog
- Splunk
- OpenTelemetry traces
- anomaly signals
- deployment correlation

If observability remains fragmented, future expansion becomes chaotic.

---

# Decision

Prometheus observability enrichment was moved into the unified incident context collection layer.

Implementation:

```text
app/tools/kubernetes/incident_context.py
```

Prometheus metrics are now automatically collected for problematic Kubernetes pods.

Metrics currently collected:

- `memory_usage_bytes`
- `cpu_usage`
- `restart_metric`

Execution model:

```text
Kubernetes Incident Detection
        ↓
Problematic Pod Identification
        ↓
Pod Metadata Collection
        ↓
Container State Collection
        ↓
Log Collection
        ↓
Event Collection
        ↓
Prometheus Metrics Enrichment
        ↓
Unified Incident Context
        ↓
AI Classification / RCA / Remediation
```

---

# Architecture Contract

Prometheus metrics are now embedded directly into the incident context payload.

Example structure:

```json
{
  "pod_name": "memory-stress",
  "namespace": "ai-lab",
  "phase": "Running",
  "container_states": [...],
  "events": [...],
  "metrics": {
    "memory_usage_bytes": 253952.0,
    "cpu_usage": 0.00018,
    "restart_metric": 744.0
  }
}
```

This becomes the normalized signal contract consumed by downstream AI workflows.

---

# Alternatives Considered

# Option 1 — Standalone Prometheus Utility

Implementation model:

```bash
python -m app.tools.prometheus.metrics_tools
```

## Advantages

- fast initial prototype validation
- isolated debugging
- simple implementation

## Disadvantages

- fragmented workflow
- manual operator dependency
- inconsistent observability enrichment
- weak AI context quality
- poor automation maturity

## Decision

Rejected.

Prototype-friendly, architecture-unfriendly.

---

# Option 2 — Query Prometheus Inside AI Agents

Examples:

- RCA agent fetches metrics
- remediation agent fetches metrics

## Advantages

- agents receive telemetry

## Disadvantages

- infrastructure coupling inside AI layers
- duplicated observability logic
- harder testing
- architecture layering violation
- agent complexity explosion

## Decision

Rejected.

AI agents should consume context, not gather infrastructure signals.

---

# Option 3 — Unified Context Enrichment Layer

Observability integrated during signal collection.

## Advantages

- clean architecture
- reusable normalized context
- better AI reasoning quality
- zero operator dependency
- simpler agent implementation
- scalable observability architecture

## Disadvantages

- slightly more context collection complexity

## Decision

Accepted.

---

# Decision Rationale

Signal collection belongs in the infrastructure context engineering layer.

AI reasoning should operate on normalized operational intelligence, not fragmented raw infrastructure access.

Clean architecture model:

```text
Signal Collection
        ↓
Context Engineering
        ↓
Incident Intelligence
        ↓
AI Reasoning
        ↓
Remediation Intelligence
        ↓
Workflow Orchestration
```

Prometheus clearly belongs in:

```text
Signal Collection / Context Engineering
```

not inside:

```text
AI Agent Reasoning Layer
```

---

# Operational Impact

Platform behavior changed significantly.

Before:

```text
Kubernetes signals only
+
manual Prometheus execution
+
human interpretation
```

After:

```text
fully unified operational context
```

Benefits:

- automated observability enrichment
- better RCA quality
- better remediation quality
- reduced operator dependency
- cleaner workflow orchestration
- faster incident analysis

---

# Implementation Impact

Modules affected:

```text
app/tools/prometheus/metrics_tools.py
app/tools/kubernetes/incident_context.py
app/agents/sre/rca_agent.py
app/agents/sre/remediation_agent.py
app/orchestration/incident_workflow.py
```

Changes included:

- metrics_tools converted into reusable library
- manual CLI dependency removed from architecture path
- automatic metrics enrichment introduced
- AI workflows now consume enriched incident payloads

---

# Risks Accepted

Current observability enrichment remains synchronous.

Potential risks:

- slower context collection under heavy load
- Prometheus latency impact
- future scale limitations

These are acceptable at current platform maturity.

---

# Future Evolution

Planned observability maturity:

---

## Expanded Metrics Coverage

Future metrics:

- network saturation
- filesystem pressure
- node pressure
- pod latency
- deployment error rates
- resource throttling

---

## Multi-Observability Integration

Planned integrations:

- Grafana metadata
- Datadog
- Splunk
- OpenTelemetry traces
- log aggregation platforms

---

## Async Observability Enrichment

Future model:

```text
Signal Collection
    ↓
Async Enrichment Workers
    ↓
Unified Context
```

Improves scale.

---

## Observability Intelligence Layer

Long-term architecture:

```text
Metrics + Logs + Events + Traces
        ↓
Correlation Engine
        ↓
Incident Intelligence
```

---

# Final Outcome

This decision transformed observability integration from a manual utility into a first-class architectural capability.

It materially improved:

- platform automation maturity
- AI reasoning quality
- workflow cohesion
- observability architecture
- future platform scalability

This was a major architectural milestone in Autonomous Ops Platform evolution.