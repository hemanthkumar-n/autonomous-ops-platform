# Changelog

All notable changes to Autonomous Ops Platform will be documented here.

---

## v0.19.0 - Linux Investigation Ladder and Release Memory

Date: 2026-08-08

### Added

- `docs/linux/LINUX_INVESTIGATION_LADDER.md` as the human map for Linux
  troubleshooting inside AOP
- release note for v0.19 explaining the consolidation boundary and next
  correlation direction
- README, roadmap, handover, memory-lane, release-index, and installation
  updates for the v0.19 baseline

### Boundary

This release does not add a new collector or investigator. It consolidates the
Linux troubleshooting order so future Linux, Kubernetes, AWS, dashboard, and
AI work has a visible place in the product story.

---

## v0.18.0 - Linux systemd Service Investigation

Date: 2026-08-08

### Added

- `aop investigate linux service --service <unit>`
- deterministic service investigation using `systemctl status`,
  `systemctl show`, `systemctl cat`, and bounded `journalctl -u` evidence
- findings for start-limit-hit, failed units, non-zero exit status, restart
  policy loops, recent journal errors, and insufficient evidence
- Linux service incident persistence with semantic-memory fallback
- tests for service agent classification, workflow persistence, collection,
  and CLI output

### Safety

Service investigation is read-only. It does not restart, reload, enable,
disable, reset-failed, mask, unmask, edit, or kill service processes.

---

## v0.17.0 - Linux Network and NIC Investigation

Date: 2026-08-08

### Added

- `aop investigate linux network`
- optional `--iface <interface>` scope for NIC-aware network diagnosis
- deterministic findings for interface down, no carrier, interface error/drop
  pressure, missing default route, missing DNS resolver, speed/duplex evidence
  gaps, and insufficient evidence
- Linux network incident persistence with semantic-memory fallback
- tests for network agent classification, workflow persistence, collection,
  and CLI output

### Safety

Network investigation is read-only. It does not bring interfaces up or down,
change routes, alter MTU, modify offload settings, reset drivers, capture
packets, change DNS, or modify firewall state.

---

## v0.16.0 - Linux CPU, Load, and D-State Investigation

Date: 2026-08-08

### Added

- `aop investigate linux cpu`
- deterministic CPU/load investigation workflow
- classification for D-state blocked tasks, I/O pressure behind load, CPU
  saturation, steal-time pressure, high-load/low-CPU ambiguity, and
  insufficient evidence
- CPU/load incident persistence with semantic-memory fallback
- tests for CPU agent classification, workflow persistence, CLI output, and
  CPU evidence collection

### Safety

CPU investigation is read-only. It does not kill processes, change priorities,
restart services, tune kernel parameters, alter cgroup limits, or change cloud
instance capacity.

---

## v0.15.0 - Evidence and Dashboard Data Contracts

Date: 2026-08-08

### Added

- provider-neutral `MetricPoint` and `MetricSeries` contracts
- provider-neutral `AlertSignal` contract
- normalized `EvidenceItem` and `EvidenceTimeline` contracts
- `DashboardPanel` and `DashboardSnapshot` contracts for future UI, reports,
  and graphing
- tests proving timeline ordering, provider-neutral metrics, and dashboard
  snapshots combining metrics, alerts, and evidence

### Boundary

This release does not build the web UI or graph renderer. It creates the typed
contracts that Linux, Kubernetes, AWS, Prometheus, future CloudWatch, reports,
memory, and AI prompt builders can share.

---

## v0.14.2 - Linux NIC and Interface Evidence

Date: 2026-08-08

### Added

- `aop linux nic`
- `aop linux nic --iface <interface>`
- NIC/interface evidence collection from `ip`, `/sys/class/net`, and
  `ethtool`
- link inventory, interface addresses, packet counters, operational state,
  carrier, speed, duplex, link settings, driver/firmware, and driver counters
- interface-name validation before reading sysfs paths
- regression tests for command exposure, JSON output, evidence ordering, and
  unsafe interface rejection

### Safety

NIC evidence collection is read-only. It does not bring interfaces up or down,
change routes, alter MTU, modify offload settings, reset drivers, capture
packets, or change firewall state.

---

## v0.14.1 - Linux Memory and OOM Investigation

Date: 2026-08-08

