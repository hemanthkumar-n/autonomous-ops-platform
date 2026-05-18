# New Chat Starter Prompt

Paste this into a fresh ChatGPT or Codex conversation:

```text
I am working on `autonomous-ops-platform`, an AI-native SRE and platform engineering project.

Repo:
https://github.com/hemanthkumar-n/autonomous-ops-platform/

Please first read `AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md` if I provide it. If not, inspect the repo starting from:
- README.md
- docs/architecture/incident-intelligence-workflow.md
- docs/architecture/adr/
- app/orchestration/incident_workflow.py
- app/tools/kubernetes/incident_context.py
- app/agents/sre/
- app/memory/
- app/llm/
- app/schemas/

Current platform focus:
- Kubernetes incident context collection
- Prometheus metrics enrichment
- deterministic incident classification
- Ollama-based RCA and remediation
- safe advisory remediation
- structured JSON incident memory
- semantic memory using ChromaDB
- hybrid exact plus semantic retrieval
- provider abstractions for LLM, embeddings, and vector stores

Important design principles:
- evidence before AI reasoning
- deterministic checks before LLM output
- typed contracts between layers
- provider abstraction, no direct vendor coupling in agents
- memory-first operational intelligence
- no destructive remediation by default
- keep changes scoped and production-minded

Known current gaps:
- CLI files are placeholders
- FastAPI layer is placeholder
- tests are missing
- many domain folders are future skeletons
- vector store settings exist but provider still hardcodes Chroma path
- `.gitignore` needs cleanup
- ADR numbering has duplicates

Now help me with this specific task:
<replace this line with the task>
```

