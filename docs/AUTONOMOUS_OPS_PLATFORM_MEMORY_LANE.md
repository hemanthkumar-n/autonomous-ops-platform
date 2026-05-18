# Autonomous Ops Platform Memory Lane

Date: 2026-05-19

Use this file as the compact project context when starting a fresh ChatGPT or Codex conversation. It is intentionally much smaller than the full repo, but it preserves the design intent, active architecture, current implementation state, and next engineering priorities.

## One-Line Summary

Autonomous Ops Platform is an AI-native operational intelligence platform for SRE and platform engineering, currently focused on Kubernetes incident intelligence with Prometheus enrichment, local Ollama-based RCA/remediation, structured incident memory, semantic vector memory, and safe advisory remediation.

## Repository

- GitHub: `https://github.com/hemanthkumar-n/autonomous-ops-platform/`
- Local repo inspected: `/Users/hemanthkumarn/autonomous-ops-platform`
- Audit zip inspected: `/Users/hemanthkumarn/autonomous-ops-platform/autonomous-ops-platform-audit.zip`
- Live repo should be treated as source of truth over the zip because it has current uncommitted changes.

## Current Project Stage

The project has evolved from an early broad AOP vision into a Day 6 style platform foundation:

- Kubernetes incident context collection
- Prometheus observability enrichment
- deterministic incident classification
- AI root cause analysis
- AI remediation guidance
- unified incident workflow orchestration
- persistent structured incident memory
- semantic vector memory through ChromaDB
- hybrid exact plus semantic retrieval
- provider abstractions for LLM, embeddings, and vector store

The repo still contains many placeholder modules for future Linux, AWS, DevOps, security, observability, Terraform, Jenkins, Slack, Jira, and Confluence capabilities.

## High-Level Architecture

```text
Kubernetes problematic workloads
    -> incident context collector
    -> Prometheus metrics enrichment
    -> deterministic incident classifier
    -> hybrid memory retrieval
    -> AI RCA
    -> AI remediation guidance
    -> workflow aggregation
    -> structured JSON persistence
    -> semantic Chroma indexing
```

## Core Runtime Flow

Main workflow:

```text
app/orchestration/incident_workflow.py
```

Execution flow:

1. `collect_incident_context()`
2. `classify_incident()`
3. `generate_rca()` per incident
4. `generate_all_remediations()` or remediation generation per incident
5. `WorkflowExecutionResponse`
6. `store_incident()`
7. JSON memory persistence plus semantic indexing

## Key Implemented Modules

### Configuration

```text
app/config/settings.py
app/config/logging_config.py
```

Settings include:

- `PLATFORM_NAME`
- `ENVIRONMENT`
- `WORKFLOW_VERSION`
- `PROMETHEUS_URL`
- `PROMETHEUS_TIMEOUT`
- `PROMETHEUS_RETRIES`
- `ENABLE_METRICS_ENRICHMENT`
- `MAX_LOG_LINES`
- `ENABLE_POD_LOG_COLLECTION`
- `ENABLE_EVENT_COLLECTION`
- `INCIDENT_HISTORY_DIR`
- `PERSIST_INCIDENTS`
- `OLLAMA_BASE_URL`
- `LLM_MODEL_NAME`
- `EMBEDDING_MODEL_NAME`
- `AI_REQUEST_TIMEOUT`
- `ENABLE_DESTRUCTIVE_REMEDIATION`
- `SAFE_MODE`

Important note: current uncommitted settings changes add vector store config inside `validate()` rather than `__init__`. This works as an attribute side effect, but it belongs in `__init__` before `self.validate()` for cleaner design.

### Kubernetes Context

```text
app/tools/kubernetes/incident_context.py
```

Collects problematic pods outside system namespaces. Signals include:

- pod name
- namespace
- phase
- node
- pod conditions
- container state
- restart count
- last termination reason and exit code
- resource requests and limits
- bounded logs
- pod events
- Prometheus metrics

Supporting files:

```text
app/tools/kubernetes/log_tools.py
app/tools/kubernetes/event_tools.py
app/tools/kubernetes/pod_tools.py
```

### Prometheus

```text
app/tools/prometheus/prometheus_client.py
app/tools/prometheus/metrics_tools.py
app/tools/prometheus/queries.py
```

Prometheus metrics collected:

- `container_memory_working_set_bytes`
- `rate(container_cpu_usage_seconds_total[5m])`
- `kube_pod_container_status_restarts_total`

Metric fetches run in parallel and return typed `PodMetrics`.

### Incident Classification

```text
app/agents/sre/incident_classifier.py
app/agents/sre/incident_rules.py
```

Supported rules:

- `OOMKilled` -> `MemoryExhaustion`, Critical, confidence 99
- `CrashLoopBackOff` -> `ApplicationCrashLoop`, High, confidence 95
- `ImagePullBackOff` -> `ImagePullFailure`, High, confidence 98
- `ErrImagePull` -> `ImagePullFailure`, High, confidence 96
- `CreateContainerConfigError` -> `ContainerConfigurationFailure`, High, confidence 95
- `CreateContainerError` -> `ContainerStartupFailure`, High, confidence 94
- `FailedScheduling` -> `SchedulingFailure`, Critical, confidence 93

Unknown states fallback to `UnknownIncident`.

### AI RCA

```text
app/agents/sre/rca_agent.py
```

Builds an SRE-style RCA prompt from:

- incident context
- classification
- historical exact memory
- semantic memory
- Prometheus metrics

Output sections requested:

- Incident Summary
- Historical Similarity Analysis
- Root Cause Analysis
- Signal Correlation
- Severity Assessment
- Team Ownership Recommendation
- Preventive Recommendations

### AI Remediation

```text
app/agents/sre/remediation_agent.py
```

Produces safe advisory remediation, not automatic destructive action.

Safety rules:

- no destructive action automatically
- validation-first guidance
- escalation if confidence is limited
- preserve operational safety

Output sections requested:

- Incident
- Historical Similarity Analysis
- Immediate Safe Actions
- Kubernetes Validation Commands
- Escalation Recommendation
- Preventive Recommendations
- Risk Notes

### LLM Provider Abstraction

```text
app/llm/client.py
app/llm/providers/base.py
app/llm/providers/ollama_provider.py
app/llm/response_validator.py
```

Agents use `LLMClient`, not direct provider transport. Current provider is Ollama via `/api/generate`.

Default model:

```text
qwen2.5-coder:latest
```

Future intended providers:

- OpenAI
- Claude
- Gemini
- enterprise gateways
- vLLM
- LiteLLM

### Embedding Abstraction

```text
app/llm/embeddings/client.py
app/llm/embeddings/providers/base.py
app/llm/embeddings/providers/ollama_embedding_provider.py
```

Current embedding provider:

```text
OllamaEmbeddingProvider
```

Default embedding model:

```text
nomic-embed-text
```

### Memory

Structured memory:

```text
app/memory/incident_history/store_incident.py
app/memory/retrieval/search.py
```

Semantic memory:

```text
app/memory/vectorstore/client.py
app/memory/vectorstore/providers/base.py
app/memory/vectorstore/providers/chroma_provider.py
app/memory/retrieval/semantic_search.py
```

Hybrid retrieval:

```text
app/memory/retrieval/hybrid_search.py
```

Structured memory writes timestamped files named like:

```text
incident_memory_YYYYMMDD_HHMMSS.json
```

Default structured memory directory:

```text
app/memory/incident_history/incidents
```

Current Chroma path is hardcoded in provider:

```text
app/memory/vectorstore/chroma_db
```

The code also has a newer config idea for:

```text
VECTORSTORE_PROVIDER
VECTORSTORE_PATH
VECTORSTORE_COLLECTION_NAME
```

but provider code does not yet use these settings.

## Typed Contracts

Important schema files:

```text
app/schemas/incident.py
app/schemas/classification.py
app/schemas/ai.py
app/schemas/metrics.py
app/schemas/memory.py
app/schemas/workflow.py
```

Key models:

- `IncidentContext`
- `ContainerState`
- `PodCondition`
- `PodMetrics`
- `IncidentClassification`
- `RCAResponse`
- `RemediationResponse`
- `WorkflowExecutionResponse`
- `IncidentFingerprint`
- `IncidentMemory`
- `MemoryQuery`
- `MemorySearchResult`

## Docs And Decisions

Important docs:

```text
README.md
docs/setup/installation.md
docs/architecture/incident-intelligence-workflow.md
docs/builder_journal/phase-2-hardening.md~
```

Accepted or implemented ADRs:

```text
docs/architecture/adr/001-centralized-runtime-settings.md
docs/architecture/adr/002-prometheus-incident-enrichment.md
docs/architecture/adr/003-structured-logging-standardization.md
docs/architecture/adr/004-ai-agent-resilience-hardening.md
docs/architecture/adr/005-incident-workflow-orchestration.md
docs/architecture/adr/006-typed-platform-contracts.md
docs/architecture/adr/007-llm-provider-abstraction.md
docs/architecture/adr/008-operational-memory-architecture.md
docs/architecture/adr/009-semantic-operational-memory-architecture.md
```

There are duplicate ADR numbering/name concerns:

- both `001-centralized-runtime-settings.md`
- and `001-prometheus-incident-enrichment.md`
- plus `002-prometheus-incident-enrichment.md`

