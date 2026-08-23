# Autonomous Ops Platform

<p align="center">
  <strong>Evidence-Driven Autonomous Investigation for SRE and Platform Engineering</strong>
</p>

<p align="center">
  Linux • Kubernetes • Observability • Incident Intelligence • Operational Memory • Bounded AI
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/AOP-v0.43.0-success" alt="AOP v0.43.0" />
  <img src="https://img.shields.io/badge/Investigation-Autonomous%20%26%20Bounded-blueviolet" alt="Bounded Autonomous Investigation" />
  <img src="https://img.shields.io/badge/LLM-Ollama%20%7C%20Kimi-green" alt="LLM Providers" />
  <img src="https://img.shields.io/badge/Safety-Read--Only%20Investigation-orange" alt="Read-Only Investigation" />
</p>

---

## Overview

Autonomous Ops Platform (AOP) is an operational intelligence platform for Site Reliability Engineering, platform engineering, and infrastructure operations.

> **Mission:** Capture experienced SRE investigation judgment as deterministic, explainable, reusable operational intelligence that can collect evidence, identify what is missing, choose safe next checks, reason across domains, remember prior incidents, and stop when the evidence is sufficient.

AOP is not intended to be a chatbot wrapper or an unrestricted remediation bot. The current engineering direction is **bounded autonomous investigation**.

```text
Observe
  -> Create InvestigationCase
  -> Collect Evidence
  -> Detect / Correlate
  -> Identify Evidence Gaps
  -> Plan Safe Next Evidence
  -> Re-evaluate Confidence
  -> RCA Candidate
  -> Validate / Confirm
  -> Learn
```

Core rules:

```text
Evidence before AI
Safety before autonomy
Candidate RCA before confirmed RCA
Read-only investigation before remediation
Historical similarity is a clue, not proof
```

For the detailed active-branch state, see [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md).

---

## Current Development Release

```text
AOP v0.43.0
```

Active branch:

```text
feature/autonomous-investigation-collectors-v043
```

v0.43 extends the v0.42 autonomous investigation foundation from Linux memory into **CPU, disk/storage, and network** evidence collection.

### What v0.43 proves

AOP can now take unresolved evidence gaps from one canonical investigation, select only registered read-only collectors, collect deterministic evidence from several Linux domains, normalize it into one case, update hypothesis support and `why` / `why_not`, and re-evaluate whether to continue or stop at an RCA candidate.

```text
InvestigationCase
      |
      v
EvidencePlanner
      |
      +--> linux_memory
      +--> linux_cpu
      +--> linux_disk
      +--> linux_network
      |
      v
Existing deterministic AOP workflows
      |
      v
EvidenceCollectionResult
      |
      +--> EvidenceItem(s)
      +--> resource identity
      +--> hypothesis support
      +--> gap resolution
      |
      v
Confidence re-evaluation
      |
      +--> collect more evidence
      +--> RCA candidate
      +--> safe stop
```

### RCA safety contract

AOP explicitly separates an RCA candidate from a confirmed root cause:

```text
rca_candidate != root_cause
```

`rca_candidate` can contain a hypothesis, confidence, supporting/contradicting evidence, and `why` / `why_not`. `root_cause` remains unconfirmed until a controlled validation/confirmation path promotes it.

---

## Implemented Platform Capabilities

### Autonomous Investigation Core

- canonical `InvestigationCase`
- affected-resource identity
- normalized evidence items
- evidence gaps with RCA-blocking semantics
- competing hypotheses
- deterministic confidence evaluation
- `why` and `why_not` reasoning
- explicit `RootCauseCandidate`
- audit timeline
- bounded evidence planner
- maximum step/request budgets
- registered collector execution only
- safe stop behavior when evidence or collectors are unavailable

### Linux Operational Intelligence

- CPU/load/D-state/I/O-wait/steal-time investigation
- memory/OOM/swap/cgroup investigation
- disk/filesystem/inode/LVM/multipath/NFS/I/O investigation
- network/NIC/carrier/error/route/resolver investigation
- boot/kernel/kdump/grubby investigation
- systemd service failure/restart-loop investigation
- container runtime troubleshooting planning
- host-level cross-domain correlation
- cgroup v1/v2, PSI, VM and scheduler evidence
- command explanation and safe troubleshooting plans

### Autonomous Linux Collectors

