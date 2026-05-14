# ADR-007: Centralized LLM Provider Abstraction for AI Platform Governance
**Date:** 2026-05-15
**Status:** Implemented
**Decision Type:** AI Platform Architecture / Provider Abstraction / Service Design
**Owners:** Autonomous Ops Platform Engineering
---
# Context
Autonomous Ops Platform introduced AI-assisted operational reasoning for:
- incident root cause analysis
- remediation recommendation generation
- autonomous workflow intelligence
Initial AI implementation embedded direct LLM transport logic inside application agents.
Affected modules:
```text
app/agents/sre/rca_agent.py
app/agents/sre/remediation_agent.py

These agents directly handled:

* HTTP transport
* Ollama endpoint construction
* payload construction
* timeout handling
* response parsing
* response validation
* provider-specific error handling

Example architecture:

RCA Agent
   ↓
requests.post()
   ↓
Ollama API

and:

Remediation Agent
   ↓
requests.post()
   ↓
Ollama API

This approach accelerated initial validation.

However, it introduced architectural coupling between AI reasoning logic and provider infrastructure.

⸻

Problem Statement

Direct provider coupling inside agents created significant engineering risk.

⸻

Infrastructure Leakage Into Business Logic

Agents responsible for operational reasoning also managed transport infrastructure.

Example responsibilities incorrectly mixed:

RCA reasoning
+
HTTP transport
+
endpoint construction
+
provider parsing

This violated separation of concerns.

⸻

Provider Lock-In

Agents depended directly on Ollama.

Examples:

requests.post(...)
settings.OLLAMA_BASE_URL
/api/generate

Changing provider would require agent rewrites.

This blocked:

* OpenAI adoption
* Claude adoption
* Gemini integration
* enterprise model gateway adoption
* vLLM integration
* LiteLLM routing

⸻

Duplicate AI Transport Logic

Multiple agents repeated identical provider logic.

Repeated concerns:

* request execution
* payload construction
* timeout handling
* response parsing
* validation
* exception handling

This created duplication and maintenance risk.

⸻

Weak Resilience Architecture

Direct provider coupling prevented centralized resilience controls.

Missing capabilities:

* retries
* fallback providers
* timeout governance
* centralized failure handling

⸻

No Routing Architecture

Future platform requires workload-aware model routing.

Examples:

Lightweight models:

classification

Higher reasoning models:

deep RCA

Safe local models:

remediation planning

Direct provider coupling blocks routing.

⸻

No AI Governance Layer

Enterprise AI platforms require governance controls.

Missing:

* approved provider enforcement
* model allowlists
* prompt policy enforcement
* cost governance
* audit logging
* sensitive workflow restrictions

⸻

Poor Observability

Provider interactions were distributed across agents.

Difficult to track:

* LLM latency
* provider failures
* model selection
* usage patterns
* operational AI health

⸻

Decision

Introduce centralized LLM platform abstraction.

Implementation:

app/llm/

Architecture introduced:

app/llm/providers/base.py
app/llm/providers/ollama_provider.py
app/llm/client.py

This becomes the authoritative AI access layer.

Agents no longer communicate directly with provider infrastructure.

⸻

Architecture Introduced

Provider Contract

Module:

app/llm/providers/base.py

Contract:

LLMProvider

Purpose:

Formal provider abstraction interface.

Responsibilities:

* deterministic provider contract
* uniform response interface
* future provider compatibility

Required interface:

generate(prompt, timeout=None)

⸻

Ollama Provider Implementation

Module:

app/llm/providers/ollama_provider.py

Implementation:

OllamaProvider

Responsibilities:

* HTTP transport
* endpoint construction
* payload construction
* timeout execution
* response parsing
* response validation
* provider failure handling

This isolates provider-specific infrastructure logic.

⸻

Central AI Client

Module:

app/llm/client.py

Implementation:

LLMClient

Purpose:

Single platform AI entrypoint.

Responsibilities:

Current:

* provider invocation
* request abstraction

Future:

* routing
* retries
* fallback providers
* governance controls
* observability
* cost enforcement
* policy gates

⸻

Architecture Transformation

Before:

RCA Agent
   ↓
requests.post
   ↓
Ollama
Remediation Agent
   ↓
requests.post
   ↓
Ollama

Characteristics:

* duplicated transport logic
* provider lock-in
* weak governance
* poor resilience
* mixed concerns

⸻

After:

RCA Agent
        ↓
Remediation Agent
        ↓
      LLMClient
        ↓
   LLMProvider Contract
        ↓
  OllamaProvider
        ↓
      Ollama

Characteristics:

* clean separation
* centralized AI control
* provider independence
* governance readiness
* resilience foundation

⸻

Alternatives Considered

Option 1 — Direct Provider Calls Inside Agents

Advantages:

* fast implementation
* minimal abstraction

Disadvantages:

* provider lock-in
* duplicated code
* weak resilience
* no routing
* poor observability
* governance gaps

Decision:

Rejected.

Prototype-only architecture.

⸻

Option 2 — Agent-Level Provider Wrappers

Example:

Each agent owns:

generate_ai_response()

Advantages:

* modest abstraction
* partial cleanup

Disadvantages:

* duplication remains
* weak governance
* fragmented architecture

Decision:

Rejected.

⸻

Option 3 — Centralized Provider Abstraction Layer

Advantages:

* clean architecture
* provider portability
* centralized resilience
* governance readiness
* routing support
* observability foundation

Decision:

Accepted.

Implemented.

⸻

Decision Rationale

Autonomous Ops Platform is evolving into an AI-native operational platform.

Future capabilities include:

* autonomous reasoning
* AI-assisted workflows
* approval-gated remediation
* operational memory systems
* model governance
* multi-provider AI execution

Engineering principle:

AI infrastructure must be abstracted from operational reasoning.

AI reasoning modules should not know:

* endpoints
* transport protocols
* authentication
* payload schemas
* provider internals

They should know only:

llm.generate(prompt)

⸻

Operational Impact

Cleaner Agent Architecture

Agents now focus only on reasoning logic.

Example:

RCA agent responsibilities:

* prompt construction
* RCA reasoning
* business fallback behavior

Not infrastructure.

⸻

Provider Portability

Future providers can be added without agent rewrites.

Examples:

OpenAI
Claude
Gemini
vLLM
LiteLLM
Enterprise gateway

⸻

Centralized Governance

Future enforcement possible:

* approved model policy
* environment restrictions
* prompt governance
* cost limits
* audit logging

⸻

Resilience Foundation

Future support:

* retries
* fallback providers
* provider failover
* timeout governance

⸻

Better Observability

Centralized AI interactions improve:

* latency tracking
* provider failure tracking
* AI health visibility
* usage telemetry

⸻

Risks Accepted

Current limitations:

* single provider implementation
* no routing yet
* no fallback yet
* no retry orchestration yet
* no provider selection policies yet

Accepted for current maturity.

⸻

Future Evolution

Multi-Provider Support

Planned:

openai_provider.py
claude_provider.py
gemini_provider.py
vllm_provider.py

⸻

Provider Router

Planned:

app/llm/router.py

Capabilities:

* workload-aware routing
* provider selection
* environment-based routing

⸻

Retry Policy

Centralized retry orchestration.

⸻

Fallback Execution

Provider failover support.

⸻

Governance Controls

Planned:

* provider allowlists
* model policy
* prompt restrictions
* environment gating

⸻

Cost Governance

Track:

* token consumption
* request counts
* provider costs

⸻

AI Telemetry

Expose:

* latency
* success/failure
* provider health

⸻

Final Outcome

ADR-007 established centralized AI platform abstraction for Autonomous Ops Platform.

This transformed AI architecture from provider-coupled agent execution into governed platform AI service architecture.

Material improvements:

* separation of concerns
* provider portability
* centralized AI governance readiness
* resilience foundation
* observability foundation
* enterprise AI scalability

This is a foundational AI platform architecture milestone.
