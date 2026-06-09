
# Autonomous Ops Platform

<p align="center">
  <strong>Enterprise AI-Powered Incident Intelligence & Autonomous Operations Platform</strong>
</p>

<p align="center">
  Built for SRE • Platform Engineering • Kubernetes Operations • DevOps • Cloud Reliability Engineering
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" />
  <img src="https://img.shields.io/badge/Kubernetes-Platform%20Engineering-326CE5" />
  <img src="https://img.shields.io/badge/SRE-Incident%20Automation-orange" />
  <img src="https://img.shields.io/badge/Observability-Prometheus-red" />
  <img src="https://img.shields.io/badge/LLM-Ollama-green" />
  <img src="https://img.shields.io/badge/Status-Day%206%20Completed-success" />
</p>

---

Enterprise Autonomous Operational Intelligence Platform for SRE and Platform Engineering teams.

Autonomous Ops Platform is an AI-native operational intelligence platform designed to evolve from AI-assisted incident analysis into safe autonomous operational reasoning for cloud-native infrastructure.

The platform combines deterministic operational telemetry, Kubernetes diagnostics, historical operational memory, semantic retrieval, and AI reasoning to accelerate incident response and operational decision-making.

---

# Vision

Modern infrastructure operations suffer from fragmented context:

- telemetry exists in monitoring tools
- runtime diagnostics live in Kubernetes
- historical incidents are buried in tickets
- remediation knowledge is tribal
- root cause analysis is repeatedly recreated

Autonomous Ops Platform aims to consolidate this into an operational intelligence layer.

The durable cross-domain product direction, including Linux, Kubernetes, AWS,
Slack/Teams approvals, the operator UI, and company onboarding, is documented
in [`docs/AOP_PRODUCT_VISION.md`](docs/AOP_PRODUCT_VISION.md).

Target evolution:

```text
Reactive Operations
      →
AI-Assisted Incident Response
      →
Operational Learning Platform
      →
Autonomous Operational Intelligence
      →
Safe Self-Healing Platform Engineering
```

---

# Current Platform Capabilities

## Kubernetes Incident Collection

Collects live incident context from Kubernetes workloads.

Signals include:

- pod lifecycle state
- container runtime state
- restart counts
- container termination reasons
- resource requests / limits
- pod events
- container logs
- node metadata

---

## Prometheus Observability Enrichment

Correlates runtime incidents with telemetry:

- memory usage
- CPU usage
- restart metrics

Architecture:

```text
Incident Context
      +
Prometheus Metrics
      =
Enriched Operational Incident
```

---

## AI Incident Classification

AI-assisted incident classification:

Examples:

- ImagePullFailure
- ApplicationCrashLoop
- MemoryExhaustion
- ConfigurationFailure
- ProbeFailure
- ResourcePressure

Outputs:

- incident type
- severity
- confidence
- ownership recommendation

---

## AI Root Cause Analysis

Memory-aware RCA generation using:

- runtime diagnostics
- Kubernetes context
- observability metrics
- hybrid historical operational memory

Outputs:

- incident summary
- historical similarity analysis
- root cause analysis
- signal correlation
- severity assessment
- ownership recommendation
- preventive recommendations

---

## AI Remediation Guidance

Safe AI-assisted remediation recommendations.

Includes:

- immediate low-risk actions
- Kubernetes validation commands
- escalation guidance
- preventive recommendations
- operational risk awareness

Safety principles:

- validation-first remediation
- non-destructive by default
- escalation-aware recommendations
- human-controlled execution

---

## Structured Operational Memory

Incident persistence layer:

```text
app/memory/incident_history/
```

Stores normalized operational incidents for:

- auditability
- deterministic retrieval
- historical learning
- operational context enrichment

---

## Semantic Operational Memory

AI semantic memory for operational similarity search.

Architecture:

```text
Structured Incident Memory
        ↓
Embedding Generation
        ↓
Vector Indexing
        ↓
Semantic Retrieval
```