### Added

- `aop investigate linux memory`
- optional `--pid` cgroup memory evidence for process-scoped investigation
- deterministic Linux memory diagnosis for kernel OOM kills, cgroup OOM
  events, active swap pressure, low `MemAvailable`, cgroup `memory.high`
  pressure, and insufficient evidence
- structured Linux memory incident persistence with semantic-memory fallback
- human-readable and JSON CLI output with `Next:` and `Why:` guidance
- regression tests for memory collection, agent classification, workflow
  persistence, and CLI output

### Safety

Memory investigation is read-only. It does not kill processes, clear cache,
restart services, change cgroup limits, tune sysctl values, or modify swap.

---

## v0.14.0 - Linux Complex Scenario Plans

Date: 2026-08-08

### Added

- `aop linux plan scenario --list`
- `aop linux plan scenario <scenario>`
- structured Linux complex troubleshooting scenario catalog
- human-readable and JSON output for symptoms, likely causes, first safe
  checks, interpretation, common traps, and cross-domain correlations
- aliases for common operator language such as `oom`, `fdisk`, `diskpressure`,
  `listener`, and `d-state`
- regression tests for scenario listing, rendering, alias lookup, JSON output,
  and unknown-scenario handling

### Safety

Scenario plans are read-only. They expose senior troubleshooting order and
interpretation, but they do not execute host commands or remediate systems.

---

## v0.13.0 - Linux Explain and Command Reasoning

Date: 2026-08-07

### Added

- `aop linux explain <command>`
- `aop linux plan disk --path <path>`
- command explanation lookup backed by the Linux argument reasoning catalog
- read-only disk investigation plan with ordered evidence steps,
  interpretations, Kubernetes correlation, and AWS/EBS correlation
- placeholder-aware matching for commands such as `lsof -p 4242` and
  `netstat -plane | grep :3045`
- human-readable and JSON output for command purpose, argument meaning,
  troubleshooting value, risk, incident fit, AOP guidance, and related next
  commands
- `aop investigate linux disk` finding output now includes why the recommended
  next diagnostic check matters
- regression tests for Linux explain CLI behavior

### Safety

`aop linux explain` and `aop linux plan` do not execute the requested
troubleshooting commands. They explain cataloged commands and planned evidence
steps so operators can understand why a command is useful before running it.

---

## v0.12.0 - Linux Disk Incident Intelligence

Date: 2026-06-10

### Added

- `aop investigate linux disk`
- typed disk investigation and finding contracts
- deterministic classification for capacity exhaustion, inode exhaustion,
  deleted-open files, rapid growth, read-only filesystems, storage errors, and
  insufficient evidence
- evidence-based severity, confidence, next checks, and evidence gaps
- Linux-native structured incident memory
- semantic indexing with structured-memory fallback
- regression tests for classification precedence, CLI behavior, orchestration,
  and persistence fallback

### Architecture

Raw collection remains available through `aop linux disk`. The investigation
command adds interpretation and memory without requiring an LLM. General Linux
AI RCA and Kubernetes-to-Linux live correlation remain future work.

---

## v0.11.0 - Ordered Disk Space Investigation

Date: 2026-06-10

### Added

- dedicated `aop linux disk` troubleshooting workflow
- `aop linux space` and `aop linux fs` shortcuts
- filesystem-targeted capacity, type, inode, source, and mount-option checks
- bounded and numerically sorted directory usage
- configurable recent large-file discovery
- deleted-open file evidence
- bounded kernel filesystem and storage-error evidence
- disk command help, manual guidance, and regression tests

### Safety

Disk collection remains on the filesystem backing the selected path and does
not delete, truncate, restart, unmount, repair, or resize anything.

---

## v0.10.0 - Timed Linux Pressure and Cgroup Sampling

Date: 2026-06-10

### Added

- `aop linux internals --interval <seconds>`
- `aop linux cgroups --pid <PID> --interval <seconds>`
- two-snapshot counter deltas and per-second rates
- measured PSI stall percentages from cumulative microsecond counters
- active OOM, swap, direct-reclaim, CPU-throttling, memory-high, and PID-limit
  findings
- before/after cgroup memory gauges
- counter-reset protection
- PID and cgroup-membership change protection

### Interpretation

