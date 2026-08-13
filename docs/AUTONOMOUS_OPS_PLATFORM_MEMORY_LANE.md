# Autonomous Ops Platform: Codex Memory

Updated: 2026-08-08

## Purpose

AOP is an AI-native operational intelligence runtime for SRE and platform
engineering. Kubernetes incident intelligence and the first deterministic
Linux troubleshooting CLI are implemented. AWS, Terraform, UI, collaboration,
and autonomous execution remain future domains.

Long-term product direction is preserved in:

```text
docs/AOP_PRODUCT_VISION.md
docs/ROADMAP.md
docs/linux/LINUX_INVESTIGATION_LADDER.md
```

Read that file for roadmap, product, Linux, AWS, UI, Slack/Teams, company
onboarding, or platform-positioning work. It is the durable vision source.

Human-readable release notes are preserved in:

```text
docs/releases/
```

Use those files when handing the project to a future teammate, ChatGPT
conversation, or Codex session.

Observability, dashboard, alert-signal, and future provider strategy:

```text
docs/architecture/observability-dashboard-strategy.md
```

Use that file before building dashboards, graphs, telemetry contracts, alert
processing, or Kimi/Moonshot support.

The previous detailed 555-line memory remains recoverable from Git:

```bash
git show 526bdbc:docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md
```

Core loop:

```text
collect evidence -> classify -> recall history -> reason -> recommend -> persist
```

Remediation is advisory and non-destructive.

## Current Baseline

- Version: `0.24.0`
- Branch: `main`
- Remote baseline: `origin/main`
- Python: `3.11+`
- CLI entry point: `aop`
- Tests: one hundred forty-three offline regression tests passing
- Real Ollama generation and 768-dimensional embeddings verified
- Full live demo still requires Kubernetes and Prometheus to be running

## Implemented Runtime

```text
Kubernetes pods
  -> context collection: state, termination, resources, logs, events
  -> optional Prometheus enrichment
  -> deterministic primary classification per pod
  -> exact + semantic incident-memory retrieval
  -> Ollama RCA
  -> safe remediation guidance
  -> JSON incident memory + Chroma indexing
```

Semantic-memory failure degrades to exact structured memory. Missing memory
does not block analysis from current evidence.

Linux CLI:

```text
host health
  -> bounded read-only command collection
  -> CPU, memory, disk, network, process, service, log, kernel, boot, security
  -> scheduler/load, task states, PSI, VM counters, and cgroup evidence
  -> optional timed counter deltas and measured pressure
  -> ordered disk-space and inode investigation
  -> NIC/interface state, carrier, speed, duplex, driver, and counters
  -> normalized unavailable, permission, timeout, and error evidence
  -> human-readable or JSON output
```

Linux disk intelligence:

```text
ordered disk evidence
  -> deterministic parsing and classification
  -> primary diagnosis, severity, confidence, and evidence gaps
  -> safe next diagnostic action
  -> Linux-native JSON memory
  -> optional semantic indexing with structured fallback
```

Linux memory intelligence:

```text
ordered memory evidence
  -> deterministic parsing and classification
  -> OOM, active swap, low MemAvailable, cgroup OOM, and memory.high findings
  -> safe next diagnostic action
  -> Linux-native JSON memory
  -> optional semantic indexing with structured fallback
```

Linux CPU/load intelligence:

```text
ordered CPU and scheduler evidence
  -> deterministic parsing and classification
  -> D-state, I/O wait, CPU saturation, steal time, and high-load findings
  -> safe next diagnostic action
  -> Linux-native JSON memory
  -> optional semantic indexing with structured fallback
```

Linux network/NIC intelligence:

```text
ordered network and NIC evidence
  -> deterministic parsing and classification
  -> interface down, no carrier, errors/drops, route, and resolver findings
  -> safe next diagnostic action
  -> Linux-native JSON memory
  -> optional semantic indexing with structured fallback
```

Linux service intelligence:

```text
ordered systemd evidence
  -> deterministic parsing and classification
  -> start-limit, failed unit, exit status, restart-loop, and journal findings
  -> safe next diagnostic action
  -> Linux-native JSON memory
  -> optional semantic indexing with structured fallback
```

Linux investigation ladder:

```text
health
  -> explain
  -> plan
  -> collect domain evidence
  -> investigate deterministically
  -> persist memory
  -> correlate to Kubernetes, AWS, dashboards, and approvals
```

The current human-readable map is:

```text
docs/linux/LINUX_INVESTIGATION_LADDER.md
```

Kubernetes-to-Linux correlation training:

```text
aop investigate k8s-linux --list
aop investigate k8s-linux --incident OOMKilled
aop investigate k8s-linux --incident DiskPressure --format json
```

Implemented symptom mappings:

```text
OOMKilled
CrashLoopBackOff
ImagePullBackOff
ErrImagePull
CreateContainerConfigError
CreateContainerError
FailedScheduling
DiskPressure
MemoryPressure
NodeNotReady
```

The executable catalog is:

```text
app/agents/sre/k8s_linux_correlation_agent.py
app/memory/knowledgebase/kubernetes_linux_correlation_catalog.md
```

Curated Kubernetes issue knowledge:

```text
aop investigate k8s-knowledge --list
aop investigate k8s-knowledge --symptom CrashLoopBackOff
aop investigate k8s-knowledge --symptom DiskPressure --format json
```

Implemented issue memory:

```text
CrashLoopBackOff
ImagePullBackOff
ErrImagePull
OOMKilled
CreateContainerConfigError
CreateContainerError
FailedScheduling
DiskPressure
MemoryPressure
PIDPressure
NodeNotReady
NetworkUnavailable
```

The executable catalog is:

```text
app/agents/sre/kubernetes_issue_training_agent.py
app/memory/knowledgebase/kubernetes_issue_catalog.md
```

Kubernetes investigation guidance integration:

```text
aop investigate k8s -n ai-lab
aop investigate k8s -n ai-lab --format json
aop investigate k8s -n ai-lab --format markdown --output reports/incident.md
```

The workflow now includes:

```text
correlation_guidance
  -> Kubernetes issue knowledge
  -> Kubernetes-to-Linux evidence requirements
  -> safe next AOP commands
  -> do-not-assume rules
  -> evidence gaps
```

Kubernetes expert shortcuts:

```text
aop kx list
aop kx oom
aop kx crash
aop kx image
aop kx disk
aop kx node
aop kx explain DiskPressure --json
```

Linux expert shortcuts:

```text
aop lx list
aop lx boot
aop lx kernel
aop lx grub
aop lx storage
aop lx lvm
aop lx dns
aop lx nfs
aop lx limits
aop lx selinux
aop lx runtime
```

Linux command reasoning:

```text
aop linux explain <command>
  -> command purpose
  -> argument meaning
  -> troubleshooting value
  -> risk and root-read notes
  -> related next commands

aop linux plan disk --path <path>
  -> read-only investigation order
  -> capacity, inode, mount, growth, deleted-open file, kernel, and I/O checks
  -> Kubernetes node and AWS/EBS correlation

aop linux plan scenario <scenario>
  -> senior Linux scenario planning
  -> symptoms, likely causes, first safe checks, interpretation, and traps
  -> Kubernetes, AWS, and cgroup correlation where relevant
```

Linux complex scenario memory:

```text
app/memory/knowledgebase/linux_complex_troubleshooting_scenarios.md
```

This is the source memory behind the v0.14 scenario planning CLI for high load
with low CPU, `D` state, memory/OOM, `df`/`du` mismatch, inode exhaustion,
read-only filesystems, file descriptor pressure, port conflicts, systemd
restart loops, kernel panic clues, LVM expansion mismatch, and container
runtime disk pressure.

General Linux cross-signal correlation and AI RCA are not implemented.
Original `tshelper` sources are preserved under
`docs/linux/tshelper-original/`.

Observability/dashboard direction:

```text
Prometheus and Grafana are useful integrations, not the whole AOP model.
AOP should own normalized evidence, alert-signal, timeline, and dashboard
contracts so CLI, UI, reports, chat, memory, and AI can share the same truth.
```

