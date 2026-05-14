# ADR-006: Typed Platform Contracts for Deterministic Module Architecture

**Date:** 2026-05-15  
**Status:** Implemented  
**Decision Type:** Architecture / Software Engineering / Platform Contract Design  
**Owners:** Autonomous Ops Platform Engineering  

---

# Context

Autonomous Ops Platform evolved through rapid engineering iterations to validate core operational intelligence capabilities for SRE automation.

Initial implementation focused on proving end-to-end incident intelligence workflows:

```text
incident_context.py
metrics_tools.py
incident_classifier.py
rca_agent.py
remediation_agent.py
incident_workflow.py
store_incident.py
```

During early platform development, module communication relied primarily on loosely structured Python dictionaries and nested lists.

Example incident payload:

```python
incident = {
    "pod_name": "memory-stress",
    "namespace": "ai-lab",
    "metrics": {...}
}
```

Example classification payload:

```python
{
    "incident_type": "MemoryExhaustion",
    "severity": "Critical"
}
```

Example workflow payload:

```python
workflow_output = {
    "incident_context": [...],
    "classified_incidents": [...],
    "rca_results": [...],
    "remediation_results": [...]
}
```

This accelerated prototyping and validation.

However, as the platform matured, this architecture introduced structural engineering risks.

---

# Problem Statement

Dictionary-driven module communication created architectural instability.

---

## No Formal Module Contracts

Modules exchanged implicit payload assumptions.

Examples:

```text
incident_context.py → incident_classifier.py
incident_classifier.py → rca_agent.py
rca_agent.py → remediation_agent.py
remediation_agent.py → incident_workflow.py
incident_workflow.py → store_incident.py
```

No formal schema guaranteed payload structure.

This created hidden coupling between modules.

A change in one producer could silently break multiple downstream consumers.

---

## Runtime Fragility

Dictionary access depends on exact key correctness.

Examples:

```python
incident["pod_name"]
incident["container_states"]
incident["metrics"]
```

Failure scenarios:

- missing keys
- spelling mismatches
- null assumptions
- inconsistent nested structures
- malformed payloads

These failures surface only during runtime execution.

This reduces reliability and increases debugging complexity.

---

## Weak Refactor Safety

As platform modules evolve, dictionary contracts become unsafe.

Example:

Changing:

```python
"restart_metric"
```

to:

```python
"restart_count_metric"
```

could silently break:

- incident enrichment
- classification
- RCA reasoning
- remediation workflows
- persistence serialization

Without contract enforcement, refactoring becomes high-risk.

---

## Poor API Readiness

Planned platform evolution includes:

- FastAPI service interfaces
- workflow APIs
- operational control APIs
- external consumers
- agent communication endpoints

Dictionary payloads are poor API contracts.

Production APIs require deterministic schemas.

---

## Weak Testability

Dynamic payload systems are harder to validate.

Common issues:

- malformed nested payloads
- missing observability data
- inconsistent AI outputs
- incomplete workflow serialization

Typed contracts improve deterministic testing.

---

## Multi-Agent Scalability Risk

Planned architecture includes specialized agents:

- SRE incident agent
- Kubernetes diagnostics agent
- observability agent
- RCA reasoning agent
- remediation planning agent
- operational memory agent
- future autonomous execution agent

Inter-agent communication requires explicit message contracts.

Implicit dictionaries do not scale safely.

---

## Governance and Maintainability Risk

Enterprise platforms require predictable internal interfaces.

Missing capabilities:

- schema ownership
- validation boundaries
- contract governance
- deterministic serialization
- compatibility discipline

Without contracts, maintainability degrades over time.

---

# Decision

Autonomous Ops Platform adopts typed schema-based internal platform contracts using Pydantic.

Implementation location:

```text
app/schemas/
```

Schema modules introduced:

```text
app/schemas/metrics.py
app/schemas/incident.py
app/schemas/classification.py
app/schemas/ai.py
app/schemas/workflow.py
```

Technology selected:

```text
Pydantic
```

These schemas become the authoritative internal contracts for platform module communication.

---

# Contract Architecture Introduced

## Metrics Contract

Module:

```text
app/schemas/metrics.py
```

Primary schema:

```python
PodMetrics
```

Purpose:

Formal observability metrics contract.

Fields:

- memory_usage_bytes
- cpu_usage
- restart_metric

Used by:

```text
metrics_tools.py
incident_context.py
```

---

## Incident Context Contracts

Module:

```text
app/schemas/incident.py
```

Schemas:

```python
PodCondition
ContainerState
PodEvent
IncidentContext
```

Purpose:

Canonical operational incident representation.

Captures:

- pod identity
- namespace
- lifecycle phase
- node placement
- pod readiness conditions
- container operational state
- restart history
- termination metadata
- Kubernetes events
- container logs
- observability metrics

Used by:

```text
incident_context.py
incident_classifier.py
rca_agent.py
remediation_agent.py
incident_workflow.py
```

---

## Classification Contract

Module:

```text
app/schemas/classification.py
```

Primary schema:

```python
IncidentClassification
```

Purpose:

Canonical incident intelligence representation.

Captures:

- incident type
- severity
- confidence
- recommended ownership
- workload context
- restart metadata
- container state

Used by:

```text
incident_classifier.py
rca_agent.py
remediation_agent.py
incident_workflow.py
```

---

## AI Output Contracts