Supports similarity-based recall for operational reasoning.

---

## Hybrid Retrieval Engine

Combines:

```text
Exact Retrieval
        +
Semantic Retrieval
        =
Hybrid Operational Memory
```

Purpose:

- exact historical incident lookup
- fuzzy semantic similarity detection
- contextual AI operational reasoning

---

## Provider Abstraction Architecture

Platform avoids direct infrastructure coupling.

Implemented abstractions:

### LLM Provider Abstraction

```text
LLMClient
    ↓
LLMProvider
    ↓
OllamaProvider
```

Future:

- OpenAI
- Claude
- Gemini
- enterprise LLMs

---

### Embedding Provider Abstraction

```text
EmbeddingClient
    ↓
EmbeddingProvider
    ↓
OllamaEmbeddingProvider
```

Future:

- OpenAI embeddings
- VoyageAI
- BGE
- enterprise embedding providers

---

### Vector Store Abstraction

```text
SemanticMemoryClient
        ↓
VectorStoreProvider
        ↓
ChromaVectorStoreProvider
```

Future:

- PostgreSQL + pgvector
- Qdrant
- Weaviate
- enterprise vector platforms

---

# High-Level Architecture

```text
                   ┌────────────────────────────┐
                   │ Kubernetes Cluster         │
                   │ Problematic Workloads      │
                   └────────────┬───────────────┘
                                │
                                ▼
                   ┌────────────────────────────┐
                   │ Incident Context Collector │
                   └────────────┬───────────────┘
                                │
               ┌────────────────┴────────────────┐
               │                                 │
               ▼                                 ▼
   ┌──────────────────────┐         ┌────────────────────────┐
   │ Kubernetes Runtime   │         │ Prometheus Metrics     │
   │ Diagnostics          │         │ Observability Signals  │
   └────────────┬─────────┘         └────────────┬───────────┘
                │                                │
                └────────────────┬───────────────┘
                                 ▼
                  ┌─────────────────────────────┐
                  │ Enriched Incident Context   │
                  └────────────┬────────────────┘
                               │
                               ▼
                  ┌─────────────────────────────┐
                  │ AI Incident Classification  │
                  └────────────┬────────────────┘
                               │
                               ▼
                  ┌─────────────────────────────┐
                  │ Hybrid Memory Retrieval     │
                  │ Exact + Semantic            │
                  └────────────┬────────────────┘
                               │
                 ┌─────────────┴──────────────┐
                 │                            │
                 ▼                            ▼
      ┌────────────────────┐      ┌─────────────────────────┐
      │ Structured Memory  │      │ Semantic Vector Memory  │
      └────────────────────┘      └─────────────────────────┘
                 │                            │
                 └─────────────┬──────────────┘
                               ▼
                  ┌─────────────────────────────┐
                  │ Memory-Aware RCA            │
                  └────────────┬────────────────┘
                               │
                               ▼
                  ┌─────────────────────────────┐
                  │ Memory-Aware Remediation    │
                  └────────────┬────────────────┘
                               │
                               ▼
                  ┌─────────────────────────────┐
                  │ Structured Persistence      │
                  │ + Semantic Indexing         │
                  └─────────────────────────────┘
```

---

# Repository Structure

