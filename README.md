# Autonomous Ops Platform

<p align="center">
  <strong>AI-Native Operational Intelligence for SRE and Platform Engineering</strong>
</p>

<p align="center">
  Linux • Kubernetes • AWS • Observability • Incident Intelligence • Operational Memory
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/AOP-v0.38.0-success" alt="AOP v0.38.0" />
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

> **Mission:** Build a unique SRE tool that captures experienced Linux,
> Kubernetes, AWS, observability, and incident-response judgment as one source
> of operational truth. AOP should teach, investigate, remember, and guide
> safe action instead of behaving like a generic command wrapper.

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

The enterprise platform evolution is documented in
[`docs/architecture/enterprise-platform-evolution.md`](docs/architecture/enterprise-platform-evolution.md).

## Platform Evolution

AOP is being built as a staged platform, not as a one-off CLI.

```text
Reactive Operations
  -> AI-Assisted Incident Response
  -> Operational Learning Platform
  -> Autonomous Operational Intelligence
  -> Safe Self-Healing Platform Engineering
```

The current implementation proves the early platform core:

- deterministic Linux and Kubernetes evidence collection
- operational memory
- provider abstraction
- token-budget and model-tier planning
- safe, read-only investigation workflows

The current intelligence milestone is bounded runbook/RAG retrieval: matching
trusted operational snippets to an incident without dumping full documents into
prompts.

The dashboard and observability strategy is documented in
[`docs/architecture/observability-dashboard-strategy.md`](docs/architecture/observability-dashboard-strategy.md).
AOP will use Prometheus and Grafana where useful, but will keep its own
provider-neutral evidence and dashboard model for custom UI, reports, AI
context, alert triage, and incident memory.

For release-by-release human context, read
[`docs/releases/`](docs/releases/). These notes are written for future team
members, ChatGPT handoffs, and Codex sessions that need to understand why a
release exists.

---

## Current Release

Current version:

```text
AOP v0.38.0
```

The implemented and tested paths currently cover Kubernetes incident
intelligence, deterministic Linux troubleshooting, Linux disk incident
intelligence, Linux memory/OOM investigation, Linux CPU/load investigation,
Linux network/NIC investigation, NIC/interface-card evidence,
systemd service investigation, a consolidated Linux investigation ladder,
Kubernetes-to-Linux correlation training, command-reasoning workflows,
curated Kubernetes issue knowledge, Kubernetes investigation guidance,
Kubernetes expert shortcuts, Linux expert shortcuts, Linux boot/kernel/grubby
investigation, deeper Linux storage/LVM/NFS investigation, complex Linux
scenario plans, host-level Linux correlation, and provider-neutral
evidence/dashboard contracts, Kubernetes node-to-Linux evidence planning,
container runtime troubleshooting planning, the first enterprise-grade
canonical investigation case model, provider-neutral LLM routing with optional
Kimi/Moonshot configuration, deterministic AI token-budget/model-tier
planning, restored enterprise platform roadmap/narrative docs, and the first
Incident Pattern Intelligence recurrence lookup wired into Kubernetes
investigation output, bounded pattern context in RCA prompts, Linux summary
recurrence hints, and a safe troubleshooting catalog runner ported from the
old AOP CLI transition branch, plus the first bounded runbook/RAG retrieval
foundation for trusted investigation context.

### Release Memory

