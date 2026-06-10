# Autonomous Ops Platform

<p align="center">
  <strong>AI-Native Operational Intelligence for SRE and Platform Engineering</strong>
</p>

<p align="center">
  Linux • Kubernetes • AWS • Observability • Incident Intelligence • Operational Memory
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/AOP-v0.8.1-success" alt="AOP v0.8.1" />
  <img src="https://img.shields.io/badge/Kubernetes-SRE%20Shortcuts-326CE5" alt="Kubernetes SRE Shortcuts" />
  <img src="https://img.shields.io/badge/Observability-Prometheus-red" alt="Prometheus" />
  <img src="https://img.shields.io/badge/LLM-Ollama-green" alt="Ollama" />
  <img src="https://img.shields.io/badge/Safety-Advisory%20Only-orange" alt="Advisory Only" />
</p>

---

## Overview

Autonomous Ops Platform (AOP) is an operational intelligence platform for
Site Reliability Engineering, platform engineering, and infrastructure
operations.

AOP combines:

- deterministic infrastructure troubleshooting
- Kubernetes and Prometheus evidence collection
- AI-assisted root cause analysis
- safe remediation guidance
- structured and semantic incident memory
- reusable CLI workflows for SRE teams

The long-term goal is to provide one operational source of truth across Linux,
Kubernetes, AWS, observability systems, runbooks, incident history, and human
approval workflows.

AOP is not intended to be a chatbot wrapper or a Kubernetes-only tool. It is
being developed as an operational intelligence runtime that can:

```text
Observe
  -> Collect Evidence
  -> Detect
  -> Correlate
  -> Remember
  -> Reason
  -> Recommend
  -> Validate
  -> Act Safely
  -> Learn
```

The durable cross-domain product direction is documented in
[`docs/AOP_PRODUCT_VISION.md`](docs/AOP_PRODUCT_VISION.md).

---

## Current Release

Current version:

```text
AOP v0.8.1
```

The implemented and tested paths currently cover Kubernetes incident
intelligence and the first deterministic Linux troubleshooting CLI.

### Implemented

- installable `aop` command
- native `aop linux` health and diagnostic commands
- bounded, shell-free Linux command execution with JSON output
- CPU, memory, disk, network, process, service, log, kernel, boot, and security
  evidence collection
- read-only Kubernetes SRE shortcuts
- Kubernetes pod and container evidence collection
- node, namespace, deployment, service, event, and log inspection
- Prometheus CPU, memory, and restart enrichment
- deterministic incident classification
- Ollama-based RCA and remediation guidance
- structured JSON incident history
- ChromaDB semantic incident memory
- exact and semantic hybrid retrieval
- graceful exact-memory fallback
- Markdown and JSON incident reports
- typed Pydantic contracts
- twenty-five offline regression tests

### Not Yet Implemented

- deep Linux signal correlation, incident classification, memory, and AI RCA
- AWS and CloudWatch troubleshooting
- operator web UI
- Slack or Microsoft Teams approval workflows
- FastAPI service layer
- authentication and RBAC
- automatic remediation execution
- multi-tenant company onboarding

These are roadmap capabilities, not current claims.

---

## Why AOP

Operational context is usually fragmented:

- alerts and metrics live in monitoring systems
- logs are spread across hosts, pods, and cloud services
- Kubernetes runtime state requires manual inspection
- incident history is buried in tickets and chat threads
- runbook knowledge remains tribal
- root cause analysis is repeatedly recreated

AOP converts these signals into a normalized incident record that can be
searched, explained, reused, and eventually acted upon through controlled
approval workflows.

---

## Five-Minute Showcase

After completing the installation steps:

```bash
# Confirm local dependencies and platform access
aop health

# Review Kubernetes health with SRE-friendly shortcuts
aop kb health
aop kb po
aop kb ev

# Run the complete evidence, classification, memory, and AI workflow
aop kb inv -n ai-lab
```

The showcase demonstrates a single workflow from live Kubernetes evidence to
deterministic classification, historical-memory lookup, AI-assisted RCA, safe
remediation guidance, and persisted incident knowledge.

---

## Linux SRE CLI

The preserved `tshelper` workflow is now available through native AOP commands:

```bash
aop linux health
aop linux cpu
aop linux memory
aop linux disk --path /var
aop linux network
aop linux processes --top 20
aop linux services
aop linux logs
aop linux kernel
aop linux boot
aop linux security
aop linux all
```

Use JSON output for automation:

```bash
aop linux health --json
aop linux network --json
aop linux all --json > linux-report.json
```

The first release is read-only and deterministic. It uses explicit command
arguments without shell evaluation, applies timeouts and output limits,
records missing commands and permission failures as evidence, and avoids
restart, kill, delete, unmount, firewall, and log-clearing actions.

