# AOP Roadmap

Updated: 2026-08-08

This roadmap is the public project direction for future contributors, ChatGPT
handoffs, and Codex sessions. It separates implemented work from planned work
so the project remains honest and easy to explain.

## Current Baseline

```text
Current release: v0.16.0
Status: implemented and pushed
```

v0.16.0 adds deterministic Linux CPU, load, and D-state investigation:

```text
collect CPU and scheduler evidence
  -> separate CPU saturation from D-state, I/O wait, and steal
  -> explain the next safe check
  -> persist structured Linux CPU incident records
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
```

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

## Current Linux Expansion: v0.14

```text
v0.14: Linux Complex Troubleshooting Catalog and Scenario Plans
```

This keeps AOP aligned with the founder's Linux administration strength. The
goal is not to dump commands into a file. The goal is to preserve the
diagnostic order, interpretation, traps, and next safe checks behind complex
Linux incidents.

Implemented scenario plans:

- high load with low CPU usage
- `D` state and blocked tasks
- memory pressure and OOM killer evidence
- file descriptor exhaustion
- port conflicts and missing listeners
- systemd restart loops
- kernel panic and previous-boot evidence
- `df` and `du` mismatch
- inode exhaustion
- deleted-open files
- read-only filesystem remounts
- LVM, partition, and filesystem expansion mismatch
- container runtime disk pressure
- Kubernetes symptoms that require Linux node correlation

Cgroups are part of this Linux internals context, especially for containers
and Kubernetes workloads, but they are not the standalone v0.14 headline.

Implemented raw evidence workflows:

- NIC/interface state, counters, carrier, speed, duplex, driver, firmware, and
  driver counters

Still pending inside the larger Linux expansion:

- DNS and route failure scenario plans
- NFS stale mount scenario plans
- deterministic investigation workflows for CPU/load, network/DNS, services,
  boot, and kernel failures
- Linux AI RCA grounded only in collected Linux evidence

## Current Data Contract Foundation: v0.15

```text
v0.15: Evidence and Dashboard Data Contracts
```

Purpose:

```text
Create provider-neutral typed contracts before building custom dashboards,
graphs, alert processing, or UI features.
```

Target contracts:

- `MetricPoint`
- `MetricSeries`
- `AlertSignal`
- `EvidenceItem`
- `EvidenceTimeline`
- `DashboardPanel`
- `DashboardSnapshot`

These should work with Prometheus, Linux collectors, Kubernetes evidence,
CloudWatch later, OpenTelemetry later, reports, UI, Slack/Teams, and AI
prompt context.

Status: implemented as typed Pydantic contracts in `app/schemas/evidence.py`.

## Next: v0.17

```text
v0.17: Linux Network and NIC Investigation
```

Purpose:

```text
Turn NIC and network evidence into deterministic network investigation.
```

Target findings:

- link down
- no carrier
- RX/TX error or drop pressure
- speed or duplex mismatch
- route evidence gaps
- DNS evidence gaps
- listener evidence gaps
- insufficient evidence

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
