# AOP Roadmap

Updated: 2026-08-08

This roadmap is the public project direction for future contributors, ChatGPT
handoffs, and Codex sessions. It separates implemented work from planned work
so the project remains honest and easy to explain.

## Current Baseline

```text
Current release: v0.36.0
Status: implemented and pushed
```

v0.36.0 adds bounded pattern context to RCA prompts and Linux summaries:

```text
exact recurrence
  -> bounded pattern summary
  -> RCA prompt context
  -> Linux CLI recurrence hints
```

v0.35.0 wires pattern intelligence into Kubernetes investigation output:

```text
current incident
  -> exact historical pattern lookup
  -> pattern_guidance
  -> summary / JSON / Markdown output
```

v0.34.0 adds the first Incident Pattern Intelligence implementation:

```text
structured memory
  -> deterministic fingerprint
  -> grouped occurrences
  -> recurring pattern report
```

v0.33.0 restores the enterprise platform narrative:

```text
Reactive Operations
  -> AI-Assisted Incident Response
  -> Operational Learning Platform
  -> Autonomous Operational Intelligence
  -> Safe Self-Healing Platform Engineering
```

It also adds the Incident Pattern Intelligence roadmap:

```text
fingerprints
  -> recurrence detection
  -> similarity clustering
  -> pattern-aware RCA
  -> trend visibility
```

v0.32.0 adds AI token-budget and model-tier planning:

```text
evidence text
  -> deterministic token estimate
  -> light / standard / deep / local tier
  -> visible budget decision
```

v0.31.0 adds provider-neutral LLM routing:

```text
LLMClient
  -> LLMRouter
  -> ollama by default
  -> kimi / moonshot when explicitly configured
```

v0.30.0 added the enterprise investigation core:

```text
domain investigation
  -> canonical InvestigationCase
  -> evidence gaps and hypotheses
  -> deterministic confidence and why / why-not reasoning
  -> RCA candidate or collect-more-evidence decision
  -> audit trail
```

Implemented commands:

```bash
aop linux explain "df -hT"
aop linux plan disk --path /var
aop linux plan scenario --list
aop linux plan scenario high-load
aop linux disk --path /var
aop investigate linux disk --path /var
aop investigate linux memory
aop investigate linux memory --pid 4242
aop linux nic
aop linux nic --iface ens5
aop investigate linux cpu
aop investigate linux network --iface ens5
aop investigate linux service --service nginx
aop investigate k8s-knowledge --symptom CrashLoopBackOff
aop investigate k8s-knowledge --symptom DiskPressure --format json
aop investigate k8s-linux --incident OOMKilled
aop investigate k8s-linux --incident DiskPressure --format json
aop investigate k8s -n ai-lab
aop kx oom
aop kx disk
aop kx node
aop lx boot
aop lx kernel
aop lx grub
aop lx storage
aop lx dns
aop investigate linux boot
aop investigate linux host
aop investigate k8s-node --node worker-01 --condition DiskPressure
aop investigate linux runtime --runtime containerd --symptom image-pull
```

The human-readable Linux ladder is maintained in
`docs/linux/LINUX_INVESTIGATION_LADDER.md`.

## Completed Linux And Data Foundation