```text
autonomous-ops-platform/
│
├── app/
│   ├── agents/
│   │   └── sre/
│   │       ├── incident_classifier.py
│   │       ├── rca_agent.py
│   │       └── remediation_agent.py
│   │
│   ├── config/
│   │   ├── logging_config.py
│   │   └── settings.py
│   │
│   ├── llm/
│   │   ├── client.py
│   │   ├── response_validator.py
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   └── ollama_provider.py
│   │   │
│   │   └── embeddings/
│   │       ├── client.py
│   │       └── providers/
│   │           ├── base.py
│   │           └── ollama_embedding_provider.py
│   │
│   ├── memory/
│   │   ├── fingerprints/
│   │   ├── incident_history/
│   │   ├── retrieval/
│   │   │   ├── search.py
│   │   │   ├── semantic_search.py
│   │   │   └── hybrid_search.py
│   │   │
│   │   └── vectorstore/
│   │       ├── client.py
│   │       └── providers/
│   │           ├── base.py
│   │           └── chroma_provider.py
│   │
│   ├── orchestration/
│   │   └── incident_workflow.py
│   │
│   ├── schemas/
│   │   ├── ai.py
│   │   ├── classification.py
│   │   ├── incident.py
│   │   ├── memory.py
│   │   └── workflow.py
│   │
│   └── tools/
│       ├── kubernetes/
│       └── prometheus/
│
├── docs/
│   └── architecture/
│       └── adr/
│
├── infra/
├── scripts/
├── tests/
└── README.md
```

---

# Technology Stack

Core Platform:

- Python 3.11+
- Pydantic
- FastAPI (planned service layer)

Cloud Native:

- Kubernetes
- Prometheus

AI Runtime:

- Ollama
- qwen2.5-coder
- local AI inference

Semantic Memory:

- ChromaDB
- nomic-embed-text embeddings

Future Targets:

- PostgreSQL + pgvector
- Qdrant
- enterprise vector stores

DevOps / Platform:

- Docker
- Terraform
- Jenkins
- AWS / Azure

---

# Architecture Principles

## Provider Abstraction

Infrastructure implementations must remain replaceable.

Avoid:

```text
agent → vendor SDK
```

Prefer:

```text
agent → abstraction → provider implementation
```

---

## Typed Contracts

Operational contracts are strongly typed.

Examples:

- IncidentContext
- IncidentClassification
- RCAResponse
- RemediationResponse
- IncidentMemory
- WorkflowExecutionResponse

---

## Memory-First Operational Intelligence

Operational reasoning should use organizational history.

Not:

```text
incident → AI reasoning only
```

But:

```text
incident
  +
historical memory
  +
semantic similarity
  +
AI reasoning
```

---

## Safety by Design

Autonomous remediation must remain controlled.

Principles:

- safe defaults
- validation-first execution
- escalation-aware workflows
- destructive actions gated

---

## Future Infrastructure Portability

Avoid permanent coupling to:

- specific LLM vendors
- vector stores
- embedding providers

---

# ADR Architecture Decisions

Current architectural decisions:

- ADR-006 — Typed Contract Architecture
- ADR-007 — LLM Provider Abstraction Architecture
- ADR-008 — Operational Memory Architecture
- ADR-009 — Semantic Operational Memory Architecture

Path:

```text
docs/architecture/adr/
```

---

# Local Setup

## Prerequisites

Install:

- Python 3.14+
- Kubernetes cluster
- kubectl configured
- Prometheus endpoint
- Ollama
- ChromaDB dependencies

---

## Install Dependencies

```bash
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

---

## Install Ollama Model

Example:

```bash
ollama pull qwen2.5-coder:latest
ollama pull nomic-embed-text
```

---

## Environment Configuration

Example:

```env
ENVIRONMENT=development

WORKFLOW_VERSION=v1

PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_TIMEOUT=10

OLLAMA_BASE_URL=http://localhost:11434

LLM_MODEL_NAME=qwen2.5-coder:latest
EMBEDDING_MODEL_NAME=nomic-embed-text

INCIDENT_HISTORY_DIR=data/incidents

VECTORSTORE_PATH=data/vectorstore/chroma
VECTORSTORE_COLLECTION_NAME=incident_memory

SAFE_MODE=true
ENABLE_DESTRUCTIVE_REMEDIATION=false
```

---

# Run Platform

## Showcase CLI

Validate the local runtime:

```bash
aop health
```

Investigate all unhealthy Kubernetes workloads:

```bash
aop investigate k8s
```

Limit investigation to a namespace:

```bash
aop investigate k8s --namespace ai-lab
```

Generate a Markdown report:

```bash
aop investigate k8s \
  --namespace ai-lab \
  --format markdown \
  --output reports/incident-report.md