Module:

```text
app/schemas/ai.py
```

Schemas:

```python
RCAResponse
RemediationResponse
```

Purpose:

Canonical AI output contracts.

These formalize:

- RCA generation output
- remediation planning output

Used by:

```text
rca_agent.py
remediation_agent.py
incident_workflow.py
```

---

## Workflow Contract

Module:

```text
app/schemas/workflow.py
```

Primary schema:

```python
WorkflowExecutionResponse
```

Purpose:

Canonical workflow orchestration contract.

Captures:

- incident context
- classifications
- RCA outputs
- remediation outputs

Used by:

```text
incident_workflow.py
store_incident.py
```

---

# Architectural Migration

Modules migrated:

```text
incident_context.py
metrics_tools.py
incident_classifier.py
rca_agent.py
remediation_agent.py
incident_workflow.py
store_incident.py
```

Migration objective:

Replace implicit dictionary glue with deterministic typed contracts.

---

# Architecture Before

```text
Kubernetes signals
      ↓
dictionary blobs
      ↓
classification dictionaries
      ↓
free-form AI payloads
      ↓
workflow dictionaries
      ↓
raw JSON persistence
```

Characteristics:

- implicit coupling
- weak validation
- runtime fragility
- unsafe refactoring
- poor scalability

---

# Architecture After

```text
IncidentContext
        ↓
IncidentClassification
        ↓
RCAResponse
        ↓
RemediationResponse
        ↓
WorkflowExecutionResponse
        ↓
typed persistence
```

Characteristics:

- explicit contracts
- deterministic interfaces
- validation boundaries
- safe refactoring
- enterprise scalability

---

# Alternatives Considered

# Option 1 — Continue Dictionary-Based Architecture

Advantages:

- fastest implementation
- lowest initial engineering effort
- flexible prototyping

Disadvantages:

- runtime fragility
- hidden coupling
- poor testability
- weak API readiness
- unsafe refactoring
- poor agent interoperability

Decision:

Rejected.

Appropriate only for prototypes.

---

# Option 2 — Python Dataclasses

Example:

```python
@dataclass
class PodMetrics:
```

Advantages:

- stronger typing
- lightweight
- simpler than raw dictionaries

Disadvantages:

- weaker validation
- limited schema tooling
- weaker serialization guarantees
- less API-native integration

Decision:

Rejected.

Improvement over dicts, but insufficient for long-term platform evolution.

---

# Option 3 — Pydantic Typed Contracts

Advantages:

- runtime validation
- deterministic typing
- schema serialization
- API compatibility
- refactor safety
- governance readiness
- future versioning support

Disadvantages:

- schema maintenance overhead
- stricter engineering discipline required

Decision:

Accepted.

---

# Decision Rationale

Autonomous Ops Platform roadmap includes:

- enterprise API exposure
- operational memory systems
- vector indexing
- incident retrieval
- multi-agent orchestration
- autonomous remediation workflows
- approval-gated execution safety

These architectures require deterministic interfaces.

Engineering principle:

```text
Loose internal interfaces do not scale.
```

Typed contracts provide:

- reliability
- maintainability
- safety
- auditability
- API readiness
- AI interoperability

This is foundational architecture.

---

# Operational Impact

## Early Validation

Invalid payloads fail immediately.

Benefits:

- faster debugging
- earlier fault isolation
- safer deployments

---

## Safer Refactoring

Contract-aware changes reduce regression risk.

Refactors become controlled engineering operations instead of runtime experiments.

---

## Better Developer Experience

Before:

```python
incident["pod_name"]
```

After:

```python
incident.pod_name
```

Cleaner interfaces.

Better IDE support.

Safer navigation.

---

## AI Contract Governance

LLM interactions now produce explicit platform objects.

Improves:

- reasoning pipeline stability
- workflow predictability
- downstream compatibility

---

## Persistence Stability

Workflow outputs are serialized using canonical typed models.

Improves:

- audit consistency
- operational traceability
- schema stability

---

## API Readiness

Typed contracts align directly with:

```text
FastAPI request models
FastAPI response models
OpenAPI generation
```

---

# Risks Accepted

Current maturity limitations:

- internal-only contracts
- no public API versioning
- limited compatibility governance
- no schema migration policy
- no backward compatibility enforcement

Acceptable for current platform maturity.

---

# Future Evolution

Planned maturity expansions:

---

## API Contract Reuse

Schemas reused directly for service interfaces.

---

## Versioned Contracts

Future:

```text
v1
v2
v3
```

schema compatibility governance.

---

## Agent Communication Contracts

Explicit message schemas between agents.

---

## Workflow Validation Gates

Policy enforcement using typed workflow validation.

---

## Memory Layer Contracts

Future schema contracts for:

- incident memory
- RCA knowledge memory
- remediation memory
- architecture memory
- vector retrieval interfaces

---

## Autonomous Execution Safety

Future execution workflows require typed action contracts.

Examples:

- approval payloads
- remediation execution requests
- rollback requests
- execution audit artifacts

---

# Final Outcome

Typed platform contracts transformed Autonomous Ops Platform from loosely coupled prototype implementation into deterministic schema-governed platform architecture.

This materially improved:

- reliability
- maintainability
- refactor safety
- API readiness
- operational auditability
- multi-agent scalability
- future autonomous execution readiness

This was a foundational architecture milestone in platform evolution.