| Release | What it proves | Human reference |
|---|---|---|
| `v0.38.0` | AOP can retrieve trusted runbook snippets and feed bounded RAG context into RCA prompts | [`docs/releases/v0.38-runbook-rag-retrieval-foundation.md`](docs/releases/v0.38-runbook-rag-retrieval-foundation.md) |
| `v0.37.0` | AOP can safely inspect and run known catalog commands while closing stale feature branches | [`docs/releases/v0.37-safe-catalog-runner-branch-closure.md`](docs/releases/v0.37-safe-catalog-runner-branch-closure.md) |
| `v0.36.0` | AOP can feed bounded recurrence context into RCA prompts and show Linux recurrence hints | [`docs/releases/v0.36-pattern-context-rca-linux-summaries.md`](docs/releases/v0.36-pattern-context-rca-linux-summaries.md) |
| `v0.35.0` | AOP can surface exact historical recurrence hints inside Kubernetes investigation output | [`docs/releases/v0.35-pattern-aware-investigation-output.md`](docs/releases/v0.35-pattern-aware-investigation-output.md) |
| `v0.34.0` | AOP can detect recurring Kubernetes and Linux incident patterns from structured memory | [`docs/releases/v0.34-incident-pattern-intelligence.md`](docs/releases/v0.34-incident-pattern-intelligence.md) |
| `v0.33.0` | AOP has a clear enterprise platform narrative and incident-pattern intelligence roadmap | [`docs/releases/v0.33-enterprise-platform-narrative.md`](docs/releases/v0.33-enterprise-platform-narrative.md) |
| `v0.32.0` | AOP can estimate evidence tokens and choose a light, standard, deep, or local reasoning tier before spending model calls | [`docs/releases/v0.32-ai-token-budget-model-policy.md`](docs/releases/v0.32-ai-token-budget-model-policy.md) |
| `v0.31.0` | AOP can route reasoning through a provider boundary instead of hardcoding one LLM backend | [`docs/releases/v0.31-llm-provider-routing.md`](docs/releases/v0.31-llm-provider-routing.md) |
| `v0.30.0` | AOP has a canonical investigation case model for enterprise-grade agent reasoning | [`docs/releases/v0.30-enterprise-investigation-core.md`](docs/releases/v0.30-enterprise-investigation-core.md) |
| `v0.29.0` | AOP can train SREs and agents through safe container runtime troubleshooting plans | [`docs/releases/v0.29-container-runtime-troubleshooting-planner.md`](docs/releases/v0.29-container-runtime-troubleshooting-planner.md) |
| `v0.28.0` | AOP can map Kubernetes node conditions to the right Linux host evidence plan | [`docs/releases/v0.28-kubernetes-node-linux-correlation.md`](docs/releases/v0.28-kubernetes-node-linux-correlation.md) |
| `v0.27.0` | AOP can correlate Linux disk, memory, CPU, network, boot, and service findings into one host-level SRE diagnosis | [`docs/releases/v0.27-linux-host-correlation.md`](docs/releases/v0.27-linux-host-correlation.md) |
| `v0.26.0` | AOP can diagnose Linux storage-layer risk across filesystems, block devices, LVM, multipath, NFS, and I/O latency | [`docs/releases/v0.26-linux-storage-lvm-nfs-investigation.md`](docs/releases/v0.26-linux-storage-lvm-nfs-investigation.md) |
| `v0.25.0` | AOP can diagnose boot, kernel, kdump, and grubby/default-kernel evidence safely | [`docs/releases/v0.25-linux-boot-kernel-investigation.md`](docs/releases/v0.25-linux-boot-kernel-investigation.md) |
| `v0.24.0` | AOP has short Linux expert shortcuts with safety guardrails | [`docs/releases/v0.24-linux-expert-shortcuts.md`](docs/releases/v0.24-linux-expert-shortcuts.md) |
| `v0.23.0` | AOP has short Kubernetes expert shortcuts for SRE muscle memory | [`docs/releases/v0.23-kubernetes-expert-shortcuts.md`](docs/releases/v0.23-kubernetes-expert-shortcuts.md) |
| `v0.22.0` | AOP can enrich real Kubernetes investigations with issue knowledge and Linux evidence guidance | [`docs/releases/v0.22-kubernetes-investigation-guidance.md`](docs/releases/v0.22-kubernetes-investigation-guidance.md) |
| `v0.21.0` | AOP has curated Kubernetes issue knowledge with source-aware troubleshooting guidance | [`docs/releases/v0.21-kubernetes-issue-knowledge.md`](docs/releases/v0.21-kubernetes-issue-knowledge.md) |
| `v0.20.0` | AOP can map Kubernetes symptoms to required Linux evidence without inventing host facts | [`docs/releases/v0.20-kubernetes-linux-correlation-training.md`](docs/releases/v0.20-kubernetes-linux-correlation-training.md) |
| `v0.19.0` | AOP has a visible Linux investigation ladder for future teammates, demos, and AI handoffs | [`docs/releases/v0.19-linux-investigation-ladder.md`](docs/releases/v0.19-linux-investigation-ladder.md) |
| `v0.18.0` | AOP can diagnose systemd service failure and restart-loop evidence safely | [`docs/releases/v0.18-linux-systemd-service-investigation.md`](docs/releases/v0.18-linux-systemd-service-investigation.md) |
| `v0.17.0` | AOP can diagnose Linux NIC, route, and resolver evidence deterministically | [`docs/releases/v0.17-linux-network-nic-investigation.md`](docs/releases/v0.17-linux-network-nic-investigation.md) |
| `v0.16.0` | AOP can separate Linux CPU saturation from high load, D-state, I/O wait, and steal time | [`docs/releases/v0.16-linux-cpu-load-dstate-investigation.md`](docs/releases/v0.16-linux-cpu-load-dstate-investigation.md) |
| `v0.15.0` | AOP has typed evidence, alert, metric, timeline, and dashboard contracts for future UI and integrations | [`docs/releases/v0.15-evidence-dashboard-contracts.md`](docs/releases/v0.15-evidence-dashboard-contracts.md) |
| `v0.14.2` | AOP can collect Linux NIC/interface-card evidence safely | [`docs/releases/v0.14.2-linux-nic-interface-evidence.md`](docs/releases/v0.14.2-linux-nic-interface-evidence.md) |
| `v0.14.1` | AOP can diagnose Linux memory pressure and OOM evidence deterministically | [`docs/releases/v0.14.1-linux-memory-oom-investigation.md`](docs/releases/v0.14.1-linux-memory-oom-investigation.md) |
| `v0.14.0` | AOP can expose complex senior Linux troubleshooting scenarios as read-only plans | [`docs/releases/v0.14-linux-complex-scenario-plans.md`](docs/releases/v0.14-linux-complex-scenario-plans.md) |
| `v0.13.0` | AOP can explain Linux command intent and plan disk investigations before execution | [`docs/releases/v0.13-linux-explain-and-plan.md`](docs/releases/v0.13-linux-explain-and-plan.md) |
| `v0.12.0` | AOP can classify Linux disk incidents deterministically and preserve memory | [`docs/releases/v0.12-linux-disk-incident-intelligence.md`](docs/releases/v0.12-linux-disk-incident-intelligence.md) |

