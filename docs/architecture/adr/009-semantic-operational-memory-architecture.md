# ADR-009: Semantic Operational Memory Architecture

**Date:** 2026-05-15  
**Status:** Accepted  
**Decision Type:** Architecture / AI Platform Engineering / Operational Memory Design  
**Owners:** Autonomous Ops Platform Engineering  

---

# Context

Autonomous Ops Platform initially introduced structured operational memory for incident persistence.

Architecture:

```text
incident workflow
    ↓
IncidentMemory
    ↓
JSON persistence
```

This enabled:

- incident auditability
- historical storage
- deterministic retrieval
- operational memory enrichment

Structured memory introduced via:

```text
app/schemas/memory.py
app/memory/incident_history/store_incident.py
app/memory/retrieval/search.py
```

This design improved platform memory maturity.

However, deterministic exact-match retrieval alone was insufficient for intelligent operational reasoning.

---

# Problem Statement

Operational incidents often share semantic similarity without exact metadata equality.

Examples:

Example A:

```text
ApplicationCrashLoop
failure_reason=OOMKilled
```

Example B:

```text
MemoryExhaustion
failure_reason=ContainerMemoryPressure
```

Operationally similar.

But exact-match retrieval would treat them as unrelated.

---

## Deterministic Retrieval Limitation

Structured retrieval depends on exact filtering:

```python
incident_type == query.incident_type
namespace == query.namespace
severity == query.severity
```

Limitations:

- exact string dependency
- schema equality assumptions
- inability to detect semantically related incidents
- poor fuzzy reasoning

---

## AI Historical Reasoning Limitation

LLM-powered RCA and remediation agents initially reasoned only from:

```text
current incident context
```

No semantic operational memory existed.

Consequences:

- no similarity-based recall
- no contextual operational learning
- repeated AI reasoning from scratch
- weak organizational memory

---

## Future Platform Vision

Autonomous Ops Platform is evolving toward:

- AI-assisted SRE incident response
- autonomous operational diagnostics
- historical learning
- remediation recommendation
- organizational operational intelligence
- multi-agent operational reasoning

These capabilities require semantic operational memory.

---

# Decision

Introduce hybrid semantic operational memory architecture.

Architecture:

```text
Deterministic Memory
        +
Semantic Vector Memory
        =
Hybrid Operational Memory
```

This architecture enables both:

- exact structured retrieval
- semantic similarity retrieval

for AI operational reasoning.

---

# Architecture Introduced

---

# Structured Memory Layer

Canonical operational incident persistence remains:

```text
app/memory/incident_history/
```

Structured memory stores:

```python
IncidentMemory
```

Purpose:

- auditability
- exact retrieval
- deterministic operational history
- canonical source of operational truth

---

# Embedding Abstraction Layer

Introduced:

```text
app/llm/embeddings/
```

Components:

```text
client.py
providers/base.py
providers/ollama_embedding_provider.py
```

Architecture:

```text
EmbeddingClient
    ↓
EmbeddingProvider
    ↓
Ollama implementation
```

Purpose:

Semantic vector generation abstraction.

Future provider portability:

- Ollama
- OpenAI embeddings
- VoyageAI
- BGE
- enterprise embedding providers

---

# Vector Store Abstraction Layer

Introduced:

```text
app/memory/vectorstore/
```

Components:

```text
client.py
providers/base.py
providers/chroma_provider.py
```

Architecture:

```text
SemanticMemoryClient
        ↓
VectorStoreProvider
        ↓
Chroma implementation
```

Purpose:

Vector database abstraction.

Avoid direct infrastructure coupling.

---

# Initial Vector Store Implementation

Initial provider:

```text
ChromaDB
```

Selection rationale:

- rapid implementation
- local development simplicity
- Python-native integration
- semantic search experimentation

Explicit decision:

ChromaDB is an implementation choice, not a permanent platform dependency.

---

# Retrieval Architecture

Structured retrieval:

```text
app/memory/retrieval/search.py
```

Semantic retrieval:

```text
app/memory/retrieval/semantic_search.py
```

Hybrid fusion:

```text
app/memory/retrieval/hybrid_search.py
```

Architecture:

```text
Hybrid Retrieval
      ↓
Exact Search
      +
Semantic Search
```

Purpose:

Operational context fusion.

---

# AI Agent Integration

RCA agent:

```text
app/agents/sre/rca_agent.py
```

Now enriched with:

```text
hybrid operational memory
```

Remediation agent:

```text
app/agents/sre/remediation_agent.py
```