Implemented v0.15 contracts:

```text
MetricPoint
MetricSeries
AlertSignal
EvidenceItem
EvidenceTimeline
DashboardPanel
DashboardSnapshot
```

AI provider direction:

```text
Current implemented LLM provider: Ollama.
Planned future provider: Kimi/Moonshot.
Kimi is not implemented yet; do not claim runtime support.
```

## Kubernetes and Linux AI Criterion

Founder's authored LinkedIn source:

```text
app/memory/knowledgebase/linkedin_kubernetes_linux_criteria.md
```

Durable rule:

```text
Kubernetes symptom
  -> collect orchestration evidence
  -> determine whether a Linux node cause is plausible
  -> correlate node evidence when available
  -> state evidence gaps when unavailable
  -> never invent host facts
  -> recommend the next read-only aop linux command
```

This policy is active in the RCA, combined incident-analysis, and remediation
prompts through `app/prompts/shared/cross_domain.py`.

## Main Files

```text
app/cli/main.py
app/cli/investigate.py
app/cli/health.py
app/cli/kubernetes.py
app/cli/linux.py
app/orchestration/incident_workflow.py
app/orchestration/linux_cpu_workflow.py
app/orchestration/linux_disk_workflow.py
app/orchestration/linux_memory_workflow.py
app/orchestration/linux_network_workflow.py
app/orchestration/linux_service_workflow.py
app/tools/kubernetes/incident_context.py
app/tools/kubernetes/operations.py
app/tools/linux/operations.py
app/tools/linux/internals.py
app/schemas/linux.py
app/agents/linux/
app/agents/sre/incident_classifier.py
app/agents/sre/rca_agent.py
app/agents/sre/remediation_agent.py
app/prompts/shared/cross_domain.py
app/memory/knowledgebase/linkedin_kubernetes_linux_criteria.md
app/memory/knowledgebase/linux_complex_troubleshooting_scenarios.md
app/memory/knowledgebase/kubernetes_linux_correlation_catalog.md
app/memory/knowledgebase/kubernetes_issue_catalog.md
app/llm/client.py
app/llm/providers/ollama_provider.py
docs/architecture/observability-dashboard-strategy.md
app/memory/retrieval/hybrid_search.py
app/memory/incident_history/store_incident.py
app/memory/vectorstore/client.py
app/schemas/
tests/
```

Read only files relevant to the current task. Use README or ADRs only when
architecture history or setup details are specifically needed.

## Showcase Commands

```bash
source venv/bin/activate
aop health
aop kb health
aop kb po
aop kb ev
aop linux health
aop linux explain "df -hT"
aop linux plan disk --path /var
aop linux disk --path /var
aop linux network
aop linux internals --interval 5
aop linux cgroups --pid 1 --interval 5
aop linux all --json
aop investigate linux disk --path /var
aop investigate linux memory --pid 4242
aop investigate linux cpu
aop investigate linux network --iface ens5
aop investigate linux service --service nginx
aop investigate k8s-knowledge --symptom CrashLoopBackOff
aop investigate k8s-knowledge --symptom DiskPressure --format json
aop investigate k8s-linux --incident OOMKilled
aop investigate k8s-linux --incident DiskPressure --format json
aop kx oom
aop kx disk
aop kx node
aop lx boot
aop lx grub
aop lx storage
aop lx dns
aop investigate k8s --namespace ai-lab
aop investigate k8s --namespace ai-lab \
  --format markdown \
  --output reports/incident.md
aop memory search --namespace ai-lab
```

Kubernetes shortcut reference:

```text
docs/KUBERNETES_CLI.md
docs/ROADMAP.md
docs/releases/
docs/architecture/observability-dashboard-strategy.md
app/memory/knowledgebase/kubernetes_linux_correlation_catalog.md
app/memory/knowledgebase/kubernetes_issue_catalog.md
```

Linux references:

```text
docs/LINUX_CLI.md
docs/linux/LINUX_EXPERTISE_BLUEPRINT.md
docs/linux/LINUX_INVESTIGATION_LADDER.md
docs/linux/tshelper-original/
app/memory/knowledgebase/linux_troubleshooting_command_catalog.md
app/memory/knowledgebase/linux_expert_shortcuts_catalog.md
```

Sample incidents:

```bash
kubectl apply -f kubernetes/incidents/imagepull/broken-nginx.yaml
kubectl apply -f kubernetes/incidents/oomkilled/oom-test.yaml
kubectl apply -f kubernetes/incidents/crashloop/crashloop-app.yaml
kubectl apply -f kubernetes/incidents/configerror/missing-configmap.yaml
kubectl apply -f kubernetes/incidents/failedscheduling/oversized-pod.yaml
```

Offline validation:

```bash
python -m unittest discover -s tests -v
git diff --check
```

## Configuration

Use `.env.example`. Local `.env`, generated data, audit ZIPs, `.DS_Store`,
and packaging metadata are ignored.

Important settings:

```text
PROMETHEUS_URL
ENABLE_METRICS_ENRICHMENT
OLLAMA_BASE_URL
LLM_MODEL_NAME
EMBEDDING_MODEL_NAME
INCIDENT_HISTORY_DIR=data/incidents
VECTORSTORE_PATH=data/vectorstore/chroma
SAFE_MODE=true
ENABLE_DESTRUCTIVE_REMEDIATION=false
```

## Engineering Rules

- Evidence before AI reasoning.
- Correlate Kubernetes symptoms with Linux node evidence when relevant.
- State missing host evidence explicitly; never infer invented Linux facts.
- Use the Linux command catalog as the canonical source for safe diagnostic
  commands, arguments, interpretation, and future collector expansion.
- Deterministic classification before LLM analysis.
- Keep typed Pydantic contracts between layers.
- Agents use provider clients, not vendor transports directly.
- Do not hardcode Grafana-only, Prometheus-only, or Ollama-only assumptions.
- Preserve exact-memory fallback when semantic memory is unavailable.
- Do not hide programming errors behind fallback behavior.
- No destructive remediation without explicit policy and approval controls.
- Keep changes scoped; add tests when behavior changes.
- Do not expand into new domains until the Kubernetes path stays stable.

## Known Gaps

- Kubernetes and Prometheus live integration is not currently validated.
- Kubernetes issue knowledge and Kubernetes-to-Linux correlation now enrich
  live Kubernetes investigation reports, but they still do not automatically
  collect Linux node evidence.
- Kimi/Moonshot provider runtime support is not implemented.
- FastAPI and most non-Kubernetes domain modules are placeholders.
- Test coverage is focused, not comprehensive.
- RCA/remediation outputs are prose rather than structured action contracts.
- No CI pipeline yet.
- ADR numbering contains an older duplicate Prometheus ADR.

## Next Priorities

1. Convert boot/kernel/grubby into deterministic Linux investigators.
2. Convert storage/LVM/NFS into deterministic Linux investigators.
3. Prepare dashboard/evidence timeline summaries from the enriched workflow.
4. Run and record a complete live Kubernetes/Prometheus showcase.
5. Add CI for tests, formatting, linting, and type checks.
6. Validate Linux disk diagnosis against real ext4, XFS, LVM, container, and
   cloud-volume examples.
5. Extend the next Linux scenario plan into deterministic investigation,
   starting with CPU/load and `D` state.
6. Add recurrence and incident-pattern intelligence.
7. Introduce structured AI output contracts.
8. Add approval-gated execution only after governance exists.

## Codex Startup Rule

Start with `docs/PROJECT_HANDOVER.md`, then use this file as compact
implementation memory. Inspect only the files needed for the requested task.
Also read `docs/AOP_PRODUCT_VISION.md` when the task affects product direction
or roadmap. Treat current source and tests as truth for implemented behavior
when older docs disagree.
Read `docs/architecture/observability-dashboard-strategy.md` before dashboard,
graph, telemetry, alert-processing, or provider-routing work.