### Implemented

- installable `aop` command
- `aop catalog` command for listing, searching, and safely running known
  troubleshooting catalog commands
- `aop runbooks` command for trusted runbook/RAG snippet retrieval
- native `aop linux` health and diagnostic commands
- bounded, shell-free Linux command execution with JSON output
- CPU, memory, disk, network, process, service, log, kernel, boot, and security
  evidence collection
- NIC/interface-card evidence through `aop linux nic`
- Linux scheduler, process-state, PSI, VM-counter, and cgroup evidence
- cgroup v1/v2 detection and cgroup v2 limits, events, and pressure
- timed VM, PSI, and cgroup counter deltas with active-event findings
- ordered disk/storage investigation with inode, mount, block-device, LVM,
  multipath, NFS, I/O latency, growth, deleted-file, and kernel-error evidence
- `aop investigate linux disk` deterministic diagnosis with severity,
  confidence, evidence gaps, next checks, command reasoning, and
  operational-memory persistence, including storage-layer findings for LVM,
  multipath, NFS, read-only device state, and I/O latency
- `aop investigate linux memory` deterministic diagnosis for OOM, swap,
  `MemAvailable`, and cgroup memory events
- `aop investigate linux cpu` deterministic diagnosis for high load, D-state,
  I/O wait, CPU saturation, and steal time
- `aop investigate linux network` deterministic diagnosis for NIC state,
  carrier, errors/drops, route, and resolver evidence
- `aop investigate linux service` deterministic diagnosis for systemd failed
  state, start-limit-hit, exit status, restart loops, and journal errors
- `aop investigate k8s-linux` correlation training for Kubernetes symptoms
  that require Linux node evidence
- `aop investigate k8s-node` node-condition planning for DiskPressure,
  MemoryPressure, PIDPressure, NetworkUnavailable, and Ready=False
- `aop investigate k8s-knowledge` curated Kubernetes issue knowledge from
  trusted source memory
- `aop investigate k8s` report enrichment with Kubernetes knowledge,
  Linux evidence guidance, and do-not-assume rules
