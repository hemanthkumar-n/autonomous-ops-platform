# Autonomous Ops Platform

<p align="center">
  <strong>Enterprise AI-Powered Incident Intelligence &amp; Autonomous Operations Platform</strong>
</p>

<p align="center">
  Built for SRE &bull; Platform Engineering &bull; Kubernetes Operations &bull; DevOps &bull; Cloud Reliability Engineering
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Kubernetes-Platform%20Engineering-326CE5" alt="Kubernetes Platform Engineering" />
  <img src="https://img.shields.io/badge/SRE-Incident%20Automation-orange" alt="SRE Incident Automation" />
  <img src="https://img.shields.io/badge/Observability-Prometheus-red" alt="Prometheus Observability" />
  <img src="https://img.shields.io/badge/LLM-Ollama-green" alt="Ollama LLM" />
  <img src="https://img.shields.io/badge/Status-Phase%203.2%20Completed-success" alt="Phase 3.2 Completed" />
</p>

---

## Executive Summary

Autonomous Ops Platform is an enterprise-focused AI operations engineering initiative designed to transform fragmented infrastructure signals into structured operational intelligence.

The platform combines Kubernetes diagnostics, observability telemetry, AI-assisted reasoning, incident classification, remediation guidance, workflow orchestration, typed platform contracts, LLM provider abstraction, and operational memory foundations into a modular architecture that evolves toward safe autonomous operations.

This is not a chatbot experiment.

This is a platform engineering project focused on real operational automation.

---

## Vision

Modern operations teams still spend significant engineering effort on:

- manual incident triage
- fragmented observability correlation
- repetitive operational diagnostics
- inconsistent remediation guidance
- knowledge silos
- delayed root cause analysis
- reactive incident management

Autonomous Ops Platform aims to evolve toward:

**AI-native operational intelligence and autonomous reliability engineering.**

Long-term vision:

```text
Detect -> Understand -> Reason -> Recommend -> Approve -> Execute -> Learn
```

Current implementation focuses on building deterministic, enterprise-safe foundations for that evolution.

---

## What Has Been Built

### Incident Context Intelligence

Collects structured Kubernetes operational context:

- Kubernetes pod discovery
- unhealthy workload detection
- container lifecycle inspection
- restart intelligence
- termination reason extraction
- pod condition analysis
- resource requests and limits inspection
- Kubernetes event correlation
- container log collection
- structured incident context normalization
- namespace-aware diagnostics

Supported incident patterns:

- ImagePullBackOff
- ErrImagePull
- CrashLoopBackOff
- OOMKilled
- FailedScheduling
- CreateContainerError
- CreateContainerConfigError
- restart storms
- startup failures

### Observability Intelligence

Prometheus-backed telemetry enrichment:

- pod memory usage
- CPU usage
- restart metrics
- observability enrichment for incidents
- operational signal correlation

Production improvements completed:

- environment-driven Prometheus configuration
- timeout-based query safety
- resilient error handling
- production-safe Prometheus client structure
- parallel telemetry collection with fault tolerance

### Incident Classification Engine

Deterministic incident classification.

Implemented:

- incident pattern classification
- severity assignment
- confidence scoring
- ownership routing

Example outputs:

- incident type
- severity
- confidence
- Platform Engineering ownership
- Application Team ownership

### AI Root Cause Analysis Engine

AI-assisted RCA generation using contextual operational intelligence.

Correlates:

- Kubernetes runtime signals
- observability telemetry
- restart patterns
- workload behavior
- operational failure context
- ownership recommendations
- preventive recommendations

Execution:

```bash
python -m app.agents.sre.rca_agent
```

### Safe AI Remediation Engine

AI-generated remediation guidance focused on operational safety.

Implemented:

- incident-specific remediation generation
- Kubernetes validation commands
- safe operational actions
- escalation recommendations
- preventive guidance

Design principle:

```text
recommend, never destructively execute
```

Execution:

```bash
python -m app.agents.sre.remediation_agent
```

### Workflow Orchestration

End-to-end autonomous incident workflow:

```text
Incident Detection
        |
        v
Context Collection
        |
        v
Observability Correlation
        |
        v
Incident Classification
        |
        v
AI Root Cause Analysis
        |
        v
AI Remediation Generation
        |
        v
Incident Persistence
```

Execution:

```bash
python -m app.orchestration.incident_workflow
```

