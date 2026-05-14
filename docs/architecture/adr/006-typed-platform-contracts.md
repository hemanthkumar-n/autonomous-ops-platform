# ADR-006: Typed Platform Contracts for Deterministic Module Architecture

**Date:** 2026-05-15  
**Status:** Accepted  
**Decision Type:** Architecture / Software Engineering / Platform Contract Design  
**Owners:** Autonomous Ops Platform Engineering  

---

# Context

Autonomous Ops Platform evolved through rapid engineering iterations focused on validating core operational intelligence capabilities.

Implemented platform modules included:

```text
incident_context.py
metrics_tools.py
incident_classifier.py
rca_agent.py
remediation_agent.py
incident_workflow.py
store_incident.py
```

During early platform development, data exchange between modules relied entirely on loosely structured Python dictionaries and lists.

Examples:

```python
incident = {
    "pod_name": "memory-stress",
    "namespace": "ai-lab",
    "metrics": {...}
}
```

Classification output:

```python
{
    "incident_type": "MemoryExhaustion",
    "severity": "Critical"
}
```

Workflow payload:

```python
workflow_output = {
    "incident_context": [...],
    "classified_incidents": [...],
    "rca_results": [...],
    "remediation_results": [...]
}
```

This approach accelerated functional prototyping.

However, it introduced significant architectural risk as platform complexity increased.

---

# Problem Statement

Loose dictionary-based module communication created multiple engineering risks.

---

## No Formal Module Contracts

Modules exchanged implicit payload structures.

Examples:

```text
incident_context.py → incident_classifier.py
incident_classifier.py → rca_agent.py
rca_agent.py → incident_workflow.py
```

But no formal contract guaranteed structure.

This created hidden coupling.

If one module changed payload shape, downstream consumers could fail unexpectedly.

---

## Runtime Fragility

Dictionary access depends on exact key correctness.

Examples:

```python
incident["pod_name"]
incident["container_states"]
incident["metrics"]
```

Risks:

- missing keys
- spelling mistakes
- null structure assumptions
- inconsistent payloads

Failures occur only at runtime.

This reduces reliability.

---

## Weak Refactor Safety

As platform modules evolve, dictionary-based payloads become difficult to refactor safely.

Example:

Renaming:

```python
"restart_metric"
```

to:

```python
"restart_count_metric"
```

could silently break downstream consumers.

Without contracts, refactors become risky.

---

## Poor API Readiness

Future platform evolution includes:

- FastAPI service interfaces
- external API consumers
- workflow APIs
- agent-to-agent communication
- memory retrieval APIs

Loose dictionaries are poor API contracts.

Production APIs require deterministic schemas.

---

## Weak Testability

Dictionary-heavy systems are harder to validate.

Examples:

- incomplete payload generation
- malformed AI outputs
- unexpected nested structures

Typed contracts improve test precision.

---

## Multi-Agent Evolution Risk

Future platform architecture includes specialized agents:

- SRE incident agent
- Kubernetes diagnostics agent
- observability agent
- remediation agent
- memory agent

Inter-agent communication requires strict contracts.

Implicit dictionaries do not scale well.

---

## Platform Governance Risk

Enterprise systems require predictable internal interfaces.

Loose structures make governance difficult.

Missing:

- field ownership
- explicit contracts
- schema validation
- deterministic interfaces

---

# Decision

A typed schema contract architecture was introduced.

Implementation:

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

These schemas become the formal internal data contracts for platform modules.

---

# Contract Architecture Introduced

## Metrics Contract

Module:

```text
app/schemas/metrics.py
```

Schema:

```python
PodMetrics
```

Purpose:

Formal observability metrics contract.

Fields:

- memory_usage_bytes
- cpu_usage
- restart_metric

---

## Incident Context Contract

Module:

```text
app/schemas/incident.py
```

Schemas:

```python
PodCondition
ContainerState
IncidentContext
```

Purpose:

Formal operational incident context contract.

Captures:

- pod identity
- namespace
- lifecycle phase
- node placement
- conditions
- container states
- logs
- events
- observability metrics