- `aop kx` Kubernetes expert shortcuts for common troubleshooting symptoms
- `aop lx` Linux expert shortcuts for boot, kernel, grubby, storage, LVM,
  DNS, NFS, limits, SELinux, and runtime troubleshooting
- `aop investigate linux boot` deterministic diagnosis for boot, kernel,
  panic/oops, kdump, grubby/default-kernel, and boot-argument evidence
- `aop investigate linux host` host-level correlation across disk, memory,
  CPU, network, boot, and optional systemd service investigations
- `aop investigate linux runtime` container runtime planning for containerd,
  CRI-O, Docker, kubelet relation, image pulls, create failures, runtime disk,
  CNI, logs, PID pressure, and cgroups
- canonical enterprise investigation core with cases, evidence gaps,
  hypotheses, confidence scoring, reasoning summaries, decisions, audit events,
  and a Linux memory adapter
- Linux command explanation through `aop linux explain`
- read-only disk investigation planning through `aop linux plan disk`
- read-only complex Linux scenario plans through `aop linux plan scenario`
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
- provider-neutral evidence, alert, metric, timeline, and dashboard contracts
- provider-neutral LLM routing
- optional Kimi/Moonshot provider configuration
- deterministic AI token-budget and model-tier planning
- `aop ai budget` zero-cost estimation command
- deterministic incident fingerprints for recurring Kubernetes and Linux
  memory patterns
- `aop memory patterns` recurrence lookup
- pattern-aware Kubernetes investigation summary, JSON, and Markdown output
- bounded incident-pattern context in Kubernetes RCA prompts
- bounded runbook/RAG context in Kubernetes RCA prompts
- Linux investigation summary recurrence hints
- two hundred nineteen offline regression tests

### Not Yet Implemented

- general Linux cross-signal classification and AI RCA across all Linux
  domains
- AWS and CloudWatch troubleshooting
- operator web UI
- Slack or Microsoft Teams approval workflows
- FastAPI service layer
- authentication and RBAC
- automatic remediation execution
- multi-tenant company onboarding
- live-validated Kimi/Moonshot production rollout, scoring, cost controls, and
  fallback policy

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
aop kx oom
aop kx crash
aop kx image
aop lx boot
aop lx grub
aop lx storage
aop investigate linux boot
aop investigate k8s-knowledge --symptom CrashLoopBackOff
aop investigate k8s-linux --incident OOMKilled

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
aop linux explain "df -hT"
aop linux explain "netstat -plane | grep :3045"
aop linux plan disk --path /var
aop linux plan scenario --list
aop linux plan scenario high-load
aop linux plan scenario oom --json
aop linux cpu
aop investigate linux cpu
aop linux memory
aop linux nic
aop linux nic --iface ens5
aop investigate linux network --iface ens5
aop linux disk --path /var
aop investigate linux memory
aop investigate linux memory --pid 4242
aop linux space --path /var
aop linux fs --path /var
aop linux network
aop linux processes --top 20
aop linux services
aop investigate linux service --service nginx
aop investigate k8s-linux --list
aop investigate k8s-linux --incident OOMKilled
aop investigate k8s-linux --incident DiskPressure --format json
aop investigate k8s-knowledge --list
aop investigate k8s-knowledge --symptom CrashLoopBackOff
aop investigate k8s-knowledge --symptom DiskPressure --format json
aop kx list
aop kx oom
aop kx disk
aop kx node
aop lx list
aop lx boot
aop lx grub
aop lx storage
aop lx dns
aop investigate linux boot
aop investigate linux boot --recent-minutes 30 --format json
aop linux logs
aop linux kernel
aop linux boot
aop linux security
aop linux internals
aop linux internals --interval 5
aop linux cgroups --pid 1
aop linux cgroups --pid 1 --interval 5
aop linux all
```

Use JSON output for automation:

```bash
aop linux health --json
aop linux network --json
aop linux all --json > linux-report.json
```

The Linux CLI remains read-only and deterministic. It uses explicit command
arguments without shell evaluation, applies timeouts and output limits,
records missing commands and permission failures as evidence, explains command
intent before execution, and avoids restart, kill, delete, unmount, firewall,
and log-clearing actions.

The deeper Linux intelligence roadmap is documented in
[`docs/linux/LINUX_EXPERTISE_BLUEPRINT.md`](docs/linux/LINUX_EXPERTISE_BLUEPRINT.md).
The current Linux operator flow is documented in
[`docs/linux/LINUX_INVESTIGATION_LADDER.md`](docs/linux/LINUX_INVESTIGATION_LADDER.md).

Explain command intent before running deeper checks:

```bash
aop linux explain "df -hT"
aop linux explain "ps aux"
aop linux explain "lsof -p 4242"
aop linux explain "netstat -plane | grep :3045"
aop linux explain "strace -tt -T -f -y -yy -s 1024 -p 4242"
aop linux explain "df -hT" --json
```

The explain workflow is backed by the Linux argument reasoning catalog. It
does not execute the command. It returns the command purpose, argument meaning,
troubleshooting value, risk, incident fit, AOP guidance, and related next
commands.

Plan the investigation before collecting evidence:

```bash
aop linux plan disk --path /var
aop linux plan disk --path /company/app/logs
aop linux plan disk --path /var --json
aop linux plan scenario --list
aop linux plan scenario high-load
aop linux plan scenario oom --json
```

The disk plan is read-only and does not require the path to exist locally. It
shows the ordered Linux admin reasoning for capacity, inodes, mount identity,
bounded growth checks, deleted-open files, kernel storage errors, Kubernetes
node paths, and AWS/EBS follow-up.

Complex scenario plans expose senior Linux troubleshooting patterns before
collection starts. Current scenarios include high load with low CPU, memory
pressure and OOM, `df`/`du` mismatch, inode exhaustion, read-only filesystems,
file descriptor exhaustion, port conflicts, systemd restart loops, kernel
panic clues, LVM expansion mismatch, and container runtime disk pressure.

Disk-space investigation follows an evidence-first sequence:

```bash
aop linux disk --path /var
aop linux disk \
  --path /var/log \
  --top 20 \
  --recent-minutes 30 \
  --large-size-mb 500
