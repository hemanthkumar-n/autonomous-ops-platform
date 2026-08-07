# AOP Roadmap

Updated: 2026-08-08

This roadmap is the public project direction for future contributors, ChatGPT
handoffs, and Codex sessions. It separates implemented work from planned work
so the project remains honest and easy to explain.

## Current Baseline

```text
Current release: v0.13.0
Status: implemented and pushed
```

v0.13 completed the Linux disk reasoning loop:

```text
explain command
  -> plan disk investigation
  -> collect disk evidence
  -> diagnose deterministic disk findings
  -> explain why the next check matters
```

Implemented commands:

```bash
aop linux explain "df -hT"
aop linux plan disk --path /var
aop linux disk --path /var
aop investigate linux disk --path /var
```

## Next Release: v0.14

```text
v0.14: Linux Complex Troubleshooting Catalog
```

Purpose:

```text
Capture senior Linux troubleshooting scenarios as structured AOP memory before
turning them into more automated investigation workflows.
```

This keeps AOP aligned with the founder's Linux administration strength. The
goal is not to dump commands into a file. The goal is to preserve the
diagnostic order, interpretation, traps, and next safe checks behind complex
Linux incidents.

Target scenarios:

- high load with low CPU usage
- `D` state and blocked tasks
- memory pressure and OOM killer evidence
- swap storms
- file descriptor exhaustion
- port conflicts and missing listeners
- DNS and route failures
- systemd restart loops
- kernel panic and previous-boot evidence
- `df` and `du` mismatch
- inode exhaustion
- deleted-open files
- read-only filesystem remounts
- NFS stale mounts
- LVM, partition, and filesystem expansion mismatch
- container runtime disk pressure
- Kubernetes symptoms that require Linux node correlation

Cgroups are part of this Linux internals context, especially for containers
and Kubernetes workloads, but they are not the standalone v0.14 headline.

## Then: v0.15

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
