# ADR-001: Prometheus Metrics Integrated Into Incident Context

Date: 2026-05-15
Status: Accepted

## Context

Prometheus metrics were originally fetched manually via metrics_tools.py CLI.

This created fragmented operational workflows and prevented unified incident reasoning.

## Decision

Prometheus metrics were integrated directly into incident_context.py.

Metrics are now auto-enriched per problematic pod.

## Alternatives Considered

1. Keep standalone Prometheus CLI tool
2. Fetch metrics inside RCA agent
3. Fetch metrics during context collection

## Decision Rationale

Context collection is the correct signal aggregation layer.

RCA/remediation should consume normalized context, not fetch infrastructure data.

## Operational Impact

Unified incident payload now includes:

- pod state
- events
- logs
- metrics

## Future Evolution

Metrics may later move to async enrichment pipelines.