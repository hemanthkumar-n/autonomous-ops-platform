# New Codex Chat

```text
Work in `autonomous-ops-platform`.

First read `docs/PROJECT_HANDOVER.md`.
Use `docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md` as compact implementation
memory when more detail is needed.
Then inspect only files relevant to my task; do not scan every ADR or Markdown
file unless the task requires architecture history.

If the task concerns roadmap, Linux, AWS, UI, Slack/Teams, company onboarding,
or product direction, also read `docs/AOP_PRODUCT_VISION.md`.

Preserve:
- evidence before AI
- deterministic classification before LLM reasoning
- typed contracts
- provider abstraction
- exact-memory fallback when semantic memory is unavailable
- advisory, non-destructive remediation
- focused changes with tests

Treat current code and tests as truth over stale documentation.
Do not claim placeholder modules as implemented.
Do not add LangGraph or another orchestration framework unless the workflow
requires branching, checkpointing, resumability, or approval pauses.

Explain substantial Linux changes before implementing them. Then test,
document, commit, and push completed work.

Task:
<describe the task>
```
