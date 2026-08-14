# Incident Pattern Intelligence

Incident Pattern Intelligence is the next major intelligence layer after
deterministic Linux/Kubernetes investigation and operational memory.

The goal is to help AOP answer:

```text
Have we seen this before?
How often?
What changed?
Which evidence matched?
Which fix worked last time?
What should the SRE check next?
```

## Why It Matters

Enterprise incidents are rarely isolated. Teams repeatedly face:

- recurring pod failures
- repeated disk pressure on the same node pool
- periodic memory pressure after deployments
- noisy alerts masking one underlying pattern
- recurring DNS, certificate, image pull, or storage failures
- application incidents caused by infrastructure changes
- infrastructure failures that appear as Kubernetes symptoms

Without pattern intelligence, every incident starts from zero.

## Inputs

Pattern intelligence should combine:

- canonical `InvestigationCase` records
- structured incident memory
- semantic incident memory
- deterministic Linux findings
- Kubernetes incident classifications
- runbook chunks
- ticket references
- service ownership
- deployment/change metadata
- cloud and observability evidence when available

## Core Capabilities

### Incident Fingerprints

Create stable fingerprints from normalized evidence:

```text
domain + resource + symptom + finding + evidence keys + ownership context
```

Example:

```text
kubernetes:payments:OOMKilled:memory_limit_exceeded:checkout
linux:worker-07:DiskPressure:container_runtime_disk_pressure
```

Fingerprints should avoid secrets, raw customer data, and unstable timestamps.

### Recurrence Detection

Detect repeated incidents by exact and fuzzy matching:

- same namespace and symptom
- same node condition
- same service and failure mode
- same Linux finding family
- same error signature
- same runbook match

### Similarity Clustering

Group related incidents:

- exact fingerprint clusters
- semantic similarity clusters
- service-level clusters
- node/fleet clusters
- release/change-window clusters

### Pattern-Aware RCA

AOP should explain recurrence honestly:

```text
This resembles 3 previous incidents in payments.
The strongest match was an OOMKilled checkout pod on 2026-08-10.
The previous resolution increased memory limits after validating heap growth.
Current evidence is missing container memory metrics, so confidence is limited.
```

### Trend Awareness

Future UI and reports should show:

- top recurring incident classes
- noisy namespaces or hosts
- services with repeated restarts
- node pools with repeated pressure
- incident count by week
- repeated evidence gaps
- fixes that repeatedly worked or failed

## Safety Boundaries

Pattern intelligence must not:

- treat historical similarity as proof
- invent missing evidence
- hide deterministic contradictions
- recommend destructive action without approval
- store secrets, tokens, private keys, or sensitive customer data

Similarity is a clue, not a conclusion.

## Implementation Sequence

1. Add deterministic incident fingerprint models.
2. Add fingerprint generation for Kubernetes incident classifications.
3. Add fingerprint generation for Linux investigation findings.
4. Store fingerprints with structured memory.
5. Add recurrence lookup across local incident history.
6. Add `aop memory patterns` CLI output.
7. Add pattern-aware evidence in RCA prompts.
8. Add runbook and ticket references.
9. Add dashboard panels for recurring patterns.

## Relation To RAG

RAG should retrieve only the relevant historical incidents, runbook sections,
and pattern summaries. It should not paste the whole memory store or all
runbooks into a prompt.

Pattern intelligence decides what is relevant before the LLM sees context.