The deeper Linux intelligence roadmap is documented in
[`docs/linux/LINUX_EXPERTISE_BLUEPRINT.md`](docs/linux/LINUX_EXPERTISE_BLUEPRINT.md).

---

## Kubernetes SRE CLI

Use `aop kb` for fast, read-only Kubernetes troubleshooting.

`aop k8s` is an equivalent alias.

### First Response

```bash
aop kb health
aop kb po
aop kb ev
```

### Command Reference

| Command | Alias | Purpose |
|---|---|---|
| `aop kb health` | | Cluster readiness and unhealthy workload summary |
| `aop kb nodes` | `aop kb no` | Node readiness, pressure, and capacity |
| `aop kb namespaces` | `aop kb ns` | Namespace inventory |
| `aop kb deployments` | `aop kb deploy` | Deployment replica health |
| `aop kb services` | `aop kb svc` | Service types, addresses, and ports |
| `aop kb pods` | `aop kb po` | Unhealthy pods |
| `aop kb events` | `aop kb ev` | Recent warning events |
| `aop kb logs POD` | `aop kb log POD` | Current or previous container logs |
| `aop kb describe POD` | `aop kb desc POD` | Pod state, resources, and events |
| `aop kb investigate` | `aop kb inv` | Full AI and memory-aware investigation |

Examples:

```bash
# Namespace health
aop kb health -n payments

# Unhealthy pods
aop kb po -n payments

# All pods
aop kb po -n payments --all

# Warning events
aop kb ev -n payments

# Previous crashed-container logs
aop kb log checkout-abc123 \
  -n payments \
  -c checkout \
  --previous

# Normalized pod investigation
aop kb desc checkout-abc123 -n payments

# Scriptable output
aop kb po -n payments --json
```

The complete shortcut guide is available in
[`docs/KUBERNETES_CLI.md`](docs/KUBERNETES_CLI.md).

---

## AI-Assisted Investigation

Run the complete incident workflow:

```bash
aop kb inv -n payments
```

The compatible long-form command remains available:

```bash
aop investigate k8s --namespace payments
```

Generate a presentation-ready Markdown report:

```bash
aop kb inv \
  -n payments \
  --format markdown \
  --output reports/payments-incident.md
```

Search structured operational memory:

```bash
aop memory search --namespace payments
aop memory search --incident-type MemoryExhaustion
```

---

## Incident Workflow

```text
Kubernetes Cluster
       |
       v
Incident Context Collection
  - pod lifecycle
  - container state
  - termination history
  - restart counts
  - resource requests and limits
  - logs and events
       |
       +-------------------+
       |                   |
       v                   v
Prometheus Metrics    Deterministic Rules
       |                   |
       +---------+---------+
                 |
                 v
       Enriched Incident Context
                 |
                 v
       Primary Classification
                 |
                 v
       Hybrid Memory Retrieval
        - exact JSON memory
        - semantic Chroma memory
                 |
                 v
       Ollama RCA and Guidance
                 |
                 v
       Structured Persistence
        + Semantic Indexing
```

---

## Deterministic Classification

Supported incident rules currently include:

| Kubernetes signal | AOP classification | Severity |
|---|---|---|
| `OOMKilled` | `MemoryExhaustion` | Critical |
| `CrashLoopBackOff` | `ApplicationCrashLoop` | High |
| `ImagePullBackOff` | `ImagePullFailure` | High |
| `ErrImagePull` | `ImagePullFailure` | High |
| `CreateContainerConfigError` | `ContainerConfigurationFailure` | High |
| `CreateContainerError` | `ContainerStartupFailure` | High |
| `FailedScheduling` | `SchedulingFailure` | Critical |

Termination history takes precedence when appropriate. For example, a pod
currently showing `CrashLoopBackOff` with a previous `OOMKilled` termination
is classified as memory exhaustion.

Deterministic findings are established before LLM reasoning.

---

## Operational Memory

AOP maintains two complementary memory layers.

### Structured Memory

Normalized incident records are stored as JSON under:

```text
data/incidents/
```

Structured memory provides:

- auditability
- exact filtering
- deterministic historical lookup
- canonical incident records

### Semantic Memory

Incident documents are embedded with:

```text
nomic-embed-text
```

and indexed locally using:

```text
ChromaDB
```

Semantic memory supports similarity-based historical recall.

### Fallback Behavior

```text
Semantic memory unavailable
        |
        v
Use exact structured memory
        |
        v
If no history exists, continue with current evidence
```

Memory improves analysis but does not become a single point of failure.
Programming errors are not silently hidden behind fallback behavior.

---

## Architecture Principles

### Evidence Before AI