### Typed Platform Contracts

Schema-driven internal architecture using Pydantic.

Benefits:

- deterministic module contracts
- safer refactoring
- validation boundaries
- API readiness
- workflow consistency
- persistence stability

### AI Provider Abstraction

Centralized LLM architecture:

```text
Agents
  |
  v
LLM Client
  |
  v
Provider Contract
  |
  v
Provider Implementation
```

Current provider:

- Ollama

Architecture ready for:

- OpenAI
- Claude
- Gemini
- vLLM
- enterprise AI gateways

### Operational Memory Foundation

Incident workflow persistence foundation:

- workflow result persistence
- incident JSON storage
- historical workflow archiving
- operational auditability
- operational memory foundation for future retrieval intelligence

Example output:

```text
app/memory/incident_history/incidents/incident_YYYYMMDD_HHMMSS.json
```

---

## Current Platform Architecture

### High-Level Architecture

```text
Kubernetes Cluster
        |
        v
Signal Collection Layer
        |
        v
Incident Context Engine
        |
        v
Prometheus Observability Correlation
        |
        v
Incident Classification Engine
        |
        v
AI RCA Agent
        |
        v
AI Remediation Agent
        |
        v
Workflow Orchestrator
        |
        v
Operational Memory Store
```

### AI Architecture

```text
RCA Agent
Remediation Agent
        |
        v
      LLMClient
        |
        v
   LLMProvider Contract
        |
        v
   OllamaProvider
        |
        v
      Ollama
```

### Contract Architecture

```text
IncidentContext
        |
        v
IncidentClassification
        |
        v
RCAResponse
        |
        v
RemediationResponse
        |
        v
WorkflowExecutionResponse
```

---

## Repository Structure

```text
autonomous-ops-platform/
|
|-- app/
|   |-- agents/
|   |   `-- sre/
|   |       |-- incident_classifier.py
|   |       |-- rca_agent.py
|   |       `-- remediation_agent.py
|   |
|   |-- config/
|   |   |-- logging_config.py
|   |   `-- settings.py
|   |
|   |-- llm/
|   |   |-- client.py
|   |   |-- response_validator.py
|   |   `-- providers/
|   |       |-- base.py
|   |       `-- ollama_provider.py
|   |
|   |-- memory/
|   |   `-- incident_history/
|   |       `-- store_incident.py
|   |
|   |-- orchestration/
|   |   `-- incident_workflow.py
|   |
|   |-- schemas/
|   |   |-- ai.py
|   |   |-- classification.py
|   |   |-- incident.py
|   |   |-- metrics.py
|   |   `-- workflow.py
|   |
|   `-- tools/
|       |-- kubernetes/
|       `-- prometheus/
|
|-- docs/
|   `-- architecture/
|       `-- adr/
|
|-- kubernetes/
|-- memory/
|-- screenshots/
|-- README.md
`-- requirements.txt
```

---

## Technology Stack

Current stack:

- Python 3.11+
- Kubernetes Python SDK
- Prometheus
- Ollama
- Qwen 2.5 Coder
- Docker Desktop Kubernetes
- VS Code
- GitHub

Target ecosystem:

- Grafana
- Datadog
- Splunk
- OpenTelemetry
- AWS
- Azure
- Terraform
- Jenkins
- GitHub Actions
- Slack
- Jira
- Confluence
- OpenAI
- Claude
- LangGraph
- MCP ecosystem

---

## Capability Matrix

| Capability | Status |
| --- | --- |
| Kubernetes incident collection | Implemented |
| Incident context engine | Implemented |
| Event correlation | Implemented |
| Log correlation | Implemented |
| Prometheus correlation | Implemented |
| Incident classification | Implemented |
| AI RCA generation | Implemented |
| AI remediation generation | Implemented |
| Incident workflow orchestration | Implemented |
| Typed platform contracts | Implemented |
| LLM provider abstraction | Implemented |
| Incident persistence | Implemented |
| Historical memory foundation | Implemented |
| Multi-agent coordination | Planned |
| Enterprise knowledge retrieval | Planned |
| API control plane | Planned |
| Approval-gated automation | Planned |
| Autonomous remediation | Planned |

---

## Architecture Decision Records

Documented architectural decisions:

```text
docs/architecture/adr/
```

Implemented ADRs:

- ADR-001 Centralized Runtime Settings
- ADR-002 Prometheus Incident Enrichment
- ADR-003 Structured Logging Standardization
- ADR-004 AI Agent Resilience Hardening
- ADR-005 Incident Workflow Orchestration
- ADR-006 Typed Platform Contracts
- ADR-007 LLM Provider Abstraction

---

## Setup

### Prerequisites

Required:

- Python 3.11+
- Kubernetes cluster access
- `kubectl` configured
- Prometheus
- Ollama

Optional future:

- OpenAI, Claude, or Gemini integration

### Environment Setup

Clone:

```bash
git clone https://github.com/hemanthkumar-n/autonomous-ops-platform.git
cd autonomous-ops-platform
```

Create environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:

```env
ENVIRONMENT=development
WORKFLOW_VERSION=v1
PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_TIMEOUT=10
PROMETHEUS_RETRIES=3
MAX_LOG_LINES=50
ENABLE_POD_LOG_COLLECTION=true
ENABLE_EVENT_COLLECTION=true
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=qwen2.5-coder:latest
AI_REQUEST_TIMEOUT=120
PERSIST_INCIDENTS=true
SAFE_MODE=true
ENABLE_DESTRUCTIVE_REMEDIATION=false
```

---

## Example Commands

Collect incident context:

```bash
python -m app.tools.kubernetes.incident_context
```

Run classification:

```bash
python -m app.agents.sre.incident_classifier
```

Run RCA:

```bash
python -m app.agents.sre.rca_agent
```

Run remediation:

```bash
python -m app.agents.sre.remediation_agent
```

Run orchestrated workflow:

```bash
python -m app.orchestration.incident_workflow
```

Quick validation before commit:

```bash
python -m app.agents.sre.incident_classifier
python -m app.agents.sre.rca_agent
python -m app.agents.sre.remediation_agent
python -m app.orchestration.incident_workflow
```

---

## Current Maturity

Implemented:

- Phase 1: platform foundation
- Phase 2: hardening
- Phase 3.1: typed contracts
- Phase 3.2: AI provider abstraction

Current status:

**Enterprise engineering foundation established.**

---

## Roadmap

### Phase 4: Operational Memory Architecture

- incident memory
- runbook memory
- architecture memory
- vector retrieval
- knowledge indexing

### Phase 5: API Control Plane

- FastAPI interfaces
- workflow APIs
- operational query APIs
- AI control APIs

### Phase 6: Autonomous Execution Governance

- approval workflows
- execution safety policies
- remediation gates
- audit controls

### Phase 7: Advanced AI Routing

- multi-provider routing
- provider failover
- retry orchestration
- model governance
- cost controls

### Phase 8: Autonomous Operational Intelligence

```text
signals -> context -> intelligence -> reasoning -> safe automation
```

Target capabilities:

- approval-gated remediation
- restart automation
- scaling workflows
- rollback intelligence
- alert triage
- autonomous operational decision support

---

## Engineering Philosophy

Design principles:

- enterprise-first architecture
- schema-first contracts
- modular engineering
- production-oriented evolution
- provider independence
- observability-aware reasoning
- safe automation boundaries
- context-first AI design
- operational reliability focus
- future autonomous execution governance

---

## Contribution Philosophy

This project is being engineered as a serious platform architecture initiative.

Contributions should align with:

- clean architecture
- deterministic contracts
- observability
- modularity
- enterprise operational safety

---

## Disclaimer

Current implementation provides AI-assisted operational intelligence and safe remediation recommendations.

It does not autonomously execute destructive production actions.

Execution automation will be introduced only through explicit governance and approval controls.

---

## About the Builder

**Hemanth Kumar**

Principal SRE | Platform Engineering | DevOps | Kubernetes | AWS | Azure | Terraform | CI/CD | Observability | Incident Response

14+ years of infrastructure engineering, reliability engineering, DevOps automation, and enterprise operations leadership.

This platform serves as a flagship engineering initiative demonstrating enterprise AI operations architecture and autonomous platform engineering vision.

LinkedIn:

<https://www.linkedin.com/in/hemanthkumarn/>

GitHub:

<https://github.com/hemanthkumar-n>

---

## Strategic Direction

Autonomous Ops Platform is not intended to remain a Kubernetes troubleshooting tool.

It is being architected as a long-term enterprise AI operations platform for autonomous reliability engineering.