```

Memory and OOM investigation follows the same evidence-first pattern:

```bash
aop investigate linux memory
aop investigate linux memory --pid 4242
aop investigate linux memory --pid 4242 --format json
```

The memory investigator classifies kernel OOM kills, cgroup OOM events, active
swap pressure, low `MemAvailable`, cgroup `memory.high` pressure, and
insufficient evidence. It remains read-only and does not kill processes, clear
cache, restart services, or change memory limits.

The `space` and `fs` aliases run the same workflow. AOP checks filesystem
capacity/type, inodes, mount context, bounded directory usage, recent large
files, deleted-open files, and recent kernel storage errors.

Turn that raw evidence into a deterministic incident diagnosis:

```bash
aop investigate linux disk --path /var
aop investigate linux disk --path /var --format json
aop investigate linux disk --path /var --no-persist
```

The investigation distinguishes byte exhaustion, inode exhaustion,
deleted-open files, rapid growth, read-only filesystems, kernel storage errors,
and insufficient evidence. It records confidence, evidence, next checks, why
those checks matter, and evidence gaps. Structured memory still persists when
semantic indexing is unavailable.

Linux internals commands read the kernel's virtual filesystems directly:

```bash
aop linux internals
aop linux internals --json
aop linux cgroups --pid 4242
aop linux cgroups --pid 4242 --json
```

`internals` covers load, task states, PSI, and selected VM counters.
`cgroups` maps a PID to its resource-control hierarchy and reports CPU,
memory, I/O, PID, event, and pressure evidence. Current counters are
point-in-time cumulative values. Adding `--interval` takes two snapshots,
calculates deltas and rates, and identifies activity that occurred during the
investigation.

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
aop memory patterns --min-count 2
aop memory patterns --domain linux.disk --format json
```

---

## Incident Workflow

```text
Linux Hosts       Kubernetes Clusters       AWS / Cloud Future
    |                    |                         |
    v                    v                         v
Read-Only Evidence   Runtime Evidence       Cloud Evidence
    |                    |                         |
    +----------+---------+-----------+-------------+
               |
               v
       Unified Evidence Model
               |
               v
 Deterministic Detection And Correlation
               |
               v
      Canonical InvestigationCase
               |
      +--------+--------+
      |                 |
      v                 v
Structured Memory   Semantic / RAG Memory
      |                 |
      +--------+--------+
               |
               v
     Token-Budget And Model Policy
               |
               v
     AI-Assisted RCA And Guidance
               |
               v
 CLI + UI + Slack/Teams + Ticket Systems
               |
               v
 Human Approval, Audit, Validation, Learning
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

### Memory-First Intelligence

AOP should learn from organizational history:

```text
current evidence
  + previous incidents
  + runbooks
  + semantic similarity
  + deterministic findings
  + AI reasoning
