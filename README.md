# Autonomous Ops Platform

<p align="center">
  <strong>Enterprise AI-Powered Incident Intelligence & Autonomous Operations Platform</strong>
</p>

<p align="center">
  Built for SRE • Platform Engineering • Kubernetes Operations • DevOps • Cloud Reliability
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" />
  <img src="https://img.shields.io/badge/Kubernetes-Production%20Focused-326CE5" />
  <img src="https://img.shields.io/badge/SRE-Incident%20Automation-orange" />
  <img src="https://img.shields.io/badge/Observability-Prometheus-red" />
  <img src="https://img.shields.io/badge/LLM-Ollama-green" />
  <img src="https://img.shields.io/badge/Architecture-Enterprise%20Grade-purple" />
</p>

---

## Executive Summary

Autonomous Ops Platform is an enterprise-focused AI-driven incident intelligence platform engineered to transform raw infrastructure telemetry into structured operational intelligence.

It combines Kubernetes diagnostics, observability enrichment, deterministic incident classification, AI-assisted root cause analysis, remediation guidance, and persistent operational memory.

**Vision:** evolve from AI-assisted incident response into a policy-governed autonomous operations control plane.

---

## Why This Platform Exists

Modern platform teams face:

- Fragmented observability
- Disconnected operational tooling
- Tribal troubleshooting dependency
- Repetitive incident triage
- Slow root cause analysis
- Inconsistent remediation execution
- Alert fatigue
- Weak historical incident reuse

Traditional tools expose signals.
Engineers still perform the reasoning.

**Autonomous Ops Platform closes that gap.**

---

## Platform Architecture

```text
Infrastructure Signals
        ↓
Kubernetes Incident Context Engine
        ↓
Observability Enrichment Layer
        ↓
Incident Classification Engine
        ↓
AI RCA Intelligence
        ↓
Remediation Intelligence
        ↓
Workflow Orchestration
        ↓
Incident Persistence Layer
        ↓
Future Operational Memory Intelligence
        ↓
Autonomous Safe Operations
```

---

## Current Production Capabilities (Day 6)

### Kubernetes Incident Context Engine

Implemented:

- Multi-namespace pod discovery
- Pod lifecycle inspection
- Container runtime diagnostics
- Restart telemetry correlation
- Termination reason extraction
- Resource inspection
- Bounded container log retrieval
- Kubernetes event correlation
- Namespace-aware diagnostics
- Node attribution

Supported incident patterns:

- OOMKilled
- CrashLoopBackOff
- ImagePullBackOff
- ErrImagePull
- CreateContainerConfigError
- CreateContainerError
- FailedScheduling

---

### Observability Enrichment

Prometheus-backed telemetry:

- Pod memory usage
- Pod CPU usage
- Restart telemetry

Production hardening completed:

- Environment-driven configuration
- Configurable timeout handling
- Graceful failure fallback
- No hardcoded endpoints
- Reusable telemetry abstraction

Example configuration:

```bash
PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_TIMEOUT=10
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=qwen2.5-coder
```

---

### Incident Classification Engine

Deterministic normalization layer converting raw failure signals into actionable incident intelligence.

Examples:

| Raw Signal | Normalized Incident |
|----------|---------------------|
| OOMKilled | MemoryExhaustion |
| ImagePullBackOff | ImagePullFailure |
| CrashLoopBackOff | ApplicationCrashLoop |

Capabilities:

- Incident typing
- Severity scoring
- Confidence scoring
- Team ownership recommendations

---

### AI RCA Engine

Current stack:

- Ollama
- qwen2.5-coder

AI reasoning inputs:

- Kubernetes lifecycle state
- Container runtime state
- Restart counts
- Termination reasons
- Resource limits
- Kubernetes events
- Bounded logs
- Prometheus metrics

Capabilities:

- Incident summarization
- Root cause analysis
- Signal correlation
- Severity reasoning
- Ownership guidance
- Preventive recommendations

---

### Remediation Intelligence

Safe advisory remediation engine.

Capabilities:

- Immediate safe actions
- Kubernetes validation commands
- Escalation guidance
- Preventive recommendations
- Operational risk awareness

