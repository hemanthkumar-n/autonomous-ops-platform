# AOP Roadmap

Updated: 2026-08-08

This roadmap is the public project direction for future contributors, ChatGPT
handoffs, and Codex sessions. It separates implemented work from planned work
so the project remains honest and easy to explain.

## Current Baseline

```text
Current release: v0.27.0
Status: implemented and pushed
```

v0.27.0 adds host-level Linux correlation:

```text
aop investigate linux host
  -> run disk, memory, CPU, network, boot, and optional service investigations
  -> rank the most urgent host diagnosis by severity and confidence
  -> persist one Linux host memory record
  -> stay read-only
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
```

The human-readable Linux ladder is maintained in
`docs/linux/LINUX_INVESTIGATION_LADDER.md`.

## Completed Linux And Data Foundation

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

## Next: v0.28

Purpose:

```text
Connect Linux host correlation to Kubernetes node troubleshooting.
```

Target outcomes:

- Kubernetes node-pressure host correlation
- kubelet and container runtime service checks
- `/var/lib/kubelet` and `/var/lib/containerd` storage guidance
- CNI/network hints from Linux NIC and route evidence
- no automatic remediation
- cloud volume follow-up guidance without mutating storage
- keep AI RCA grounded in deterministic evidence and explicit gaps

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

Kimi/Moonshot is a planned future reasoning provider. Current implemented LLM
runtime is Ollama. Do not claim Kimi support until provider code, settings,
health checks, tests, and docs exist.

## Roadmap Rules

- Evidence before AI.
- Linux expertise is a product differentiator.
- Do not claim planned capabilities as implemented.
- Do not hardcode Grafana-only, Prometheus-only, or Ollama-only assumptions.
- New domains should use typed contracts and adapters.
- Consequential action requires human approval, audit, and policy controls.