---

## Classification Contract

Module:

```text
app/schemas/classification.py
```

Schema:

```python
IncidentClassification
```

Purpose:

Formal incident intelligence contract.

Captures:

- incident type
- severity
- confidence
- recommended ownership
- workload context

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

Formal AI output contracts.

---

## Workflow Contract

Module:

```text
app/schemas/workflow.py
```

Schema:

```python
WorkflowExecutionResponse
```

Purpose:

Formal orchestration payload contract.

---

# Architectural Change

Before:

```text
dict
 ↓
dict
 ↓
dict
 ↓
dict
```

Implicit contracts.

Hidden coupling.

Runtime fragility.

---

After:

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
```

Explicit deterministic contracts.

---

# Alternatives Considered

# Option 1 — Continue Dictionary-Based Contracts

## Advantages

- fastest implementation
- minimal development overhead
- simple prototype experimentation

## Disadvantages

- runtime fragility
- weak refactor safety
- hidden coupling
- poor testability
- poor API readiness
- unsafe multi-agent scaling

## Decision

Rejected.

Suitable for prototypes only.

---

# Option 2 — Dataclasses

Example:

```python
@dataclass
class PodMetrics:
```

## Advantages

- stronger typing
- lightweight
- better than raw dictionaries

## Disadvantages

- weaker validation
- limited schema tooling
- less API-native
- weaker serialization capabilities

## Decision

Rejected.

Improvement over dicts, but insufficient for long-term platform evolution.

---

# Option 3 — Pydantic Schema Contracts

## Advantages

- validation
- typing
- serialization
- API readiness
- schema governance
- safer refactoring
- deterministic interfaces

## Disadvantages

- modest learning overhead
- additional schema maintenance

## Decision

Accepted.

---

# Decision Rationale

Autonomous Ops Platform is evolving toward:

- enterprise API services
- multi-agent orchestration
- operational memory systems
- autonomous workflows
- approval-gated remediation

These architectures require deterministic contracts.

Engineering principle:

```text
Loose internal interfaces do not scale.
```

Typed schema contracts provide:

- reliability
- maintainability
- safety
- API readiness
- agent interoperability

This is foundational platform architecture.

---

# Operational Impact

Benefits introduced:

---

## Early Validation

Invalid payloads fail earlier.

Improves debugging speed.

---

## Safer Refactoring

Contract-aware module evolution becomes safer.

---

## Better Developer Experience

Examples:

Before:

```python
incident["pod_name"]
```

After:

```python
incident.pod_name
```

Cleaner interfaces.

---

## API Readiness

Schemas directly support:

- FastAPI request models
- FastAPI response models
- API validation

---

## AI Contract Governance

AI outputs become deterministic platform objects.

---

# Architecture Impact

Before:

```text
Implementation modules with implicit contracts
```

After:

```text
Schema-governed platform architecture
```

This formalizes platform internal APIs.

---

# Risks Accepted

Current schema implementation is intentionally initial maturity.

Known limitations:

- internal-only schemas
- no versioned API contracts
- no strict validation policies
- no compatibility governance
- no schema evolution policies

Acceptable for current platform maturity.

---

# Future Evolution

Planned maturity:

---

## API Contract Reuse

Schemas reused directly by:

```text
FastAPI
```

---

## Versioned Contracts

Future:

```text
v1
v2
```

schema compatibility.

---

## Agent Communication Contracts

Future agent-to-agent interfaces.

---

## Workflow Contract Enforcement

Formal workflow validation gates.

---

## Memory Layer Contracts

Schemas for:

- incident memory
- runbook memory
- architecture memory
- vector retrieval contracts

---

## External SDK Contracts

Potential future external integrations.

---

# Final Outcome

Typed platform contracts transformed Autonomous Ops Platform from loosely coupled prototype implementation into deterministic schema-governed platform architecture.

This materially improved:

- reliability
- maintainability
- refactor safety
- API readiness
- multi-agent scalability
- engineering governance

This was a foundational software architecture milestone in platform evolution.
