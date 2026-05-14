# ADR-001: Centralized Runtime Configuration Management

**Date:** 2026-05-15  
**Status:** Accepted  
**Decision Type:** Architecture / Platform Engineering  
**Owners:** Autonomous Ops Platform Engineering  

---

# Context

Autonomous Ops Platform began as an engineering prototype focused on rapid capability development for Kubernetes incident intelligence, AI-assisted root cause analysis, remediation intelligence, and autonomous operations experimentation.

During early implementation, runtime configuration values were embedded directly inside implementation modules.

Examples included:

- hardcoded AI model endpoints
- hardcoded Prometheus URLs
- hardcoded timeout values
- hardcoded persistence paths
- implicit environment assumptions
- duplicated runtime constants across modules

Representative examples:

```python
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:latest"
PROMETHEUS_URL = "http://localhost:9090"
timeout = 120
INCIDENT_HISTORY_DIR = "app/memory/incident_history/incidents"
```

This approach was acceptable during rapid prototyping but introduced significant architectural and operational risks.

---

# Problem Statement

Distributed runtime configuration created multiple engineering issues:

## Deployment Portability Risk

The platform assumed a fixed local runtime environment.

This prevented clean deployment across:

- local development
- Docker containers
- Kubernetes environments
- CI/CD pipelines
- cloud-hosted infrastructure

---

## Operational Governance Risk

Configuration values were not centrally governed.

This introduced:

- inconsistent timeout behavior
- duplicated environment assumptions
- divergent module behavior
- harder runtime debugging

---

## Security Risk

Hardcoded infrastructure endpoints create poor configuration hygiene and increase future secret management risk.

As the platform evolves toward enterprise deployment, credentials, API endpoints, and sensitive runtime values must be externalized.

---

## Maintainability Risk

Runtime behavior was distributed across implementation modules.

This made:

- debugging slower
- environment changes error-prone
- platform evolution harder
- operational governance inconsistent

---

## AI Platform Evolution Risk

Future platform capabilities require environment-aware runtime management.

Examples:

- LLM provider switching
- model routing
- cloud deployment
- secrets management
- runtime safety controls
- multi-environment promotion pipelines

Hardcoded runtime assumptions would block this evolution.

---

# Decision

A centralized runtime configuration architecture was introduced.

Implementation location:

```text
app/config/settings.py
```

This module becomes the single runtime configuration authority for the platform.

All operational modules consume configuration from a shared settings object.

Pattern:

```python
from app.config.settings import settings
```

---

# Configuration Domains Introduced

## Platform Identity

Platform metadata:

- `PLATFORM_NAME`
- `ENVIRONMENT`
- `WORKFLOW_VERSION`

Purpose:

- environment awareness
- workflow version traceability
- deployment context awareness

---

## Prometheus Runtime Configuration

Observability runtime controls:

- `PROMETHEUS_URL`
- `PROMETHEUS_TIMEOUT`
- `PROMETHEUS_RETRIES`
- `ENABLE_METRICS_ENRICHMENT`

Purpose:

- observability portability
- timeout governance
- retry governance
- optional metrics feature controls

---

## Kubernetes Collection Controls

Signal collection governance:

- `MAX_LOG_LINES`
- `ENABLE_POD_LOG_COLLECTION`
- `ENABLE_EVENT_COLLECTION`

Purpose:

- operational signal control
- collection safety
- future performance governance

---

## Incident Persistence Controls

Operational memory governance:

- `INCIDENT_HISTORY_DIR`
- `PERSIST_INCIDENTS`

Purpose:

- configurable persistence location
- environment portability
- feature toggle support

---

## AI Runtime Configuration

AI execution controls:

- `OLLAMA_BASE_URL`
- `MODEL_NAME`
- `AI_REQUEST_TIMEOUT`

Purpose:

- provider abstraction preparation
- model portability
- timeout governance
- future LLM routing flexibility

---

## Safety Controls

Operational guardrails:

- `ENABLE_DESTRUCTIVE_REMEDIATION`
- `SAFE_MODE`

Purpose:

- execution safety boundaries
- future autonomous remediation governance
- production risk control

---

# Implementation Details

Environment loading:

```python
load_dotenv()
```

Safe boolean parsing:

```python
_get_bool()
```

Singleton runtime configuration object:

```python
settings = Settings()
```

This enables consistent configuration access across the platform.

---

# Alternatives Considered

# Option 1 — Continue Hardcoded Runtime Configuration

## Advantages

- fastest prototype development
- minimal engineering overhead
- rapid experimentation

## Disadvantages

- zero portability
- operational fragility
- inconsistent runtime behavior
- poor governance
- security risk
- future migration difficulty

## Decision

Rejected.

Prototype-only approach unsuitable for platform evolution.

---

# Option 2 — Module-Level Configuration Constants

Example:

```python
prometheus_config.py
llm_config.py
workflow_config.py
```

## Advantages

- partial separation
- cleaner than hardcoding

## Disadvantages

- fragmented governance
- duplicated configuration logic
- inconsistent runtime patterns
- poor discoverability

## Decision

Rejected.

Still creates operational fragmentation.

---

# Option 3 — Centralized Runtime Configuration Model

## Advantages

- single source of truth
- clean governance
- environment portability
- simpler debugging
- easier production deployment
- future secret integration readiness
- scalable architecture

## Disadvantages

- slightly more upfront engineering structure

## Decision

Accepted.

---

# Decision Rationale

Autonomous Ops Platform is evolving from engineering prototype toward enterprise operational intelligence platform.

Enterprise platforms require:

- predictable runtime behavior
- environment portability
- centralized governance
- operational safety
- future secret management readiness
- deployment consistency

Centralized runtime configuration establishes this foundation.

This also aligns with future platform evolution:

- containerization
- Kubernetes deployment
- CI/CD promotion
- secrets management
- provider abstraction
- multi-environment support

---

# Operational Impact

Platform modules no longer rely on embedded runtime assumptions.

Examples updated:

- Prometheus client
- RCA agent
- remediation agent
- persistence layer
- workflow orchestration

Operational benefits:

- consistent timeout handling
- cleaner deployment portability
- easier troubleshooting
- safer runtime governance
- clearer configuration ownership

---

# Architecture Impact

Before:

```text
Implementation Modules
    ├── hardcoded runtime values
    ├── duplicated config
    ├── local assumptions
    └── inconsistent behavior
```

After:

```text
Central Settings Runtime
        ↓
Operational Modules
    ├── Prometheus
    ├── Kubernetes Collection
    ├── AI Agents
    ├── Workflow Engine
    └── Persistence Layer
```

This shifts runtime governance from implementation code to platform architecture.

---

# Risks Accepted

Current implementation still uses dotenv-based environment loading.

This is acceptable for current maturity stage.

Limitations:

- local environment dependency
- no schema enforcement
- no secret provider integration
- limited validation maturity

These are intentional temporary tradeoffs.

---

# Future Evolution

Planned future improvements:

## Configuration Schema Validation

Migration to:

- Pydantic Settings
- typed validation
- stricter runtime contracts

---

## Secret Management Integration

Future providers:

- Kubernetes Secrets
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

---

## Multi-Environment Profiles

Environment-aware deployment profiles:

- development
- test
- staging
- production

---

## Provider Abstraction

Future AI provider flexibility:

- Ollama
- OpenAI
- Claude
- Gemini
- local enterprise models

---

## Runtime Safety Expansion

Future operational controls:

- remediation approvals
- execution gating
- policy enforcement
- autonomous execution controls

---

# Final Outcome

Centralized runtime configuration established the first major production engineering control layer for Autonomous Ops Platform.

This decision materially improved:

- platform portability
- runtime governance
- maintainability
- safety
- enterprise readiness

This was a foundational architectural milestone in the platform’s evolution.