AI reasoning consumes normalized infrastructure evidence. Agents do not begin
from an alert title alone.

### Linux and Kubernetes Correlation

Kubernetes symptoms are not assumed to be Kubernetes-only failures. Current AI
prompts require relevant Linux node correlation for memory, CPU, disk, inode,
network, DNS, storage, runtime, scheduling, and node-readiness incidents. If
host evidence is unavailable, AOP must state the gap and recommend the next
read-only `aop linux` command rather than inventing node facts.

This criterion comes from the founder's authored SRE knowledge record:
[`linkedin_kubernetes_linux_criteria.md`](app/memory/knowledgebase/linkedin_kubernetes_linux_criteria.md).

### Deterministic Before Probabilistic

Known operational failure signals are classified through explicit rules before
LLM analysis.

### Typed Contracts

Pydantic models define module boundaries, including:

- `IncidentContext`
- `IncidentClassification`
- `PodMetrics`
- `RCAResponse`
- `RemediationResponse`
- `IncidentMemory`
- `WorkflowExecutionResponse`

### Provider Abstraction

```text
Agent
  -> LLMClient
  -> LLMProvider
  -> OllamaProvider
```

Equivalent abstractions exist for embeddings and vector stores.

### Safety by Design

- read-only Kubernetes shortcut commands
- validation-first recommendations
- no destructive execution
- escalation when confidence is limited
- future consequential actions require policy and human approval

---

## Repository Structure

```text
autonomous-ops-platform/
├── app/
│   ├── agents/sre/                 # classification, RCA, remediation
│   ├── cli/                        # aop and aop kb commands
│   ├── config/                     # runtime settings and logging
│   ├── llm/                        # LLM and embedding abstractions
│   ├── memory/                     # structured and semantic memory
│   ├── orchestration/              # incident workflow
│   ├── schemas/                    # typed platform contracts
│   └── tools/
│       ├── kubernetes/             # Kubernetes evidence and operations
│       └── prometheus/             # metrics enrichment
├── docs/
│   ├── architecture/adr/           # architecture decisions
│   ├── AOP_PRODUCT_VISION.md       # durable product direction
│   ├── AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md
│   └── KUBERNETES_CLI.md
├── kubernetes/
│   ├── incidents/                  # reproducible failure scenarios
│   └── monitoring/                 # Prometheus manifests
├── tests/
├── pyproject.toml
└── README.md
```

Many Linux, AWS, DevOps, security, and vendor-specific modules are currently
future placeholders.

---

## Technology Stack

| Area | Current technology |
|---|---|
| Language | Python 3.11+ |
| Contracts | Pydantic |
| Kubernetes | Kubernetes Python client |
| Metrics | Prometheus |
| Local LLM | Ollama |
| Reasoning model | `qwen2.5-coder:latest` |
| Embeddings | `nomic-embed-text` |
| Vector memory | ChromaDB |
| CLI | Click |
| HTTP | HTTPX and Requests |
| Future service layer | FastAPI |

---

## Installation

### Prerequisites

- Python 3.11+
- Git
- Kubernetes cluster and working kubeconfig
- Prometheus endpoint
- Ollama

### Setup

```bash
git clone https://github.com/hemanthkumar-n/autonomous-ops-platform.git
cd autonomous-ops-platform

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

### Ollama Models

```bash
ollama pull qwen2.5-coder:latest
ollama pull nomic-embed-text
```

### Configuration

```bash
cp .env.example .env
```

Important defaults:

```env
PROMETHEUS_URL=http://localhost:9090
ENABLE_METRICS_ENRICHMENT=true

OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL_NAME=qwen2.5-coder:latest
EMBEDDING_MODEL_NAME=nomic-embed-text

INCIDENT_HISTORY_DIR=data/incidents
VECTORSTORE_PATH=data/vectorstore/chroma
VECTORSTORE_COLLECTION_NAME=incident_memory

SAFE_MODE=true
ENABLE_DESTRUCTIVE_REMEDIATION=false
```

Validate:

```bash
aop --version
aop health
aop kb --help
```

Detailed setup instructions are available in
[`docs/setup/installation.md`](docs/setup/installation.md).

---

## Reproducible Demo Incidents

Create the test namespace:

```bash
kubectl create namespace ai-lab
```

### ImagePullBackOff

```bash
kubectl apply \
  -f kubernetes/incidents/imagepull/broken-nginx.yaml
```

### OOMKilled

```bash
kubectl apply \
  -f kubernetes/incidents/oomkilled/oom-test.yaml
