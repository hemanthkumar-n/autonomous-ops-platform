# ADR-005: Unified Incident Workflow Orchestration Architecture

**Date:** 2026-05-15  
**Status:** Accepted  
**Decision Type:** Architecture / Workflow Engineering / Platform Orchestration  
**Owners:** Autonomous Ops Platform Engineering  

---

# Context

Autonomous Ops Platform is being built as an enterprise-grade AI-powered operational intelligence platform for:

- Site Reliability Engineering (SRE)
- Kubernetes operations
- platform engineering
- DevOps automation
- observability-driven incident response
- future autonomous remediation workflows

The long-term platform objective is not isolated AI tooling.

The target architecture is:

**coordinated autonomous operational intelligence workflows.**

During early platform development, core capabilities were implemented as separate functional modules.

Implemented components included:

```text
incident_context.py
incident_classifier.py
rca_agent.py
remediation_agent.py
store_incident.py
```

Each module validated an important platform capability independently.

Examples:

- Kubernetes incident context collection
- observability enrichment
- incident classification
- AI root cause analysis
- AI remediation guidance
- persistence of incident outputs

This validated capability development successfully.

However, execution remained fragmented.

---

# Problem Statement

Independent functional modules created architectural limitations.

---

## Fragmented Operational Execution

Prototype execution required manually running separate modules.

Example execution model:

```text
Collect incident context manually
        ↓
Run classifier manually
        ↓
Run RCA manually
        ↓
Run remediation manually
        ↓
Persist outputs manually
```

This is not platform orchestration.

It is a disconnected engineering prototype.

---

## No Unified Workflow Contract

Each module operated independently without a coordinated workflow lifecycle.

Missing workflow concepts:

- execution stages
- orchestration boundaries
- stage ownership
- workflow lifecycle state
- workflow context continuity

This created weak architectural cohesion.

---

## Human Dependency Risk

The prototype required manual sequencing by the operator.

Risks:

- missed workflow stages
- inconsistent execution
- duplicated effort
- human sequencing errors
- incomplete incident analysis

Operational intelligence should not depend on manual assembly.

---

## Poor Automation Maturity

The long-term platform objective includes:

- autonomous incident analysis
- multi-agent coordination
- approval-gated remediation
- automated decision support

Fragmented scripts do not provide a foundation for autonomous workflows.

---

## Weak Failure Isolation

Independent execution makes coordinated resilience difficult.

Example:

```text
RCA failure
    ↓
manual workflow interruption
```

A platform workflow requires controlled stage isolation.

---

## No Persistence Cohesion

Incident memory existed, but workflow persistence lacked orchestration context.

Missing:

- workflow-level output aggregation
- execution context preservation
- end-to-end workflow artifacts

---

# Decision

A unified incident workflow orchestration layer was introduced.

Implementation:

```text
app/orchestration/incident_workflow.py
```

This becomes the central operational workflow coordinator.

The orchestrator manages end-to-end incident intelligence execution.

---

# Workflow Architecture Introduced

Execution flow:

```text
Incident Detection
        ↓
Unified Incident Context Collection
        ↓
Incident Classification
        ↓
Per-Incident AI RCA Generation
        ↓
Per-Incident Remediation Generation
        ↓
Workflow Output Aggregation
        ↓
Incident Persistence
```

This establishes a coordinated operational workflow model.

---

# Core Workflow Stages

## Stage 1 — Incident Context Collection

Source:

```text
collect_incident_context()
```

Responsibilities:

- detect problematic pods
- collect Kubernetes metadata
- collect container state intelligence
- collect logs
- collect events
- collect Prometheus observability metrics

Output:

normalized incident context payload.

---

## Stage 2 — Incident Classification

Source:

```text
classify_incident()
```

Responsibilities:

- convert raw infrastructure signals
- normalize incident intelligence
- assign severity
- assign ownership
- identify incident types

Output:

classified operational incidents.

---

## Stage 3 — AI RCA Generation

Source:

```text
generate_rca()
```

Responsibilities:

- root cause reasoning
- observability correlation
- incident interpretation
- ownership recommendation
- preventive guidance

Execution model:

per incident.

---

## Stage 4 — AI Remediation Generation

Source:

```text
generate_all_remediations()
```

Responsibilities:

- safe remediation recommendations
- Kubernetes validation guidance
- escalation recommendations
- preventive actions

Execution model:

per incident.

---

## Stage 5 — Workflow Persistence

Source:

```text
store_incident()
```

Responsibilities:

- workflow artifact persistence
- operational memory creation
- future historical retrieval foundation

---

# Workflow Output Contract

Unified workflow output:

```json
{
  "incident_context": [...],
  "classified_incidents": [...],
  "rca_results": [...],
  "remediation_results": [...]
}
```

This creates a reusable orchestration contract.

---

# Alternatives Considered

# Option 1 — Independent Module Execution

Execution:

```text
run each capability manually
```

## Advantages

- rapid prototype iteration
- isolated testing
- simple development

## Disadvantages

- fragmented architecture
- no workflow cohesion
- operator dependency
- poor automation maturity
- no orchestration foundation

## Decision

Rejected.

Prototype-only execution model.

---

# Option 2 — AI Agents Trigger Everything Internally

Example:

```text
RCA agent calls classifier
RCA agent fetches metrics
RCA agent persists outputs
```

## Advantages

- fewer modules visible

## Disadvantages

- severe coupling
- architectural layering violations
- AI agent complexity explosion
- poor maintainability

## Decision

Rejected.

AI agents should not become orchestration engines.

---

# Option 3 — Dedicated Workflow Orchestration Layer

Execution coordinated centrally.

## Advantages

- clean architecture
- workflow cohesion
- clear stage ownership
- future autonomous readiness
- easier resilience design
- future DAG evolution support

## Disadvantages

- additional orchestration layer complexity

## Decision

Accepted.

---

# Decision Rationale

Operational intelligence platforms require coordinated execution.

Architecture principle:

```text
Capabilities ≠ Platform Workflow
```

Independent capabilities prove functionality.

Orchestrated workflows create platform behavior.

A dedicated orchestration layer enables:

- workflow lifecycle control
- stage isolation
- future automation maturity
- multi-agent evolution
- policy enforcement

This aligns with enterprise workflow architecture.

---

# Operational Impact

Before:

```text
Human-driven manual workflow
```

After:

```text
Single orchestrated autonomous workflow
```

Benefits:

- reduced operator dependency
- consistent execution order
- reusable workflow contracts
- better platform cohesion
- improved operational maturity

---

# Architecture Impact

Before:

```text
Independent Capability Modules
    ├── incident collection
    ├── classifier
    ├── RCA
    ├── remediation
    └── persistence
```

After:

```text
Workflow Orchestrator
        ↓
Capability Modules
    ├── context engine
    ├── classifier
    ├── RCA agent
    ├── remediation agent
    └── persistence layer
```

This formalizes orchestration as architecture.

---

# Risks Accepted

Current workflow orchestration remains intentionally simple.

Known limitations:

- synchronous execution
- no async workers
- no queues
- no retries
- no stage retry policies
- no circuit breakers
- no approval gates
- no workflow IDs
- no distributed execution

These are acceptable for current maturity.

---

# Future Evolution

Planned workflow maturity:

---

## Async Execution

Future:

```text
event-driven workflow execution
```

Examples:

- Celery
- Redis queues
- Kafka workflows

---

## Workflow DAGs

Future orchestration:

```text
LangGraph
Temporal
custom execution engine
```

For:

- branching workflows
- retries
- approvals
- rollback paths

---

## Multi-Agent Coordination

Future agents:

- SRE incident agent
- Kubernetes agent
- observability agent
- Linux diagnostics agent
- cloud operations agent
- remediation execution agent

---

## Approval-Gated Remediation

Future workflow:

```text
AI recommendation
    ↓
human approval
    ↓
controlled execution
```

---

## Workflow Identity

Future:

- workflow IDs
- incident IDs
- execution correlation IDs

---

## Policy Governance

Future controls:

- execution boundaries
- remediation policy enforcement
- autonomous safety constraints

---

# Final Outcome

Unified workflow orchestration transformed Autonomous Ops Platform from disconnected engineering modules into coordinated platform workflow architecture.

This materially improved:

- workflow cohesion
- automation maturity
- platform architecture clarity
- future autonomous readiness
- operational intelligence structure

This was a foundational architectural milestone in platform evolution.