Now enriched with:

```text
historical operational context
```

Architecture:

```text
Incident
   ↓
Classification
   ↓
Hybrid Retrieval
   ↓
Memory-Aware RCA
   ↓
Memory-Aware Remediation
```

---

# Persistence Integration

Structured incident persistence now also triggers:

```text
semantic indexing
```

Architecture:

```text
store_incident.py
      ↓
Structured JSON persistence
      +
SemanticMemoryClient indexing
```

Result:

Dual operational memory persistence.

---

# Alternatives Considered

---

# Option 1 — Structured Exact Retrieval Only

Architecture:

```text
JSON memory only
```

Advantages:

- simple
- deterministic
- easy debugging
- low complexity

Disadvantages:

- no semantic recall
- weak AI contextual reasoning
- exact-match limitations
- poor fuzzy operational learning

Decision:

Rejected.

---

# Option 2 — Direct Chroma Coupling

Architecture:

```text
Agents
   ↓
Direct Chroma calls
```

Advantages:

- rapid implementation
- fewer abstractions

Disadvantages:

- infrastructure coupling
- migration difficulty
- vendor lock-in
- architecture leakage

Decision:

Rejected.

---

# Option 3 — Hybrid Semantic Architecture with Provider Abstraction

Architecture:

```text
Agents
   ↓
Hybrid Retrieval
   ↓
SemanticMemoryClient
   ↓
VectorStoreProvider
```

Advantages:

- semantic reasoning
- exact retrieval preservation
- future DB portability
- clean abstraction
- enterprise evolution readiness

Disadvantages:

- higher complexity
- more components
- abstraction maintenance overhead

Decision:

Accepted.

---

# Decision Rationale

Autonomous Ops Platform requires organizational operational learning.

Deterministic retrieval alone cannot support:

- semantic incident similarity
- fuzzy operational recall
- AI-assisted historical reasoning
- contextual remediation learning

Hybrid memory provides:

- exact auditability
- semantic intelligence
- infrastructure abstraction
- future evolution safety

This aligns with long-term platform vision.

---

# Operational Impact

Benefits introduced:

---

## Memory-Aware RCA

AI RCA reasoning now considers:

- exact incident history
- semantically similar incidents

Improves:

- contextual diagnosis
- recurrence awareness
- historical reasoning

---

## Memory-Aware Remediation

AI remediation now considers:

- prior incidents
- historical remediation context

Improves:

- recommendation quality
- operational consistency
- organizational learning

---

## Hybrid Retrieval

Combined:

```text
exact + semantic
```

Improves retrieval quality.

---

## Infrastructure Abstraction

Semantic memory avoids direct DB coupling.

Future replacements possible without agent rewrites.

---

# Risks Accepted

Current implementation limitations:

---

## Chroma as Initial Implementation

Chroma chosen for acceleration.

Known limitations:

- single-node assumptions
- operational maturity limitations
- weaker enterprise governance

Accepted as interim implementation.

---

## Structured / Vector Drift

Current architecture allows:

```text
structured memory
semantic memory
```

to diverge if manually modified.

Accepted for current maturity.

Future architecture should treat semantic memory as rebuildable derived state.

---

## Duplicate Incident Indexing

Current implementation indexes individual incidents.

No recurrence grouping yet.

Accepted for current phase.

---

# Future Evolution

Planned maturity:

---

## PostgreSQL + pgvector Migration

Target enterprise vector architecture:

```text
PostgreSQL + pgvector
```

Potential provider:

```text
PgVectorStoreProvider
```

No agent refactor required.

---

## Alternative Vector Providers

Potential implementations:

- Qdrant
- Weaviate
- enterprise vector platforms

Supported by abstraction design.

---

## Incident Pattern Intelligence

Future evolution:

- recurrence grouping
- fingerprint clustering
- pattern-level operational learning

---

## Semantic Reranking

Future hybrid retrieval enhancements:

- reranking
- confidence scoring
- weighted fusion

---

## Multi-Agent Shared Memory

Future:

```text
shared organizational operational memory
```

for:

- RCA agents
- remediation agents
- diagnostics agents
- automation agents

---

# Final Outcome

Autonomous Ops Platform evolved from deterministic historical incident storage into hybrid semantic operational memory architecture.

This introduced:

- semantic operational intelligence
- AI historical reasoning
- hybrid retrieval
- vector abstraction
- infrastructure portability
- organizational operational learning

This is a foundational architecture milestone in autonomous operational intelligence evolution.