v0.30 added the canonical enterprise investigation case model, confidence
engine, reasoning summaries, audit events, and Linux memory adapter.
v0.29 added container runtime troubleshooting planning for containerd, CRI-O,
Docker, kubelet relation, image pulls, runtime storage, CNI, logs, PID
pressure, and cgroups.
v0.28 added Kubernetes node-to-Linux correlation planning for DiskPressure,
MemoryPressure, PIDPressure, NetworkUnavailable, and Ready=False.
v0.27 added host-level correlation across existing Linux domain
investigations.
v0.26 deepened deterministic Linux disk investigation with block-device, LVM,
multipath, NFS, and I/O latency evidence.
v0.25 added deterministic Linux boot, kernel, kdump, grubby/default-kernel,
and boot-argument investigation.
v0.24 added short Linux expert shortcuts for boot, kernel, grubby, storage,
LVM, DNS, NFS, limits, SELinux, and container runtime troubleshooting.
v0.23 added short Kubernetes expert shortcuts for common SRE troubleshooting
symptoms while reusing the v0.20/v0.21 knowledge and correlation catalogs.
v0.22 integrated Kubernetes issue knowledge and Kubernetes-to-Linux
correlation guidance into the main Kubernetes investigation summary, JSON, and
Markdown reports.
v0.21 added curated Kubernetes issue knowledge for pod failures, scheduling
failures, and node conditions, backed by source-controlled memory and official
Kubernetes documentation links.
v0.20 added explicit Kubernetes-to-Linux symptom correlation training for
OOMKilled, CrashLoopBackOff, image pull failures, config/startup failures,
scheduling failures, DiskPressure, MemoryPressure, and NodeNotReady.
v0.19 documented the current Linux troubleshooting ladder for future
contributors, demos, and AI handoffs.
v0.18 added deterministic Linux systemd service failure and restart-loop
investigation.
v0.17 added deterministic Linux NIC, route, and resolver investigation.
v0.16 added deterministic Linux CPU, load, D-state, I/O-wait, and steal-time
investigation.
v0.15 added typed `MetricPoint`, `MetricSeries`, `AlertSignal`,
`EvidenceItem`, `EvidenceTimeline`, `DashboardPanel`, and `DashboardSnapshot`
contracts.
v0.14.2 added Linux NIC/interface-card evidence.
v0.14.1 added deterministic Linux memory and OOM investigation.
v0.14.0 exposed complex Linux troubleshooting scenarios through the CLI.
v0.13 completed the Linux disk reasoning loop:

```text
explain command
  -> plan disk investigation
  -> collect disk evidence
  -> diagnose deterministic disk findings
  -> explain why the next check matters
```

Implemented scenario plans include high load with low CPU, `D` state, OOM,
file descriptor exhaustion, port conflicts, systemd restart loops, kernel
panic clues, `df`/`du` mismatch, inode exhaustion, deleted-open files,
read-only remounts, LVM expansion mismatch, container runtime disk pressure,
and Kubernetes symptoms that require Linux node correlation.

## Next: v0.37

Purpose:

```text
Build the first runbook/RAG retrieval foundation.
```

Target outcomes:

- source-controlled runbook chunk model
- runbook retrieval by incident type and domain
- bounded runbook context for future RCA prompts
- preserve token-budget policy before model calls
- avoid dumping full runbooks into prompts
- no automatic remediation
- runbook match treated as guidance, not proof

Reference:

```text
docs/roadmap/incident-pattern-intelligence.md
```

## Strategic Phases

### Phase 5: Incident Pattern Intelligence

- incident fingerprints
- recurrence tracking
- incident clustering
- pattern-aware RCA
- trend awareness

### Phase 6: Agentic Orchestration

- planner agents
- execution-preparation agents
- approval waits
- guarded retries
- LangGraph, AutoGen, or similar only when branching/resumability requires it

### Phase 7: Shared Organizational Intelligence

- runbook intelligence
- multi-agent memory
- team/service ownership context
- previous fix outcome learning
- ticket and chat history as governed context

### Phase 8: Enterprise Platform Evolution

- FastAPI service layer
- operator UI
- authentication and RBAC
- audit workflows
- approval systems
- multi-tenant/company onboarding
- portable enterprise deployment

## Later Roadmap

### Operator UI

- active Linux and Kubernetes incidents
- evidence timeline
- deterministic findings
- AI RCA and remediation guidance
- command explanations
- historical similar incidents
- approval state

### AWS Operational Intelligence

- CloudWatch metrics and logs
- EC2, EBS, ELB/ALB, RDS, Lambda, EKS, IAM, VPC, Route 53, and S3
- CloudTrail change correlation
- AWS Health context

### Slack and Microsoft Teams

- incident notifications
- approve, reject, defer, and escalate actions
- execution and validation updates
- audit trail back to the canonical AOP incident record

### Kimi / Moonshot Provider

Kimi/Moonshot provider routing is implemented behind explicit configuration.
Ollama remains the default and validated local runtime. Next provider work is
live validation, provider scoring, cost controls, fallback policy, and
observability around model calls.

## Roadmap Rules

- Evidence before AI.
- Linux expertise is a product differentiator.
- Do not claim planned capabilities as implemented.
- Do not hardcode Grafana-only, Prometheus-only, or Ollama-only assumptions.
- New domains should use typed contracts and adapters.
- Consequential action requires human approval, audit, and policy controls.