```

Investigate:

```bash
aop kb health -n ai-lab
aop kb po -n ai-lab
aop kb ev -n ai-lab
aop kb inv -n ai-lab
```

---

## Testing

Run the offline regression suite:

```bash
python -m unittest discover -s tests -v
```

Current baseline:

```text
25 tests passing
```

The tests cover:

- CLI discovery and aliases
- Linux CLI discovery, JSON output, and prioritized health findings
- shell-free Linux command execution, timeout handling, and missing utilities
- bounded Linux process output and diagnostic ordering
- Kubernetes health and JSON output
- healthy and completed pod normalization
- primary incident classification
- LLM provider contracts
- hybrid-memory fallback
- workflow alignment
- deep-investigation delegation

Live Kubernetes and Prometheus validation remains a separate environment test.

---

## Documentation

| Document | Purpose |
|---|---|
| [`docs/AOP_PRODUCT_VISION.md`](docs/AOP_PRODUCT_VISION.md) | Linux, Kubernetes, AWS, UI, Slack/Teams, and onboarding vision |
| [`docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md`](docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md) | Compact current implementation memory |
| [`docs/KUBERNETES_CLI.md`](docs/KUBERNETES_CLI.md) | Kubernetes shortcut reference |
| [`docs/LINUX_CLI.md`](docs/LINUX_CLI.md) | Native Linux troubleshooting command reference |
| [`docs/linux/LINUX_EXPERTISE_BLUEPRINT.md`](docs/linux/LINUX_EXPERTISE_BLUEPRINT.md) | Linux administration expertise and implementation direction |
| [`docs/linux/tshelper-original/`](docs/linux/tshelper-original/) | Preserved original `tshelper` source materials |
| [`linux_troubleshooting_command_catalog.md`](app/memory/knowledgebase/linux_troubleshooting_command_catalog.md) | Canonical Linux commands, arguments, interpretation, and safety memory |
| [`docs/setup/installation.md`](docs/setup/installation.md) | Detailed local installation |
| [`docs/architecture/adr/`](docs/architecture/adr/) | Architecture decision records |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |

---

## Roadmap

### 1. Kubernetes Live Showcase

- validate Kubernetes and Prometheus end to end
- record repeatable ImagePullBackOff and OOMKilled demonstrations
- verify reports and incident-memory persistence

### 2. Engineering Foundation

- continuous integration
- formatting, linting, and type checking
- broader deterministic test coverage
- structured AI output contracts

### 3. Linux Operational Intelligence

- CPU, memory, process, disk, filesystem, inode, and swap diagnostics
- systemd and service troubleshooting
- networking, DNS, ports, sockets, and routes
- kernel, boot, OOM, security, and journal evidence
- reusable Linux operational memory and runbooks

Linux is a first-class product domain and a core source of project expertise.

### 4. Operator UI

- active Linux and Kubernetes incidents
- evidence timeline
- deterministic findings
- RCA and remediation guidance
- operational-memory search
- approval and audit status

### 5. Slack and Microsoft Teams

- incident notification
- ownership and escalation
- approve, reject, defer, and escalate decisions
- execution and validation updates

Chat integrations will be collaboration surfaces; the AOP incident record
remains the source of truth.

### 6. AWS Operational Intelligence

- CloudWatch logs and metrics
- EC2, EBS, ELB/ALB, RDS, Lambda, EKS, IAM, VPC, Route 53, and S3
- CloudTrail change correlation
- AWS Health context

### 7. Enterprise Onboarding and Governance

- FastAPI service layer
- authentication and RBAC
- secrets management
- audit trails
- policy-controlled actions
- portable company deployment
- approval-gated remediation

---

## Safety and Disclaimer

The current implementation provides AI-assisted incident intelligence and
safe remediation recommendations.

It does not autonomously execute destructive production actions.

Execution automation will be introduced only through explicit governance,
policy enforcement, auditability, and human approval controls.

---

## Contribution Philosophy

Contributions should align with:

- clean architecture
- deterministic contracts
- evidence-driven troubleshooting
- operational observability
- modular provider integrations
- testable behavior
- enterprise operational safety

---

## Author

Built by:

**Hemanth Kumar**

Principal SRE | Platform Engineering | DevOps | Kubernetes | AWS | Azure |
Terraform | CI/CD | Observability | Incident Response

14+ years of infrastructure engineering, reliability engineering, DevOps
automation, and enterprise operations leadership.

This platform serves as a flagship engineering initiative demonstrating
enterprise AI operations architecture and autonomous platform engineering
vision.

LinkedIn:
https://www.linkedin.com/in/hemanthkumarn/

GitHub:
https://github.com/hemanthkumar-n

### Strategic Direction

Autonomous Ops Platform is not intended to remain a Kubernetes troubleshooting
tool.

It is being architected as a long-term enterprise AI operations platform for
autonomous reliability engineering.
