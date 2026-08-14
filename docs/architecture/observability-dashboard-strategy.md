# Observability, Dashboard, and Provider Strategy

Updated: 2026-08-08

## Purpose

This document defines the early architecture direction for AOP observability,
dashboards, graphing, alert signals, and future AI provider expansion.

The goal is to avoid locking AOP into one visualization product, one metrics
backend, or one LLM provider before the platform grows across Linux,
Kubernetes, AWS, custom applications, Slack/Teams, and company-specific
workflows.

## Product Position

AOP should use Prometheus and Grafana where they are strong, but AOP should
not become only a Prometheus/Grafana wrapper.

Prometheus and Grafana answer many monitoring and dashboard questions. AOP's
role is broader:

```text
raw operational signals
  -> normalized evidence
  -> deterministic findings
  -> incident context
  -> explainable investigation
  -> AI-assisted reasoning
  -> operational memory
  -> UI, CLI, chat, reports, and approval workflows
```

## Vocabulary

### Monitoring

Monitoring watches known conditions.

Examples:

- CPU usage exceeds a threshold.
- Disk usage crosses 90%.
- A pod restarts more than expected.
- A Kubernetes node becomes `NotReady`.

Monitoring answers:

```text
Is a known signal healthy or unhealthy?
```

### Observability

Observability helps operators understand unknown or complex behavior from
system signals.

Signals include:

- metrics
- logs
- traces
- events
- topology
- deployment metadata
- host and runtime evidence

Observability answers:

```text
Why is this happening?
Where is the cause?
What changed?
Which signals correlate?
```

### Reliability

Reliability is whether the service works correctly over time.

It is measured through availability, latency, error rate, durability, SLOs,
MTTR, and recurrence.

### Resilience

Resilience is how well the system absorbs failure and recovers without
cascading impact.

Examples include pod rescheduling, retries with backoff, circuit breakers,
replication, failover, and graceful degradation.

### Autoscaling

Autoscaling changes capacity based on demand or pressure.

Examples include Kubernetes HPA/VPA, Cluster Autoscaler, Karpenter, and AWS
Auto Scaling Groups.

Autoscaling should be guided by reliable evidence, not only by a single raw
metric.

## Recommended Tool Direction

| Layer | Preferred direction | Reason |
|---|---|---|
| Telemetry standard | OpenTelemetry | Common model for metrics, logs, traces, resources, and context |
| Metrics source | Prometheus | Strong Kubernetes/SRE fit and current AOP integration |
| External dashboards | Grafana as code | Useful for teams already using Grafana and GitOps-style dashboards |
| AOP internal dashboard | AOP-owned data contracts and UI | Keeps AOP intelligence independent from Grafana panels |
| Frontend graphing | ECharts or equivalent chart library | Flexible custom incident timelines, graphs, and operational panels |
| Local analytics | DuckDB later | Useful for local investigation over JSON, CSV, and Parquet evidence |
| High-scale analytics | Evaluate later | ClickHouse, Timescale, Mimir, VictoriaMetrics, or similar only when scale requires |
| LLM provider expansion | Kimi/Moonshot selectable, not live-validated | Future reasoning provider behind the existing provider abstraction |

## AOP Data Model Direction

AOP should normalize observability inputs into its own typed model before
displaying, storing, or sending them to AI.

Future contracts should include concepts such as:

```text
MetricPoint
MetricSeries
LogEvent
TraceSpan
AlertSignal
EvidenceItem
EvidenceTimeline
IncidentFinding
DashboardPanel
DashboardSnapshot
```

This gives AOP one internal representation that can power:

- CLI output
- AOP web UI
- Grafana export
- Markdown and JSON reports
- Slack/Teams cards
- AI prompt context
- incident memory
- recurrence detection
- alert triage

## Dashboard Strategy

### Grafana

Grafana should remain a supported external visualization path.

Use it for:

- existing SRE dashboards
- Prometheus metrics exploration
- team dashboards already managed by platform teams
- dashboard-as-code where useful

Avoid making Grafana the only dashboard experience. Grafana panels do not
replace AOP incident memory, evidence timelines, command explanations,
approval state, or RCA reasoning.

### AOP Dashboard

AOP should eventually provide its own UI for:

- active incidents
- Linux and Kubernetes evidence timelines
- deterministic findings
- AI RCA and remediation guidance
- command explanations
- similar incident memory
- reliability and recurrence summaries
- approval workflow state
- AWS and cloud context

The AOP dashboard should show why a conclusion was reached, not only a chart.

### Graphing

Custom AOP graphs should be generated from normalized evidence and dashboard
contracts rather than direct backend-specific query responses.

This allows the same finding to be visualized from:

- Prometheus metrics
- CloudWatch metrics
- Linux collector samples
- Kubernetes events
- future OpenTelemetry signals
- stored incident memory

## Alert Strategy

AOP should treat alerts as signals, not final answers.

Example:

```text
Alert: node disk usage above 90%
  -> collect filesystem bytes and inodes
  -> inspect mount state
  -> inspect growth
  -> inspect deleted-open files
  -> inspect kernel storage errors
  -> correlate Kubernetes DiskPressure
  -> correlate AWS/EBS metrics if cloud context exists
  -> produce finding and next safe step
```

Alerts should become `AlertSignal` records that are correlated with evidence,
findings, historical incidents, and service impact.

## AI Provider Strategy

Current implemented provider:

```text
Ollama
```

Current default reasoning model:

```text
qwen2.5-coder:latest
```

Optional provider direction:

```text
Kimi / Moonshot
```

Kimi should be documented as selectable provider support only until live
validation, cost controls, scoring, fallback policy, and model-call
observability are implemented. Do not commit `.env` secrets.

The correct future implementation path is:

```text
app/llm/providers/kimi_provider.py
  -> provider contract tests
  -> provider selection setting
  -> health check
  -> timeout/retry handling
  -> model governance
  -> docs and .env.example update
```

The existing provider abstraction should prevent agent rewrites when Kimi or
other providers are added.

## What Not To Hardcode Now

Do not hardcode these assumptions:

- Grafana is the only dashboard.
- Prometheus is the only metrics source.
- Metrics alone explain an incident.
- Monitoring and observability are the same thing.
- Alerts are root cause.
- Ollama is the only future LLM provider.
- AOP UI charts should directly depend on Prometheus response shapes.
- AI should reason from chart visuals instead of normalized evidence.

## Recommended Next Architecture Step

After the v0.14 Linux complex troubleshooting catalog, the next
code-oriented dashboard foundation should be:

```text
v0.15: Evidence and Dashboard Data Contracts
```

Suggested first contracts:

```text
MetricPoint
MetricSeries
AlertSignal
EvidenceItem
EvidenceTimeline
DashboardPanel
DashboardSnapshot
```

These contracts should be provider-neutral and usable by CLI, UI, memory,
reports, future APIs, and AI prompt builders.
