# Enterprise Platform Evolution

This document restores the original enterprise platform direction while
aligning it with the current AOP v0.33 implementation.

AOP is not intended to remain a command collection. The CLI is the first
operator surface for a larger operational intelligence platform.

## Evolution Path

```text
Reactive Operations
  -> AI-Assisted Incident Response
  -> Operational Learning Platform
  -> Autonomous Operational Intelligence
  -> Safe Self-Healing Platform Engineering
```

The current codebase is between the second and third stages:

- Kubernetes incident workflows exist.
- Linux troubleshooting is now a first-class deterministic domain.
- Operational memory exists through structured JSON and Chroma.
- Provider routing and token-budget planning exist.
- Enterprise approval, UI, AWS, ticket, and chat integrations are still future
  tracks.

## Target Enterprise Architecture

```text
Linux Hosts          Kubernetes Clusters        AWS / Cloud
    |                       |                       |
    v                       v                       v
Read-Only Evidence   Runtime Evidence       Cloud Evidence
Collectors           Collectors             Adapters
    |                       |                       |
    +-----------+-----------+-----------+-----------+
                |
                v
        Unified Evidence Model
                |
                v
   Deterministic Detection And Correlation
                |
                v
       Canonical InvestigationCase
                |
        +-------+-------+
        |               |
        v               v
Structured Memory   Semantic / RAG Memory
        |               |
        +-------+-------+
                |
                v
      Token-Budget And Model Policy
                |
                v
      AI-Assisted RCA And Guidance
                |
                v
 CLI + UI + Slack/Teams + Ticket Systems
                |
                v
 Human Approval, Audit, Validation, Learning
```

## Original Platform Principles To Preserve

### Provider Abstraction

Core logic should not couple directly to vendor SDKs.

```text
agent -> abstraction -> provider implementation
```

This applies to:

- LLM providers
- embedding providers
- vector stores
- observability systems
- ticket systems
- chat systems
- cloud providers

### Memory-First Operational Intelligence

AOP should not reason from the current incident alone.

```text
current evidence
  + historical incidents
  + runbooks
  + semantic similarity
  + deterministic findings
  + AI reasoning
```

The future goal is organizational learning: AOP should explain when an issue
resembles previous failures, which fixes worked, which fixes failed, and what
evidence is still missing.

### Safe Autonomy

AOP should move toward automation only through explicit governance.

Required controls:

- read-only collection by default
- human approval before consequential action
- policy checks before execution
- validation after execution
- rollback or escalation plan
- audit trail for every recommendation and action

### Enterprise Portability

AOP should be deployable into a new company without rewriting the core.

Future onboarding should support:

- company identity and RBAC
- scoped secrets and credentials
- Kubernetes clusters
- Linux hosts
- AWS accounts
- observability systems
- Slack or Teams
- ticket systems
- runbooks and historical incidents
- service ownership and metadata

## Future Integration Tracks

### Observability

- Prometheus
- Grafana
- OpenTelemetry
- Splunk
- New Relic
- Datadog or similar providers when needed

### Cloud And Infrastructure

- AWS CloudWatch, CloudTrail, EC2, EBS, ELB/ALB, RDS, Lambda, EKS, IAM, VPC,
  Route 53, S3
- Terraform and infrastructure change context
- Jenkins and CI/CD failure context

### Collaboration And Workflow

- Slack
- Microsoft Teams
- Jira
- ServiceNow
- incident reports
- approvals and audit trail

### Agent Orchestration

LangGraph, AutoGen, or another orchestration framework should be introduced
only when AOP needs branching, resumability, approval pauses, retries across
tools, or multi-agent coordination that the current linear workflows cannot
express cleanly.

## What v0.33 Restores

The original README framed AOP as an enterprise AI operations platform. Recent
work rightly focused on Linux and Kubernetes implementation, but the platform
story became less visible.

v0.33 restores the strategic frame:

- platform evolution ladder
- enterprise architecture target
- phase-based roadmap
- incident pattern intelligence as a major next milestone
- runbook and organizational intelligence as first-class product tracks
- founder-led enterprise SRE positioning