| Collector | Backing workflow | Planner scope | Safety |
|---|---|---|---|
| `linux_memory` | deterministic memory workflow | host/node/PID | read-only |
| `linux_cpu` | deterministic CPU workflow | host/node | read-only |
| `linux_disk` | deterministic disk workflow | host/node/path | read-only |
| `linux_network` | deterministic network workflow | host/node/interface | read-only |

Autonomous evidence acquisition forces `persist=False` to avoid unintended incident-memory side effects while a case is still being investigated.

### Kubernetes

- cluster health and workload inspection
- pod/container evidence
- warning events and logs
- deterministic incident classification
- Kubernetes issue knowledge
- expert troubleshooting shortcuts
- Kubernetes-to-Linux correlation guidance
- node-condition evidence planning
- safe simulation manifests for common incident types

### Operational Memory and Knowledge

- structured JSON incident history
- ChromaDB semantic memory
- exact + semantic hybrid retrieval
- deterministic fallback when semantic retrieval is unavailable
- deterministic incident fingerprints
- recurrence/pattern intelligence
- bounded runbook/RAG retrieval
- provenance-controlled external Kubernetes failure-story metadata
- source-reviewed operational guidance
- unified operational knowledge retrieval with source/trust attribution

### AI Layer

- provider-neutral LLM client/router
- Ollama as the local/default provider
- optional Kimi/Moonshot provider configuration
- deterministic token-budget estimation
- light/standard/deep/local model-tier policy
- bounded AI context from current evidence, patterns, history, and trusted knowledge

AI is an assistance layer. The safety and confidence gates remain deterministic platform controls.

---

## Safety Boundary

Current autonomous investigation does **not** provide unrestricted execution.

AOP does not autonomously perform:

- arbitrary shell commands
- free-form command execution generated by an LLM
- process kills or service restarts
- filesystem cleanup or mutation
- route/firewall/NIC mutation
- Kubernetes mutation
- automatic remediation
- automatic RCA-candidate promotion to confirmed root cause

Existing read-only workflows are the execution boundary. Consequential actions remain future work requiring policy, auditability, validation, and human approval.

---

## Quick Start

```bash
git clone https://github.com/hemanthkumar-n/autonomous-ops-platform.git
cd autonomous-ops-platform

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

aop --version
aop health
```

For active v0.43 development:

```bash
git fetch origin
git checkout feature/autonomous-investigation-collectors-v043
git pull origin feature/autonomous-investigation-collectors-v043
```

---

## Useful CLI Paths

### Linux

```bash
aop linux health
aop linux explain "df -hT"
aop linux plan disk --path /var
aop linux plan scenario --list

aop investigate linux memory
aop investigate linux cpu
aop investigate linux disk --path /var
aop investigate linux network --iface ens5
aop investigate linux service --service nginx
aop investigate linux boot
aop investigate linux host
```

### Kubernetes

```bash
aop kb health
aop kb po
aop kb ev
aop kb inv -n payments

aop kx oom
aop kx crash
aop kx image

aop investigate k8s-linux --incident OOMKilled
aop investigate k8s-node --condition MemoryPressure
```

### Knowledge and Memory

```bash
aop memory search --namespace payments
aop memory patterns --min-count 2
aop knowledge search --query "dns timeout"
aop runbooks search --query "CrashLoopBackOff"
```

---

## v0.43 Dry Run

Focused collector tests:

```bash
python -m unittest tests.test_autonomous_linux_collectors -v
```

Multi-collector demo:

```bash
python -m app.investigation.demo_multi_collector_loop
python -m app.investigation.demo_multi_collector_loop --format json
```

Full regression suite:

```bash
python -m unittest discover -s tests -v
```

The last confirmed full-suite result is the v0.42 Mac validation:

```text
243 / 243 tests passing
```

v0.43 adds new collector coverage. Its final full-suite count must be recorded after the branch is executed; this README intentionally does not claim an unexecuted validation result.

---

## Current Integration Chain

```text
main
  |
  +-- PR #2: v0.42 bounded autonomous investigation loop
          |
          +-- PR #3: v0.43 Linux multi-collector autonomous investigation
```

v0.43 is intentionally based on v0.42. After v0.42 lands in `main`, v0.43 should be retargeted/reconciled, revalidated, and then promoted for merge.

---

## Architecture Direction

The next major investigation shape is cross-domain:

```text
Kubernetes symptom
      |
      v
Kubernetes read-only collector
      |
      v
Workload + node identity
      |
      v
Linux evidence collectors
      |
      v
Bounded Prometheus history
      |
      v
Competing hypotheses
      |
      v
Confidence + why / why-not
      |
      +--> collect more evidence
      +--> RCA candidate
```

The next high-value engineering priorities are:

1. Kubernetes read-only autonomous collector
2. Prometheus bounded metrics collector
3. cross-domain hypothesis competition
4. structural/semantic incident fingerprints in addition to exact recurrence
5. resolution and outcome learning from confirmed incidents
6. policy-controlled confirmation and, much later, approval-gated remediation

---

## Repository Structure

```text
autonomous-ops-platform/
├── app/
│   ├── agents/sre/                 # deterministic and AI-assisted reasoning
│   ├── cli/                        # aop CLI
│   ├── config/                     # settings and logging
│   ├── investigation/              # canonical case, planner, autonomous loop, collectors
│   ├── llm/                        # provider abstraction and model policy
│   ├── memory/                     # incidents, patterns, retrieval, runbooks
│   ├── orchestration/              # workflows
│   ├── schemas/                    # typed contracts
│   └── tools/
│       ├── linux/                  # read-only Linux evidence/workflows
│       ├── kubernetes/             # Kubernetes evidence/operations
│       ├── prometheus/             # metrics enrichment
│       └── troubleshooting/        # safe catalogs and plans
├── docs/
│   ├── CURRENT_STATUS.md
│   ├── releases/
│   ├── architecture/
│   ├── linux/
│   ├── AOP_PRODUCT_VISION.md
│   └── ROADMAP.md
├── kubernetes/
├── tests/
├── pyproject.toml
└── README.md
```

---

## Key Documentation

| Document | Purpose |
|---|---|
| [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md) | Active development state, autonomy architecture, safety boundary, and next milestone |
| [`docs/releases/v0.43-multi-collector-autonomous-investigation.md`](docs/releases/v0.43-multi-collector-autonomous-investigation.md) | v0.43 release intent and integration boundary |
| [`docs/PROJECT_HANDOVER.md`](docs/PROJECT_HANDOVER.md) | Engineering handover and verified baseline |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Detailed roadmap |
| [`docs/AOP_PRODUCT_VISION.md`](docs/AOP_PRODUCT_VISION.md) | Long-term product direction |
| [`docs/architecture/enterprise-platform-evolution.md`](docs/architecture/enterprise-platform-evolution.md) | Enterprise architecture evolution |
| [`docs/architecture/external-knowledge-ingestion.md`](docs/architecture/external-knowledge-ingestion.md) | External knowledge provenance and review policy |
| [`docs/linux/LINUX_INVESTIGATION_LADDER.md`](docs/linux/LINUX_INVESTIGATION_LADDER.md) | Linux investigation flow |
| [`docs/KUBERNETES_CLI.md`](docs/KUBERNETES_CLI.md) | Kubernetes CLI reference |
| [`docs/LINUX_CLI.md`](docs/LINUX_CLI.md) | Linux CLI reference |

Release-by-release implementation memory is under [`docs/releases/`](docs/releases/).

---

## Technology Stack

| Area | Current technology |
|---|---|
| Language | Python 3.11+ |
| Contracts | Pydantic |
| Kubernetes | Kubernetes Python client |
| Metrics | Prometheus |
| Local LLM | Ollama |
| Optional external LLM | Kimi/Moonshot |
| Reasoning model | `qwen2.5-coder:latest` by default |
| Embeddings | `nomic-embed-text` |
| Vector memory | ChromaDB |
| CLI | Click |
| HTTP | HTTPX / Requests |

---

## Product Philosophy

AOP should behave less like a command generator and more like an experienced incident investigator:

1. establish the facts
2. identify uncertainty
3. generate competing hypotheses
4. determine which evidence can discriminate between them
5. collect that evidence through approved read-only mechanisms
6. update confidence rather than defend the first guess
7. stop when evidence is sufficient or the safe investigation boundary is reached
8. preserve provenance and reasoning for the next incident

That is the foundation for safe autonomous SRE reasoning.

---

## Author

Built by **Hemanth Kumar**.

Senior Site Reliability / Platform Engineering focus across Linux, Kubernetes, cloud infrastructure, observability, incident response, automation, and reliability engineering.

This repository is a flagship engineering project exploring evidence-driven autonomous operations while preserving deterministic controls and production safety.