```

Historical similarity is a clue, not proof. AOP must still identify missing
evidence and contradictions.

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
│       ├── linux/                  # Linux evidence collection
│       ├── kubernetes/             # Kubernetes evidence and operations
│       ├── prometheus/             # metrics enrichment
│       └── troubleshooting/        # command catalogs and plans
├── docs/
│   ├── architecture/adr/           # architecture decisions
│   ├── releases/                   # human-readable release memory
│   ├── linux/                      # Linux expertise and preserved tshelper
│   ├── AOP_PRODUCT_VISION.md       # durable product direction
│   ├── AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md
│   ├── LINUX_CLI.md
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
| Optional LLM provider | Kimi/Moonshot through `LLM_PROVIDER=kimi` |
| AI token planning | Deterministic budget estimator and tier policy |
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
LLM_PROVIDER=ollama
LLM_MODEL_NAME=qwen2.5-coder:latest
MOONSHOT_API_KEY=
KIMI_MODEL_NAME=kimi-k2.6
KIMI_BASE_URL=https://api.moonshot.ai/v1
EMBEDDING_MODEL_NAME=nomic-embed-text
AI_LIGHT_MODEL_NAME=gpt-5-nano
AI_STANDARD_MODEL_NAME=gpt-5-mini
AI_DEEP_MODEL_NAME=gpt-5.1
AI_LIGHT_INPUT_TOKEN_BUDGET=3000
AI_STANDARD_INPUT_TOKEN_BUDGET=10000
AI_DEEP_INPUT_TOKEN_BUDGET=30000

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
aop ai budget --task classification --text "pod CrashLoopBackOff"
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

Additional safe simulation manifests for `CrashLoopBackOff`,
`CreateContainerConfigError`, and `FailedScheduling` are documented in
[`docs/incidents/kubernetes-simulation-catalog.md`](docs/incidents/kubernetes-simulation-catalog.md).

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
219 tests passing
```

The tests cover:

- CLI discovery and aliases
- Linux CLI discovery, JSON output, and prioritized health findings
- shell-free Linux command execution, timeout handling, and missing utilities
- NIC/interface-card command exposure, JSON output, evidence ordering, and
  unsafe interface-name rejection
- evidence/dashboard contract serialization, provider-neutral metrics, and
  evidence timeline ordering
- bounded Linux process output and diagnostic ordering
- `/proc` load, PSI, process-state, and VM-counter parsing
- cgroup v1/v2 detection and cgroup v2 limit/event interpretation
- timed counter deltas, stall percentages, reset handling, and cgroup identity
  validation
- disk evidence ordering, one-filesystem bounds, numeric sorting, CLI options,
  and aliases
- Linux disk incident classification, precedence, workflow orchestration,
  CLI output, and structured-memory fallback
- Linux memory incident classification, OOM and swap interpretation, cgroup
  memory-event handling, CLI output, workflow orchestration, and structured
  memory persistence
- Linux CPU/load incident classification, D-state and I/O-wait interpretation,
  steal-time handling, CLI output, workflow orchestration, and structured
  memory persistence
- Linux network/NIC incident classification, carrier and counter
  interpretation, route and resolver evidence, CLI output, workflow
  orchestration, and structured memory persistence
- Linux systemd service incident classification, start-limit and exit-status
  handling, journal evidence, CLI output, workflow orchestration, and
  structured memory persistence
- Kubernetes-to-Linux correlation catalog, issue aliases, JSON output, and
  safe Linux follow-up command planning
- Kubernetes issue knowledge catalog, source metadata, safe kubectl/AOP
  commands, do-not-assume rules, and JSON output
