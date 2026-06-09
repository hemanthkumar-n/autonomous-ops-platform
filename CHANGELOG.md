# Changelog

All notable changes to Autonomous Ops Platform will be documented here.

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
