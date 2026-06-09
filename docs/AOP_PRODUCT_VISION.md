# Autonomous Ops Platform: Product Vision

Updated: 2026-06-09

This document preserves the founding product direction. It should change only
when the long-term vision changes, not during ordinary implementation work.

Related records:

- Current implementation memory:
  `docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md`
- Early vision notes: `Main and power.md`
- Full pre-compaction project memory:
  `git show 526bdbc:docs/AUTONOMOUS_OPS_PLATFORM_MEMORY_LANE.md`

## Founding Goal

Build one operational source of truth for SRE and platform teams.

AOP should connect infrastructure evidence, troubleshooting knowledge,
historical incidents, runbooks, human decisions, and remediation outcomes in
one system.

It is not intended to be:

- a chatbot wrapper
- a Kubernetes-only troubleshooting tool
- a collection of disconnected scripts
- an AI system that acts without human control

It is intended to become an operational intelligence platform that helps teams
observe, investigate, remember, decide, approve, act safely, and learn.

## Founder Context

The platform is grounded in extensive practical experience across:

- Linux administration and troubleshooting
- SRE and incident response
- Kubernetes and container platforms
- AWS and cloud operations
- observability
- DevOps and automation
- Terraform and infrastructure delivery

Linux knowledge is a core product advantage, not a secondary integration.
Future Linux diagnostics should capture real operational troubleshooting
patterns and lessons accumulated through the founder's career.

An authored Linux/Kubernetes troubleshooting criterion is preserved at:

```text
app/memory/knowledgebase/linkedin_kubernetes_linux_criteria.md
```

Its central product rule is that Kubernetes orchestration symptoms must be
correlated with relevant Linux node evidence before AOP reaches a cross-domain
conclusion.

## Product Domains

### Linux

Linux and Kubernetes are the first operational foundations.

Target Linux capabilities:

- CPU, memory, load, process, disk, filesystem, inode, and swap analysis
- service and systemd troubleshooting
- networking, DNS, routes, sockets, ports, and packet-level evidence
- kernel, boot, hardware, and OOM diagnostics
- permissions, users, SSH, certificates, and security signals
- package, patching, configuration, and dependency failures
- log and journal correlation
- application process and host-level performance analysis
- deterministic checks before AI interpretation
- reusable Linux runbooks and operational memory

Example direction:

```bash
aop diagnose linux --host prod-app-01
aop investigate linux --host prod-app-01 --issue high-load
```

### Kubernetes

Kubernetes is the current implemented proving ground.

Target capabilities include:

- pod, workload, node, event, log, and resource evidence
- ImagePullBackOff, OOMKilled, CrashLoopBackOff, probe, scheduling, and
  configuration diagnosis
- Prometheus correlation
- safe RCA and remediation guidance
- deployment, service, ingress, storage, and cluster-level intelligence

### AWS

AWS becomes the next major operational domain after Linux and Kubernetes are
stable.

Target capabilities:

- CloudWatch log and metric investigation
- EC2, EBS, ELB/ALB, Auto Scaling, RDS, Lambda, ECS/EKS, IAM, VPC, Route 53,
  and S3 troubleshooting
- CloudTrail and change correlation
- AWS Health and service-event context
- resource inventory and dependency mapping
- account, region, environment, and ownership context
- cost or capacity signals when relevant to incidents

Example direction:

```bash
aop investigate aws --service ec2 --region us-east-1
aop investigate aws --cloudwatch-log-group /aws/lambda/payments
```

## Human Confirmation

AOP should meet operators where they already work.

Slack and Microsoft Teams integrations should:

- publish incident summaries and evidence
- show severity, confidence, ownership, and recommended actions
- request confirmation before controlled remediation
- support approve, reject, defer, and escalate decisions
- record who approved an action and when
- publish execution and rollback results
- link back to the full incident record and UI

Target flow:

```text
incident detected
  -> evidence and RCA generated
  -> Slack/Teams notification
  -> human approval or rejection
  -> policy-checked execution
  -> validation and rollback if required
  -> outcome stored in operational memory
```

Chat integrations are approval and collaboration surfaces, not the source of
truth. The AOP incident record remains canonical.

## Unified UI

AOP needs a clear web interface for operators, engineering leaders, and new
companies evaluating the platform.

Initial UI should display:

- platform and integration health
- active Linux and Kubernetes incidents
- evidence timeline
- deterministic findings
- AI-generated RCA
- recommended remediation and risk
- approval status
- historical similar incidents
- runbooks and previous outcomes
- Markdown/JSON report download

Later views:

- AWS and cloud investigations
- fleet and cluster health
- recurring incident patterns
- operational knowledge search
- integration and credential administration
- RBAC, audit, policy, and approval management
- executive reliability and trend summaries

The UI should explain why a conclusion was reached. Evidence and deterministic
findings must remain visible beside AI reasoning.

## Company Onboarding Model

AOP should be installable inside a new company without rewriting the core.

Target onboarding:

1. Deploy AOP in the company's environment.
2. Configure identity, RBAC, secrets, and data boundaries.
3. Connect Linux hosts through an agent, SSH/bastion, or approved collector.
4. Connect Kubernetes clusters through kubeconfig or in-cluster service
   accounts.
5. Connect observability systems such as Prometheus and CloudWatch.
6. Connect AWS accounts through scoped IAM roles.
7. Connect Slack or Teams for incident collaboration and approvals.
8. Import runbooks, incident history, ownership data, and service metadata.
9. Run read-only validation before enabling any controlled actions.

Required enterprise characteristics:

- least-privilege access
- secrets stored outside source code
- tenant and environment separation
- configurable data retention
- complete audit trails
- policy-controlled actions
- read-only mode by default
- provider and integration adapters
- portable deployment using containers and Kubernetes

## System Direction

```text
Linux + Kubernetes + AWS + Observability + Runbooks + Incident History
                              |
                              v
                   Unified Evidence Model
                              |
                              v
            Deterministic Detection and Correlation
                              |
                              v
             Operational Memory and AI Reasoning
                              |
                              v
          UI + CLI + Slack/Teams Collaboration
                              |
                              v
              Human-Approved Safe Remediation
                              |
                              v
                    Validation and Learning
```

## Delivery Sequence

1. Stabilize and demonstrate Kubernetes investigation.
2. Build the Linux diagnostics foundation using real admin knowledge.
3. Add a UI for Linux and Kubernetes evidence, RCA, and memory.
4. Add Slack/Teams incident notification and approval workflows.
5. Add AWS evidence collection, CloudWatch analysis, and troubleshooting.
6. Add company onboarding, RBAC, secrets, audit, and deployment automation.
7. Add pattern intelligence and cross-domain correlation.
8. Add tightly governed remediation execution.

## Non-Negotiable Principles

- One canonical incident record.
- Evidence before AI.
- Deterministic troubleshooting before probabilistic reasoning.
- Linux and Kubernetes are first-class domains.
- Kubernetes symptoms must trigger Linux node correlation when the failure
  could originate from kernel, cgroup, process, filesystem, network, service,
  kubelet, or container-runtime behavior.
- Missing cross-domain evidence must be identified, not invented by AI.
- AWS is a first-class cloud domain.
- Human confirmation before consequential action.
- CLI, UI, and chat are interfaces to the same platform intelligence.
- Operational memory must preserve organizational learning.
- Every action must be explainable, auditable, and reversible where possible.
- New integrations must use stable adapters rather than coupling core logic to
  vendors.

## Long-Term Outcome

AOP should help a new company connect its operational systems and quickly gain:

- a shared SRE troubleshooting surface
- consistent Linux, Kubernetes, and AWS investigations
- reusable operational knowledge
- faster and more explainable incident response
- safe collaboration and approval workflows
- a path from assistance to governed autonomous operations
