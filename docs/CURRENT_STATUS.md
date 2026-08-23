# AOP Current Status

> Development branch: `feature/autonomous-investigation-collectors-v043`
>
> Development version: **v0.43.0**
>
> This document describes the active feature branch. `main` may remain on an earlier release until the dependent pull requests are merged.

## Current Direction

Autonomous Ops Platform is evolving from deterministic SRE troubleshooting into a bounded autonomous investigation runtime.

The operating principle remains:

```text
Evidence before AI
Safety before autonomy
Candidate RCA before confirmed RCA
Read-only investigation before remediation
```

## Investigation Architecture

```text
Incident / Symptom
      |
      v
InvestigationCase
      |
      v
Initial hypotheses + evidence gaps
      |
      v
Deterministic confidence evaluation
      |
      +-------------------------------+
      |                               |
      | evidence insufficient         | evidence sufficient
      v                               v
EvidencePlanner                  RCA candidate
      |                               |
      v                               v
Registered read-only collectors  validation / human confirmation
      |                               |
      v                               v
Normalized EvidenceItem(s)       confirmed root cause (future/controlled)
      |
      v
Resolve supported gaps
      |
      v
Update hypothesis support / why / why-not
      |
      v
Re-evaluate confidence
      |
      +----> repeat within step/request budgets
```

## v0.42 Foundation

The autonomous investigation foundation introduced:

- bounded evidence planning from unresolved evidence gaps
- blocking-gap prioritization
- registered read-only collector execution only
- maximum step and request budgets
- resource identity propagation across cluster, namespace, pod, node, host, container, and PID context
- explicit `RootCauseCandidate`
- separation between `rca_candidate` and confirmed `root_cause`
- deterministic `why` and `why_not` reasoning
- collector error auditing and safe stop conditions
- Linux memory collector integration using the existing deterministic workflow

The v0.42 Mac validation completed successfully with **243/243 tests passing** before the v0.43 collector expansion.

## v0.43 Multi-Collector Expansion

The active v0.43 branch extends the same contract to additional Linux domains:

| Collector | Existing workflow reused | Scope carried by planner | Autonomous behavior |
|---|---|---|---|
| `linux_memory` | Linux memory investigation | host/node/PID context | read-only evidence collection |
| `linux_cpu` | Linux CPU investigation | host/node context | read-only evidence collection |
| `linux_disk` | Linux disk investigation | host/node/path context | read-only evidence collection |
| `linux_network` | Linux network investigation | host/node/interface context | read-only evidence collection |

All collectors normalize deterministic workflow output into `EvidenceCollectionResult` and feed the same canonical `InvestigationCase`.

### Multi-collector behavior

A single investigation can now contain several evidence gaps:

```text
CPU gap ---------> linux_cpu -----+
Disk gap --------> linux_disk ----+--> normalized evidence
Network gap -----> linux_network -+          |
Memory gap ------> linux_memory --+          v
                                      one InvestigationCase
                                             |
                                             v
                                      confidence re-evaluation
```

The planner does not receive arbitrary shell access. It selects only registered collector names and bounded metadata.

## Safety Boundary

Current autonomous investigation deliberately does **not** include:

- arbitrary shell execution
- free-form command generation and execution
- automatic restart or kill actions
- filesystem cleanup or mutation
- route, firewall, or NIC mutation
- Kubernetes mutation
- automatic remediation execution
- automatic promotion of an RCA candidate to confirmed root cause

Existing Linux workflows remain the trusted execution boundary and autonomous collection uses `persist=False` to avoid unintended incident-memory side effects during evidence acquisition.

## Operational Intelligence Already Available

The broader AOP platform also includes:

- deterministic Linux disk, memory, CPU, network, boot/kernel, service, runtime, and host investigation
- Kubernetes health and incident evidence collection
- Kubernetes-to-Linux correlation guidance
- canonical enterprise investigation cases and audit timelines
- structured incident history and semantic memory
- exact + semantic hybrid retrieval with deterministic fallback
- incident fingerprinting and recurrence intelligence
- bounded runbook/RAG retrieval
- provenance-controlled external Kubernetes failure-story metadata
- source-reviewed operational guidance
- unified operational knowledge retrieval
- provider-neutral LLM routing with Ollama default and optional Kimi/Moonshot configuration
- deterministic AI token-budget/model-tier planning

## Validation

Focused v0.43 validation:

```bash
python -m unittest tests.test_autonomous_linux_collectors -v
python -m app.investigation.demo_multi_collector_loop
python -m app.investigation.demo_multi_collector_loop --format json
```

Full regression validation:

```bash
python -m unittest discover -s tests -v
```

The last confirmed full-suite baseline from v0.42 is **243 passing tests**. The v0.43 full-suite result must be recorded after the feature branch is run on the Mac; this document intentionally does not claim an unexecuted test result.

## Pull Request Chain

```text
main
  |
  +-- PR #2: v0.42 autonomous investigation loop
          |
          +-- PR #3: v0.43 multi-collector autonomous investigation
```

v0.43 is intentionally based on v0.42 until the v0.42 integration is completed. After v0.42 lands, PR #3 should be retargeted/reconciled against `main` and revalidated before merge.

## Next Engineering Milestone

After v0.43 validation, the next high-value expansion is **cross-platform evidence acquisition**, not remediation.

Priority order:

1. Kubernetes read-only collector adapter
2. Prometheus bounded metrics collector adapter
3. cross-domain hypothesis competition using Kubernetes + Linux + metrics evidence
4. structural incident fingerprints beyond exact recurrence
5. resolution/outcome learning from confirmed incidents

Target investigation shape:

```text
CrashLoopBackOff
      |
      v
Kubernetes evidence
      |
      +--> OOMKilled?
      |
      v
Identify node + workload limits
      |
      v
Linux memory evidence
      |
      v
Prometheus historical trend
      |
      v
Competing hypotheses
      |
      v
Confidence + why / why-not
      |
      v
RCA candidate or collect more evidence
```

## Definition of Progress

AOP autonomy should be measured by whether it can safely answer:

1. What do I know?
2. What do I not know?
3. Which evidence would discriminate between the current hypotheses?
4. Which registered read-only collector can obtain that evidence?
5. Did the new evidence increase or decrease confidence?
6. Is there enough evidence to stop?
7. What remains unconfirmed?

That investigation discipline is the core of AOP's autonomous SRE direction.
