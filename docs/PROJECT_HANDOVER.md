# Autonomous Ops Platform: Project Handover

Updated: 2026-06-10

## Start Here

This is the shortest reliable entry point for a new developer or AI assistant.
Use current source code and tests as the truth for implemented behavior.

Read next:

1. `README.md` for the product overview and showcase commands.
2. `docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md` for compact implementation
   memory.
3. `docs/AOP_PRODUCT_VISION.md` for the durable Linux, Kubernetes, AWS, UI,
   Slack/Teams, and company-onboarding direction.
4. `docs/LINUX_CLI.md` and
   `app/memory/knowledgebase/linux_troubleshooting_command_catalog.md` before
   extending Linux diagnostics.

Do not treat empty modules or directory names as implemented capabilities.

## Verified Baseline

```text
Release: 0.11.0
Branch: main
Remote: origin/main
Release code commit: eb2c4e7
Offline tests: 43 passing
CLI entry point: aop
Python: 3.11+
```

Verification:

```bash
source venv/bin/activate
aop --version
python -m unittest discover -s tests -q
git diff --check
git status --short --branch
```

Expected version:

```text
aop, version 0.11.0
```

## What AOP Is

AOP is intended to become one operational source of truth for SRE teams:

```text
Linux + Kubernetes + AWS + observability + runbooks + incident history
  -> normalized evidence
  -> deterministic findings
  -> operational memory
  -> AI-assisted reasoning
  -> human-approved safe action
  -> validation and learning
```

The founder's Linux administration experience is part of the product's core
knowledge. AOP must learn troubleshooting order and interpretation, not merely
execute a large list of commands.

## What Is Implemented

### Kubernetes

- `aop kb` and `aop k8s` read-only SRE shortcuts
- pod, node, namespace, deployment, service, event, log, and description
  evidence
- Kubernetes incident investigation with deterministic classification
- optional Prometheus enrichment
- Ollama RCA and remediation guidance
- JSON incident persistence, Chroma semantic memory, and exact-memory fallback
- Markdown and JSON reports

Primary showcase:

```bash
aop health
aop kb health
aop kb po
aop kb ev
aop kb inv -n ai-lab
```

### Linux

- native, read-only `aop linux` CLI
- CPU, memory, disk, network, process, service, log, kernel, boot, and security
  collectors
- `/proc` scheduler, process-state, PSI, and VM-counter evidence
- cgroup v1/v2 detection and cgroup v2 CPU, memory, I/O, PID, event, and
  pressure evidence
- timed counter deltas for Linux internals and cgroups
- ordered disk investigation covering capacity, inodes, mount context,
  directory usage, recent large files, deleted-open files, and kernel storage
  errors
- human-readable and JSON output

Useful commands:

```bash
aop linux health
aop linux disk --path /var
aop linux space --path /var
aop linux fs --path /var
aop linux internals --interval 5
aop linux cgroups --pid 1 --interval 5
aop linux all --json
```

The original authored `tshelper` materials remain preserved under
`docs/linux/tshelper-original/`. Do not rewrite or replace them.

## What Is Not Implemented

- Linux incident classification, cross-signal diagnosis, memory persistence,
  and AI RCA
- automatic Kubernetes-to-Linux live node evidence collection
- AWS and CloudWatch collectors
- operator web UI or FastAPI service
- Slack or Microsoft Teams notifications and approvals
- authentication, RBAC, tenant isolation, and company onboarding
- governed remediation execution
- production CI pipeline

Many directories are architectural placeholders. Confirm behavior through
imports, CLI registration, tests, and executable paths before claiming a
feature exists.

## Engineering Rules

- Evidence before AI.
- Deterministic interpretation before probabilistic reasoning.
- Never invent missing Linux, Kubernetes, AWS, or observability evidence.
- Keep collection read-only, bounded, shell-free, and explicit.
- Preserve typed Pydantic contracts between layers.
- Preserve provider abstraction around LLM integrations.
- Semantic-memory failure must fall back to exact structured memory.
- Do not hide programming defects behind fallback behavior.
- No consequential action without policy, audit, and human approval.
- Add tests with every behavioral change.

## Architecture Guidance

Do not add LangGraph merely because the project contains a placeholder for it.
The current linear workflow is understandable and sufficient for the proven
Kubernetes path. Introduce a graph orchestrator only when branching,
checkpointing, resumability, approval pauses, or multi-domain retries create a
real requirement.

RAG is partially present through structured incident history, embeddings,
Chroma, and hybrid retrieval. The next memory work should improve retrieval
quality, provenance, recurrence detection, and evaluation before adding more
frameworks.

## Recommended Next Sequence

1. Validate and record the live Kubernetes plus Prometheus showcase.
2. Add CI for tests, formatting, linting, and type checks.
3. Convert Linux collector output into normalized findings and incident
   contracts.
4. Build the first Linux reasoning workflow for one domain, starting with disk
   space because its evidence order is now implemented and tested.
5. Persist Linux investigations in the same operational-memory model.
6. Correlate Kubernetes node symptoms with collected Linux evidence.
7. Add the operator UI after Linux and Kubernetes share one stable incident
   contract.
8. Add Slack/Teams approval surfaces, then AWS evidence adapters.

For the next Linux disk phase, the workflow should distinguish:

```text
filesystem bytes exhausted
inode exhaustion
deleted-open files
rapid file growth
mount or read-only state
filesystem or storage I/O errors
insufficient evidence
```

It should explain why it selected a conclusion and recommend the next
read-only check when confidence is incomplete.

## Handover Prompt

Use this with a new ChatGPT or Codex conversation:

```text
Work in the autonomous-ops-platform repository.

First read docs/PROJECT_HANDOVER.md. Then read only the implementation and
tests relevant to the requested task. Treat current source and tests as truth.

Preserve evidence-first troubleshooting, deterministic findings, typed
contracts, exact-memory fallback, read-only collection, and human-approved
remediation.

Do not claim placeholder modules as implemented. Do not introduce LangGraph or
another framework unless the requested workflow requires branching,
checkpointing, resumability, or approval pauses.

Explain the operational reasoning before making substantial Linux changes,
then implement, test, document, commit, and push the completed work.

Task:
<describe the next task>
```