This should be cleaned later to avoid confusion.

## Current Implementation Reality

Implemented or meaningful:

- SRE incident classification
- RCA agent
- remediation agent
- incident workflow orchestration
- Kubernetes incident collector
- Kubernetes logs/events/pod tools
- Prometheus client/queries/metrics
- settings/logging
- LLM abstraction
- Ollama provider
- embedding abstraction
- Chroma vector provider
- structured and semantic memory
- incident docs and ADRs

Mostly placeholder or empty:

- FastAPI app layer
- CLI commands under `app/cli`
- tests
- base agent classes
- Linux agents/tools
- AWS/cloud agents
- DevOps agents
- security agents
- observability vendor agents
- Grafana/Datadog/Splunk tool implementations
- Terraform/Jenkins/GitHub/Slack/Jira/Confluence implementations
- infra and deployment manifests

## Current Git State Observed

Uncommitted changes:

```text
 M .DS_Store
 M .gitignore
 M app/config/settings.py
?? autonomous-ops-platform-audit.zip
```

Advice:

- remove `.DS_Store` from git tracking later
- keep audit zip out of git unless intentionally publishing it
- clean `.gitignore`; it currently has a suspicious joined line: `.DS_Storeapp/memory/incident_history/incidents/`
- move vector store settings from `validate()` into `__init__`

## Dependencies

Current `requirements.txt` includes:

- FastAPI
- Uvicorn
- Pydantic
- python-dotenv
- Kubernetes Python client
- requests
- OpenAI package
- Ollama
- ChromaDB

Potential issue:

- README says Python 3.14+, but docs say Python 3.11+. Prefer documenting Python 3.11+ unless the project intentionally targets 3.14.

## Run Commands

Setup:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Ollama:

```bash
ollama serve
ollama pull qwen2.5-coder
ollama pull nomic-embed-text
```

Kubernetes checks:

```bash
kubectl cluster-info
kubectl get nodes
kubectl get pods -A
```

Prometheus should be available at:

```text
http://localhost:9090
```

Useful module runs:

```bash
python -m app.tools.kubernetes.incident_context
python -m app.agents.sre.incident_classifier
python -m app.agents.sre.rca_agent
python -m app.agents.sre.remediation_agent
python -m app.orchestration.incident_workflow
```

Sample incidents:

```bash
kubectl apply -f kubernetes/incidents/imagepull/broken-nginx.yaml
kubectl apply -f kubernetes/incidents/oomkilled/oom-test.yaml
```

## Near-Term Engineering Priorities

1. Add tests for deterministic logic.
   Start with incident rules, Prometheus metric parsing, memory fingerprinting, structured memory search, and prompt construction.

2. Fix config hygiene.
   Move vectorstore settings into `__init__`, make Chroma path and collection configurable, clean `.gitignore`, stop tracking generated files.

3. Add a real CLI.
   Implement commands like `aop investigate k8s`, `aop memory search`, `aop workflow run`, and dry-run remediation helpers.

4. Add API routes only after CLI/core is stable.
   FastAPI is present but currently mostly placeholder.

5. Separate storage/data from code.
   Do not keep Chroma DB or incident history in source-controlled app paths long term. Prefer `data/` or `.aop/` with `.gitignore`.

6. Improve provider governance.
   Add provider selection through config, retries, fallback, timeout policy, and structured LLM error types.

7. Improve prompt/output contracts.
   Consider structured JSON responses from RCA/remediation agents to make downstream automation safer.

8. Create real CI.
   Add formatting, linting, type checks, and unit tests before expanding features.

## Suggested New Chat Instruction

When starting a new ChatGPT or Codex chat, paste this:

```text
You are helping with my repo `autonomous-ops-platform`.
First read `AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md` if available, then inspect only files relevant to the task.

Treat the current source code as truth, but preserve these principles:
- evidence before AI reasoning
- deterministic checks before LLM output
- typed contracts between layers
- provider abstractions for LLM, embeddings, and vector stores
- safe, advisory remediation only unless explicitly approved
- memory-first incident reasoning using exact plus semantic retrieval

My current platform focus is Kubernetes incident intelligence with Prometheus enrichment, Ollama-based RCA/remediation, structured incident memory, semantic Chroma memory, and a unified incident workflow.

For any task, keep changes scoped, avoid broad refactors, and update docs/tests when the behavior changes.
```

## Expert Direction

The project is promising, but it should resist expanding horizontally too soon. The strongest path is to make the Kubernetes incident intelligence loop excellent first:

```text
detect -> collect -> classify -> enrich -> remember -> reason -> recommend -> verify
```

Once that loop has tests, CLI ergonomics, stable config, and repeatable demos, then expand into Linux, AWS, Terraform, and broader autonomous operations.

