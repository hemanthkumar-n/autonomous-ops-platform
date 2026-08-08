# AOP Release Notes

This folder is the human-readable release memory for Autonomous Ops Platform.

Use it when a new contributor, ChatGPT conversation, or Codex session needs to
understand what changed, why it changed, how to demo it, and what remains
unfinished.

## Releases

| Release | Focus | Reference |
|---|---|---|
| `v0.18.0` | Linux systemd service investigation | [`v0.18-linux-systemd-service-investigation.md`](v0.18-linux-systemd-service-investigation.md) |
| `v0.17.0` | Linux network and NIC investigation | [`v0.17-linux-network-nic-investigation.md`](v0.17-linux-network-nic-investigation.md) |
| `v0.16.0` | Linux CPU, load, and D-state investigation | [`v0.16-linux-cpu-load-dstate-investigation.md`](v0.16-linux-cpu-load-dstate-investigation.md) |
| `v0.15.0` | Evidence and dashboard data contracts | [`v0.15-evidence-dashboard-contracts.md`](v0.15-evidence-dashboard-contracts.md) |
| `v0.14.2` | Linux NIC and interface evidence | [`v0.14.2-linux-nic-interface-evidence.md`](v0.14.2-linux-nic-interface-evidence.md) |
| `v0.14.1` | Linux memory and OOM investigation | [`v0.14.1-linux-memory-oom-investigation.md`](v0.14.1-linux-memory-oom-investigation.md) |
| `v0.14.0` | Linux complex scenario planning | [`v0.14-linux-complex-scenario-plans.md`](v0.14-linux-complex-scenario-plans.md) |
| `v0.13.0` | Linux command explanation and disk investigation planning | [`v0.13-linux-explain-and-plan.md`](v0.13-linux-explain-and-plan.md) |
| `v0.12.0` | Deterministic Linux disk incident intelligence | [`v0.12-linux-disk-incident-intelligence.md`](v0.12-linux-disk-incident-intelligence.md) |

## How To Use These Notes

- Read `CHANGELOG.md` for the concise version history.
- Read these release notes for product intent, demo commands, important files,
  boundaries, and next steps.
- Read
  [`../architecture/observability-dashboard-strategy.md`](../architecture/observability-dashboard-strategy.md)
  before dashboard, graphing, alert-signal, telemetry, or provider-routing
  work.
- Treat source code and tests as final truth when older docs disagree.
- Keep future release notes practical enough for a new SRE or teammate to
  understand the workflow without needing the original chat history.