- Kubernetes investigation guidance in summary, JSON, and Markdown reports
- Kubernetes expert shortcut CLI behavior and JSON output
- Linux expert shortcut CLI behavior and JSON output
- Linux boot/kernel/grubby incident classification, workflow orchestration,
  CLI output, collector safety, and structured memory persistence
- Linux complex scenario catalog listing, alias lookup, human output, and JSON
  output
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
| [`docs/PROJECT_HANDOVER.md`](docs/PROJECT_HANDOVER.md) | Verified baseline, implementation boundaries, engineering rules, and next work |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Current release state and planned next direction |
| [`docs/AOP_PRODUCT_VISION.md`](docs/AOP_PRODUCT_VISION.md) | Linux, Kubernetes, AWS, UI, Slack/Teams, and onboarding vision |
| [`docs/architecture/enterprise-platform-evolution.md`](docs/architecture/enterprise-platform-evolution.md) | Restored enterprise platform evolution, architecture, and integration direction |
| [`docs/architecture/observability-dashboard-strategy.md`](docs/architecture/observability-dashboard-strategy.md) | Observability, dashboard, alert-signal, and future provider strategy |
| [`docs/roadmap/incident-pattern-intelligence.md`](docs/roadmap/incident-pattern-intelligence.md) | Incident fingerprinting, recurrence detection, and pattern-aware RCA roadmap |
| [`docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md`](docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md) | Compact current implementation memory |
| [`docs/releases/`](docs/releases/) | Human-readable release notes for future team members and AI handoffs |
| [`docs/KUBERNETES_CLI.md`](docs/KUBERNETES_CLI.md) | Kubernetes shortcut reference |
| [`docs/incidents/kubernetes-simulation-catalog.md`](docs/incidents/kubernetes-simulation-catalog.md) | Safe Kubernetes issue simulation catalog |
| [`docs/LINUX_CLI.md`](docs/LINUX_CLI.md) | Native Linux troubleshooting command reference |
| [`docs/linux/LINUX_EXPERTISE_BLUEPRINT.md`](docs/linux/LINUX_EXPERTISE_BLUEPRINT.md) | Linux administration expertise and implementation direction |
| [`docs/linux/LINUX_INVESTIGATION_LADDER.md`](docs/linux/LINUX_INVESTIGATION_LADDER.md) | Current Linux troubleshooting ladder and domain order |
| [`docs/linux/tshelper-original/`](docs/linux/tshelper-original/) | Preserved original `tshelper` source materials |
| [`linux_troubleshooting_command_catalog.md`](app/memory/knowledgebase/linux_troubleshooting_command_catalog.md) | Canonical Linux commands, arguments, interpretation, and safety memory |
| [`linux_complex_troubleshooting_scenarios.md`](app/memory/knowledgebase/linux_complex_troubleshooting_scenarios.md) | Complex Linux scenario memory for v0.14 planning |
| [`linux_expert_shortcuts_catalog.md`](app/memory/knowledgebase/linux_expert_shortcuts_catalog.md) | Linux expert shortcut memory and safety guardrails |
| [`kubernetes_linux_correlation_catalog.md`](app/memory/knowledgebase/kubernetes_linux_correlation_catalog.md) | Kubernetes symptom to Linux evidence training memory |
| [`kubernetes_issue_catalog.md`](app/memory/knowledgebase/kubernetes_issue_catalog.md) | Curated Kubernetes issue knowledge and source policy |
| [`docs/setup/installation.md`](docs/setup/installation.md) | Detailed local installation |
| [`docs/architecture/adr/`](docs/architecture/adr/) | Architecture decision records |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |

---

## Roadmap

The current detailed roadmap is maintained in [`docs/ROADMAP.md`](docs/ROADMAP.md).

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

- extend the v0.14 Linux complex troubleshooting catalog into deterministic
  investigations
- convert collected Linux evidence into normalized incident findings
- add cross-signal classification without replacing operator reasoning
- persist Linux incidents in structured and semantic operational memory
- add AI-assisted RCA grounded only in collected Linux evidence
- correlate Kubernetes node symptoms with relevant Linux evidence
- continue expanding command knowledge from real administration experience

Linux is a first-class product domain and a core source of project expertise.
The deterministic collection foundation already covers CPU, memory, process,
disk, filesystem, inode, network, service, kernel, boot, security, PSI, VM,
and cgroup evidence.

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