Snapshot mode reports current gauges and cumulative history. Timed mode proves
which monotonic counters changed during the selected interval. Limits and
gauges are not incorrectly treated as event counters.

---

## v0.9.0 - Linux Internals and Cgroups

Date: 2026-06-10

### Added

- `aop linux internals`
- `aop linux cgroups --pid <PID>`
- typed Linux internals, PSI, finding, membership, and cgroup evidence models
- direct read-only parsing of `/proc` and `/sys/fs/cgroup`
- scheduler load and process-state correlation
- CPU, memory, and I/O pressure stall information
- selected VM reclaim, swap, major-fault, compaction, and OOM counters
- cgroup v1/hybrid detection
- cgroup v2 CPU, memory, I/O, PID, event, and pressure evidence
- deterministic findings for blocked tasks, pressure, throttling, OOM events,
  and PID-limit pressure
- fixture-based Linux virtual-filesystem tests

### Current Boundary

Counters in `/proc` and cgroup stat files are cumulative. This release
captures a safe point-in-time snapshot. Timed sampling and rate calculations
remain future work.

---

## v0.8.1 - Linux and Kubernetes AI Correlation Policy

Date: 2026-06-10

### Added

- founder-authored LinkedIn knowledge source for Linux and Kubernetes
  troubleshooting
- shared cross-domain AI prompt policy
- Kubernetes-to-Linux evidence-gap and correlation requirements
- prompt regression tests for RCA, combined analysis, and remediation

### Changed

- AI must distinguish confirmed evidence from hypotheses
- AI must identify missing Linux node evidence instead of inventing host facts
- AI recommends the next read-only `aop linux` diagnostic when node evidence is
  required but unavailable

---

## v0.8.0 - Native Linux SRE Commands

Date: 2026-06-10

### Added

- native `aop linux` command group
- `health`, `cpu`, `memory`, `disk`, `network`, `processes`, `services`,
  `logs`, `kernel`, `boot`, `security`, and `all` commands
- human-readable and JSON diagnostic output
- bounded shell-free command runner with timeouts
- normalized unavailable, permission, timeout, and command-error evidence
- deterministic load, available-memory, filesystem, and failed-service health
  findings
- preserved original `tshelper` sources with provenance and SHA-256 checksums
- Linux operational expertise blueprint
- Linux CLI and command-runner regression tests

### Safety

Linux commands are read-only. AOP does not restart services, kill processes,
delete files, modify firewalls, unmount filesystems, or clear logs.

### Current Boundary

This release establishes deterministic Linux evidence collection. Advanced
cross-signal correlation, incident memory, AI-assisted RCA, and remediation
guidance remain planned work.

---

## v0.7.0 — Kubernetes SRE Shortcuts

Date: 2026-06-09

### Added

- `aop kb` and `aop k8s` Kubernetes command groups
- health, node, namespace, deployment, service, pod, event, log, and pod
  description commands
- short aliases including `po`, `ev`, `log`, `desc`, `deploy`, and `svc`
- JSON output for inventory commands
- `aop kb inv` shortcut for full AI investigation
- Kubernetes CLI and normalization tests

### Safety

Kubernetes shortcut commands are read-only. Cluster mutation remains outside
the current CLI.

---

## v0.6.0 — Showcase CLI and Workflow Recovery

Date: 2026-06-09

### Added

- installable `aop` command
- `aop health`
- `aop investigate k8s`
- structured memory search command
- JSON and Markdown report output
- offline regression tests

### Fixed

- synchronous LLM provider contract
- Ollama model configuration
- remediation workflow import
- semantic indexing interface
- graceful semantic-memory fallback
- one primary classification per pod
- lazy Kubernetes client initialization

### Architecture Impact

The proven Kubernetes incident-intelligence path is now exposed as a
showcase-ready CLI while remaining advisory and non-destructive.

---

## v0.3.0 — Hardening Phase 2

Date: 2026-05-15

### Added

- centralized runtime settings
- structured logging framework
- Prometheus observability enrichment
- AI RCA resilience
- remediation resilience
- workflow orchestration hardening
- persistence safety

### Changed

- Prometheus metrics moved into incident context engine
- AI runtime config externalized
- Kubernetes signal collection hardened

### Architecture Impact

Prototype evolved into production-engineered platform foundation.
