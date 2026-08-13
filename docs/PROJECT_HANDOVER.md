# Autonomous Ops Platform: Project Handover

Updated: 2026-08-08

## Start Here

This is the shortest reliable entry point for a new developer or AI assistant.
Use current source code and tests as the truth for implemented behavior.

Read next:

1. `README.md` for the product overview and showcase commands.
2. `docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md` for compact implementation
   memory.
3. `docs/ROADMAP.md` for current release state and planned next releases.
4. `docs/AOP_PRODUCT_VISION.md` for the durable Linux, Kubernetes, AWS, UI,
   Slack/Teams, and company-onboarding direction.
5. `docs/architecture/observability-dashboard-strategy.md` before adding
   dashboards, graphing, alert processing, telemetry contracts, or LLM
   providers.
6. `docs/releases/` for release-by-release human context.
7. `docs/linux/LINUX_INVESTIGATION_LADDER.md` for the current Linux
   troubleshooting order.
8. `docs/LINUX_CLI.md` and
   `app/memory/knowledgebase/linux_troubleshooting_command_catalog.md` before
   extending Linux diagnostics.

Do not treat empty modules or directory names as implemented capabilities.

## Verified Baseline

```text
Release: 0.25.0
Branch: main
Remote: origin/main
Offline tests: 152 passing
CLI entry point: aop
Python: 3.11+
```

Verification:

```bash
source venv/bin/activate
aop --version
python -m unittest discover -s tests -q
git diff --check
git status --short --branch
```

Expected version:

```text
aop, version 0.25.0
```

## What AOP Is

AOP is intended to become one operational source of truth for SRE teams:

```text
Linux + Kubernetes + AWS + observability + runbooks + incident history
  -> normalized evidence
  -> deterministic findings
  -> operational memory
  -> AI-assisted reasoning
  -> human-approved safe action
  -> validation and learning
```

The founder's Linux administration experience is part of the product's core
knowledge. AOP must learn troubleshooting order and interpretation, not merely
execute a large list of commands.

## What Is Implemented

### Kubernetes

- `aop kb` and `aop k8s` read-only SRE shortcuts
- pod, node, namespace, deployment, service, event, log, and description
  evidence
- Kubernetes incident investigation with deterministic classification
- optional Prometheus enrichment
- Ollama RCA and remediation guidance
- JSON incident persistence, Chroma semantic memory, and exact-memory fallback
- Markdown and JSON reports
- provider-neutral evidence, alert, metric, timeline, and dashboard contracts

Primary showcase:

```bash
aop health
aop kb health
aop kb po
aop kb ev
aop kb inv -n ai-lab
```

### Linux

- native, read-only `aop linux` CLI
- CPU, memory, disk, network, process, service, log, kernel, boot, and security
  collectors
- NIC/interface-card evidence with link state, counters, carrier, speed,
  duplex, driver, firmware, and driver counters
- `/proc` scheduler, process-state, PSI, and VM-counter evidence
- cgroup v1/v2 detection and cgroup v2 CPU, memory, I/O, PID, event, and
  pressure evidence
- timed counter deltas for Linux internals and cgroups
- ordered disk investigation covering capacity, inodes, mount context,
  directory usage, recent large files, deleted-open files, and kernel storage
  errors
- command explanation through `aop linux explain`
- read-only disk investigation planning through `aop linux plan disk`
- read-only complex scenario plans through `aop linux plan scenario`
- human-readable and JSON output
- deterministic `aop investigate linux disk` classification
- disk severity, confidence, supporting evidence, evidence gaps, and safe next
  checks
- Linux-native disk incident memory with semantic-indexing fallback
- deterministic `aop investigate linux memory` classification for OOM, swap,
  `MemAvailable`, and cgroup memory events
- Linux-native memory incident persistence with semantic-indexing fallback
- deterministic `aop investigate linux cpu` classification for D-state, I/O
  wait, CPU saturation, high-load/low-CPU, and steal time
- Linux-native CPU incident persistence with semantic-indexing fallback
- deterministic `aop investigate linux network` classification for NIC state,
  carrier, errors/drops, routes, and resolver evidence
- Linux-native network incident persistence with semantic-indexing fallback
- deterministic `aop investigate linux service` classification for
  start-limit-hit, failed units, exit status, restart loops, and journal
  errors
- Linux-native service incident persistence with semantic-indexing fallback
- consolidated Linux investigation ladder in
  `docs/linux/LINUX_INVESTIGATION_LADDER.md`
- complex Linux scenario catalog exposed through v0.14 planning commands
- Kubernetes-to-Linux correlation training through
  `aop investigate k8s-linux`
- curated Kubernetes issue knowledge through
  `aop investigate k8s-knowledge`
- Kubernetes investigation reports enriched with issue knowledge and Linux
  evidence guidance
- short Kubernetes expert shortcuts through `aop kx`
- short Linux expert shortcuts through `aop lx`
- deterministic Linux boot/kernel/grubby investigation through
  `aop investigate linux boot`

Useful commands:

```bash
aop linux health
aop linux explain "df -hT"
aop investigate linux cpu
aop linux plan disk --path /var
aop linux plan scenario --list
aop linux plan scenario high-load
aop linux nic
aop linux nic --iface ens5
aop investigate linux network --iface ens5
aop investigate linux service --service nginx
aop investigate k8s-knowledge --symptom CrashLoopBackOff
aop investigate k8s-knowledge --symptom DiskPressure --format json
aop investigate k8s-linux --incident OOMKilled
aop investigate k8s-linux --incident DiskPressure --format json
aop kx oom
aop kx disk
aop kx node
aop lx boot
aop lx grub
aop lx storage
aop lx dns
aop investigate linux boot
aop linux disk --path /var
aop investigate linux memory
aop investigate linux memory --pid 4242
aop linux space --path /var
aop linux fs --path /var
aop linux internals --interval 5
aop linux cgroups --pid 1 --interval 5
aop linux all --json
aop investigate linux disk --path /var
```

The original authored `tshelper` materials remain preserved under
`docs/linux/tshelper-original/`. Do not rewrite or replace them.

## What Is Not Implemented

- general Linux cross-signal AI RCA across all Linux domains
- automatic Kubernetes-to-Linux live node evidence collection
- live Linux node evidence collection from Kubernetes incidents
- AWS and CloudWatch collectors
- Kimi/Moonshot provider runtime support
- operator web UI or FastAPI service
- Slack or Microsoft Teams notifications and approvals
- authentication, RBAC, tenant isolation, and company onboarding
- governed remediation execution
- production CI pipeline

Many directories are architectural placeholders. Confirm behavior through
imports, CLI registration, tests, and executable paths before claiming a
feature exists.

## Engineering Rules

- Evidence before AI.
- Deterministic interpretation before probabilistic reasoning.
- Never invent missing Linux, Kubernetes, AWS, or observability evidence.
- Keep collection read-only, bounded, shell-free, and explicit.
- Preserve typed Pydantic contracts between layers.
- Preserve provider abstraction around LLM integrations.
- Semantic-memory failure must fall back to exact structured memory.
- Do not hide programming defects behind fallback behavior.
- No consequential action without policy, audit, and human approval.
- Add tests with every behavioral change.

## Architecture Guidance

Do not add LangGraph merely because the project contains a placeholder for it.
The current linear workflow is understandable and sufficient for the proven
Kubernetes path. Introduce a graph orchestrator only when branching,
checkpointing, resumability, approval pauses, or multi-domain retries create a
real requirement.

RAG is partially present through structured incident history, embeddings,
Chroma, and hybrid retrieval. The next memory work should improve retrieval
quality, provenance, recurrence detection, and evaluation before adding more
frameworks.

Do not assume Grafana is the only dashboard or Prometheus is the only future
metrics source. AOP should own provider-neutral evidence and dashboard
contracts before building custom UI, graphing, alert triage, or multi-source
observability. See `docs/architecture/observability-dashboard-strategy.md`.

Kimi/Moonshot is a planned future reasoning provider only. Current implemented
LLM runtime is Ollama. Do not add Kimi environment variables or claim runtime
support until the provider, settings, health checks, tests, and docs exist.

## Recommended Next Sequence

1. Validate and record the live Kubernetes plus Prometheus showcase.
2. Add CI for tests, formatting, linting, and type checks.
3. Validate the Linux disk workflow against real ext4, XFS, LVM, container,
   NFS, and cloud-volume examples.
4. Extend Linux complex scenario plans into deterministic investigation
   workflows.
5. Consolidate v0.14-v0.18 into v0.19 release memory and demo guidance.
6. Add recurrence search across Linux incident memory.
8. Correlate Kubernetes node symptoms with collected Linux evidence.
9. Add the operator UI after Linux and Kubernetes share one stable incident
   contract.
10. Add Slack/Teams approval surfaces, then AWS evidence adapters.

For the next Linux disk phase, the workflow should distinguish:

```text
filesystem bytes exhausted
inode exhaustion
deleted-open files
rapid file growth
mount or read-only state
filesystem or storage I/O errors
insufficient evidence
```

It should explain why it selected a conclusion and recommend the next
read-only check when confidence is incomplete.

## Handover Prompt

Use this with a new ChatGPT or Codex conversation:

```text
Work in the autonomous-ops-platform repository.

First read docs/PROJECT_HANDOVER.md. Then read only the implementation and
tests relevant to the requested task. Treat current source and tests as truth.

Preserve evidence-first troubleshooting, deterministic findings, typed
contracts, exact-memory fallback, read-only collection, and human-approved
remediation.

Do not claim placeholder modules as implemented. Do not introduce LangGraph or
another framework unless the requested workflow requires branching,
checkpointing, resumability, or approval pauses.

Do not hardcode Grafana-only, Prometheus-only, or Ollama-only assumptions.
Kimi/Moonshot is planned but not implemented.

Explain the operational reasoning before making substantial Linux changes,
then implement, test, document, commit, and push the completed work.

Task:
<describe the next task>
```
