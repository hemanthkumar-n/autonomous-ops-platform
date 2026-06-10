# Changelog

All notable changes to Autonomous Ops Platform will be documented here.

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
