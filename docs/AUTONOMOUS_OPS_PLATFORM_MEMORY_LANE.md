# Autonomous Ops Platform: Codex Memory

Updated: 2026-06-09

## Purpose

AOP is an AI-native operational intelligence runtime for SRE and platform
engineering. Kubernetes is the first production path; Linux, AWS, Terraform,
and autonomous execution remain future domains.

Long-term product direction is preserved in:

```text
docs/AOP_PRODUCT_VISION.md
```

Read that file for roadmap, product, Linux, AWS, UI, Slack/Teams, company
onboarding, or platform-positioning work. It is the durable vision source.

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

- Version: `0.7.0`
- Branch: `feature/aop-cli-transition`
- Latest commits:
  - `526bdbc` remove local artifacts from tracking
  - `e946e90` add showcase-ready AOP CLI workflow
- Python: `3.11+`
- CLI entry point: `aop`
- Tests: twelve offline regression tests passing
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

## Main Files

```text
app/cli/main.py
app/cli/investigate.py
app/cli/health.py
app/cli/kubernetes.py
app/orchestration/incident_workflow.py
app/tools/kubernetes/incident_context.py
app/tools/kubernetes/operations.py
app/agents/sre/incident_classifier.py
app/agents/sre/rca_agent.py
app/agents/sre/remediation_agent.py
app/llm/client.py
app/llm/providers/ollama_provider.py
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
aop investigate k8s --namespace ai-lab
aop investigate k8s --namespace ai-lab \
  --format markdown \
  --output reports/incident.md
aop memory search --namespace ai-lab
```

Kubernetes shortcut reference:

```text
docs/KUBERNETES_CLI.md
```

Sample incidents:

```bash
kubectl apply -f kubernetes/incidents/imagepull/broken-nginx.yaml
kubectl apply -f kubernetes/incidents/oomkilled/oom-test.yaml
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
- Deterministic classification before LLM analysis.
- Keep typed Pydantic contracts between layers.
- Agents use provider clients, not vendor transports directly.
- Preserve exact-memory fallback when semantic memory is unavailable.
- Do not hide programming errors behind fallback behavior.
- No destructive remediation without explicit policy and approval controls.
- Keep changes scoped; add tests when behavior changes.
- Do not expand into new domains until the Kubernetes path stays stable.

## Known Gaps

- Kubernetes and Prometheus live integration is not currently validated.
- FastAPI and most non-Kubernetes domain modules are placeholders.
- Test coverage is focused, not comprehensive.
- RCA/remediation outputs are prose rather than structured action contracts.
- No CI pipeline yet.
- ADR numbering contains an older duplicate Prometheus ADR.

## Next Priorities

1. Run and record a complete live Kubernetes/Prometheus showcase.
2. Add CI for tests, formatting, linting, and type checks.
3. Expand tests for Prometheus parsing, persistence, fingerprints, and reports.
4. Add recurrence and incident-pattern intelligence.
5. Introduce structured AI output contracts.
6. Add approval-gated execution only after governance exists.

## Codex Startup Rule

Start with this file. Then inspect only the files needed for the requested
task. Also read `docs/AOP_PRODUCT_VISION.md` when the task affects product
direction or roadmap. Treat current source and tests as truth for implemented
behavior when older docs disagree.