**Safety boundary:** advisory only. No destructive autonomous execution.

---

### Workflow Orchestration

End-to-end automated incident workflow:

```text
Detect
→ Collect Incident Context
→ Enrich Observability
→ Classify Incident
→ Generate RCA
→ Generate Remediation
→ Persist Incident Record
```

Implemented:

- Incident-by-incident orchestration
- Unified structured payload generation
- Workflow persistence
- Incident archive creation

---

### Incident Persistence Layer

Storage path:

```text
app/memory/incident_history/incidents/
```

Purpose:

- Audit trail
- Historical incident archive
- Recurring issue analysis
- Future operational memory
- Retrieval-augmented troubleshooting foundation

---

## Repository Structure

```text
autonomous-ops-platform/
├── app/
│   ├── agents/sre/
│   ├── tools/kubernetes/
│   ├── tools/prometheus/
│   ├── orchestration/
│   ├── memory/
│   ├── config/
│   ├── llm/
│   ├── prompts/
│   └── api/
├── docs/
├── infra/
├── kubernetes/
├── scripts/
├── screenshots/
└── tests/
```

---

## Execution

Run full workflow:

```bash
python -m app.orchestration.incident_workflow
```

Run individual modules:

```bash
python -m app.tools.kubernetes.incident_context
python -m app.agents.sre.incident_classifier
python -m app.agents.sre.rca_agent
python -m app.agents.sre.remediation_agent
python -m app.tools.prometheus.metrics_tools
```

---

## Production Hardening Progress

### Completed — Hardening Phase 1

- Removed hardcoded Prometheus endpoint
- Environment-driven configuration
- Timeout governance
- Reusable telemetry abstraction
- Graceful dependency degradation
- Incident persistence workflow
- Observability enrichment hardening

### Planned Hardening

**Phase 2**
- Structured logging
- Correlation IDs
- Central exception handling

**Phase 3**
- Pydantic schemas
- Typed workflow contracts
- Response validation

**Phase 4**
- Retry/backoff policies
- Circuit breakers
- Dependency resilience

**Phase 5**
- Secrets management
- RBAC-aware execution
- Credential abstraction

**Phase 6**
- Provider plugin architecture
- Multi-observability integrations
- Cloud provider adapters

**Phase 7**
- Approval-gated remediation
- Policy enforcement
- Human-in-loop execution

---

## Future Roadmap

### Observability Intelligence

Planned:

- Grafana correlation
- Datadog integration
- Splunk analysis
- OpenTelemetry enrichment
- Anomaly detection

### Enterprise Knowledge Intelligence

Planned:

- Jira incidents
- Confluence runbooks
- RCA history correlation
- Troubleshooting knowledge retrieval

### Agentic Operations

Planned agents:

- Kubernetes Agent
- Linux Diagnostics Agent
- Cloud Operations Agent
- Observability Agent
- Security Agent
- Release Intelligence Agent

### Autonomous Operations

Long-term direction:

- Approval-gated remediation
- Policy-driven execution
- Safe automation boundaries
- Autonomous operational workflows

---

## Technology Stack

Current:

- Python
- Kubernetes Python SDK
- Kubernetes
- Prometheus
- Ollama
- qwen2.5-coder
- Docker Desktop
- GitHub
- VS Code

Planned:

- Grafana
- Datadog
- Splunk
- OpenTelemetry
- AWS
- Azure
- Terraform
- Jenkins
- GitHub Actions
- LangGraph
- MCP ecosystem

---

## Author

**Hemanth Kumar**

Principal SRE | Platform Engineering | DevOps | Kubernetes | AWS | Azure | Terraform | Observability | Incident Response

Focus Areas:

- AI for Infrastructure Operations
- Autonomous Platform Engineering
- Kubernetes Reliability Automation
- Operational Intelligence Systems

GitHub: https://github.com/hemanthkumar-n  
LinkedIn: https://www.linkedin.com/in/hemanthkumarn/

---

## Final Direction

This is **not a demo chatbot project**.

This is the foundation for an **enterprise autonomous operations control plane** engineered with production-grade platform discipline.