# External Knowledge Ingestion

## Purpose

AOP can learn from public incident reports, vendor runbooks, company
postmortems, tickets, and knowledge systems. External content must retain
provenance and review state so an agent never turns an unverified story into a
confident production recommendation.

## Knowledge States

```text
metadata_only
  -> source_reviewed
  -> guidance_reviewed
  -> eligible_for_bounded_rag
```

`metadata_only` contains discovery fields such as title, URL, technology tags,
and impact. It must not enter RCA as a solution.

`source_reviewed` means the original source was read and reported facts were
captured with attribution.

`guidance_reviewed` means reusable checks were separated from historical or
version-specific workarounds and reviewed for safety.

Only `guidance_reviewed` content may become trusted runbook context.

## Required Provenance

Each external record needs:

- stable artifact ID
- source catalog and catalog URL
- canonical original URL
- source host
- title and publication year when available
- content scope and review state
- license status
- source checksum
- import timestamp on the catalog snapshot

## k8s.af Policy

k8s.af is imported as metadata only. AOP stores the index title, URL,
technology tags, impact, and year. Linked content is not copied.

The source snapshot is useful for questions such as:

- Which public incidents involved CoreDNS and OOM?
- Which stories involved conntrack, AWS CNI, or CPU throttling?
- What impacts were associated with node readiness or cluster upgrades?

It is not sufficient to answer:

- What was the verified root cause?
- Which command fixed the incident?
- Is the historical mitigation safe on the current Kubernetes version?

Those answers require original-source review.

## Safety Boundary

External metadata never authorizes command execution, remediation, SSH,
Kubernetes mutation, Linux mutation, or changes to cloud resources.