```

Search structured operational memory:

```bash
aop memory search --incident-type MemoryExhaustion
```

The CLI is advisory. It collects evidence, classifies incidents, generates
RCA and remediation guidance, and stores operational memory. It does not
execute destructive remediation.

## Module Entrypoints

Full incident workflow:

```bash
python -m app.orchestration.incident_workflow
```

RCA only:

```bash
python -m app.agents.sre.rca_agent
```

Remediation only:

```bash
python -m app.agents.sre.remediation_agent
```

Semantic search test:

```bash
python -m app.memory.retrieval.semantic_search
```

Hybrid search test:

```bash
python -m app.memory.retrieval.hybrid_search
```

---

# Current Maturity

Completed:

```text
Phase 1
✓ Incident collection

Phase 2
✓ AI classification
✓ RCA generation
✓ remediation generation

Phase 3
✓ LLM provider abstraction

Phase 4
✓ operational memory
✓ embeddings abstraction
✓ vector store abstraction
✓ semantic indexing
✓ hybrid retrieval
✓ memory-aware RCA
✓ memory-aware remediation

Phase 5
✓ installable `aop` CLI
✓ runtime health checks
✓ namespace and pod-scoped investigation
✓ JSON and Markdown report export
✓ offline regression tests
```

---

# Roadmap

## Phase 5 — Operational Intelligence Evolution

Planned:

- incident pattern intelligence
- recurrence tracking
- incident fingerprint clustering
- pattern-aware semantic memory
- operational trend awareness

---

## Phase 6 — Agentic Orchestration

Planned:

- planner agents
- execution agents
- approval workflows
- guarded remediation automation

---

## Phase 7 — Shared Organizational Intelligence

Planned:

- shared operational knowledge
- multi-agent memory
- runbook intelligence
- institutional operational learning

---

## Phase 8 — Enterprise Platform Evolution

Planned:

- FastAPI service layer
- authentication
- RBAC
- audit workflows
- approval systems
- multi-tenant architecture

---

# Long-Term Vision

Target capability:

```text
Observe
→ Understand
→ Remember
→ Reason
→ Recommend
→ Validate
→ Act (safely)
→ Learn
```

Autonomous Ops Platform is being engineered as an enterprise-grade foundation for autonomous operational intelligence.

---

# Status

Active engineering architecture evolution.

Current maturity:

```text
Semantic operational intelligence foundation complete.
```

Next milestone:

```text
Incident Pattern Intelligence
```

⸻

Contribution Philosophy
This project is being engineered as a serious platform architecture initiative.
Contributions should align with:
	•	clean architecture
	•	deterministic contracts
	•	observability
	•	modularity
	•	enterprise operational safety

⸻

Disclaimer
Current implementation provides AI-assisted operational intelligence and safe remediation recommendations.
It does not autonomously execute destructive production actions.
Execution automation will be introduced only through explicit governance and approval controls.

⸻

Author
Built by:
Hemanth Kumar

Principal SRE | Platform Engineering | DevOps | Kubernetes | AWS | Azure | Terraform | CI/CD | Observability | Incident Response

14+ years of infrastructure engineering, reliability engineering, DevOps automation, and enterprise operations leadership.
This platform serves as a flagship engineering initiative demonstrating enterprise AI operations architecture and autonomous platform engineering vision.

LinkedIn:
https://www.linkedin.com/in/hemanthkumarn/

GitHub:
https://github.com/hemanthkumar-n

⸻

Strategic Direction
Autonomous Ops Platform is not intended to remain a Kubernetes troubleshooting tool.
It is being architected as a long-term enterprise AI operations platform for autonomous reliability engineering.
