# AOP Release Notes

This folder is the human-readable release memory for Autonomous Ops Platform.

Use it when a new contributor, ChatGPT conversation, or Codex session needs to
understand what changed, why it changed, how to demo it, and what remains
unfinished.

## Releases

| Release | Focus | Reference |
|---|---|---|
| `v0.28.0` | Kubernetes node to Linux correlation | [`v0.28-kubernetes-node-linux-correlation.md`](v0.28-kubernetes-node-linux-correlation.md) |
| `v0.27.0` | Linux host-level correlation | [`v0.27-linux-host-correlation.md`](v0.27-linux-host-correlation.md) |
| `v0.26.0` | Linux storage, LVM, multipath, and NFS investigation | [`v0.26-linux-storage-lvm-nfs-investigation.md`](v0.26-linux-storage-lvm-nfs-investigation.md) |
| `v0.25.0` | Linux boot, kernel, and grubby investigation | [`v0.25-linux-boot-kernel-investigation.md`](v0.25-linux-boot-kernel-investigation.md) |
| `v0.24.0` | Linux expert shortcuts | [`v0.24-linux-expert-shortcuts.md`](v0.24-linux-expert-shortcuts.md) |
| `v0.23.0` | Kubernetes expert shortcuts | [`v0.23-kubernetes-expert-shortcuts.md`](v0.23-kubernetes-expert-shortcuts.md) |
| `v0.22.0` | Kubernetes investigation guidance integration | [`v0.22-kubernetes-investigation-guidance.md`](v0.22-kubernetes-investigation-guidance.md) |
| `v0.21.0` | Kubernetes issue knowledge catalog | [`v0.21-kubernetes-issue-knowledge.md`](v0.21-kubernetes-issue-knowledge.md) |
| `v0.20.0` | Kubernetes to Linux correlation training | [`v0.20-kubernetes-linux-correlation-training.md`](v0.20-kubernetes-linux-correlation-training.md) |
| `v0.19.0` | Linux investigation ladder and release memory | [`v0.19-linux-investigation-ladder.md`](v0.19-linux-investigation-ladder.md) |
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
