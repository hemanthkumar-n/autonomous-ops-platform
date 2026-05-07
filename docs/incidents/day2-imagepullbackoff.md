

# Day 2 - Kubernetes ImagePullBackOff Incident Analysis

---

# Objective

The objective of Day 2 was to build the first AI-assisted Kubernetes troubleshooting workflow using:

- Kubernetes Python SDK
- Structured incident context collection
- Ollama local LLM
- AI-generated RCA workflows

---

# Incident Type

## ImagePullBackOff

The incident was intentionally generated to simulate a common Kubernetes operational failure scenario.

---

# Incident Architecture Workflow

```text
Broken Kubernetes Deployment
        ↓
Kubernetes Cluster
        ↓
Kubernetes Python SDK
        ↓
Incident Context Collector
        ↓
Structured JSON Context
        ↓
Ollama AI Analysis
        ↓
RCA + Remediation Guidance
```

---

# Broken Deployment Manifest

File:

```text
kubernetes/incidents/imagepull/broken-nginx.yaml
```

Configuration:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-nginx
  namespace: ai-lab

spec:
  replicas: 1

  selector:
    matchLabels:
      app: broken-nginx

  template:
    metadata:
      labels:
        app: broken-nginx

    spec:
      containers:
      - name: nginx
        image: nginx:doesnotexist
```

---

# Deployment Execution

## Create Namespace

```bash
kubectl create namespace ai-lab
```

## Apply Deployment

```bash
kubectl apply -f kubernetes/incidents/imagepull/broken-nginx.yaml
```

---

# Incident Verification

## Pod Status

```bash
kubectl get pods -n ai-lab
```

Output:

```text
NAME                            READY   STATUS             RESTARTS   AGE
broken-nginx-5fc7d9ddf8-kqbv5   0/1     ImagePullBackOff   0          7m45s
```

---

# Event Analysis

## Kubernetes Events

```bash
kubectl describe pod -n ai-lab
```

Important events:

```text
Failed to pull image "nginx:doesnotexist"
ErrImagePull
ImagePullBackOff
Back-off pulling image
```

---

# Important Operational Learning

## Pod Phase vs Container State

### Pod Phase

```text
Pending
```

### Container State

```text
ImagePullBackOff
```

This was an important architectural discovery.

Kubernetes AI systems should inspect:
- container states
- pod conditions
- events
- deployment metadata

instead of relying only on:
```python
pod.status.phase
```

---

# Kubernetes Python SDK Integration

## Pod Tool

Implemented:
```text
app/tools/kubernetes/pod_tools.py
```

Capabilities:
- pod retrieval
- pod phase inspection
- container state inspection

---

## Event Tool

Implemented:
```text
app/tools/kubernetes/event_tools.py
```

Capabilities:
- Kubernetes event retrieval
- operational event parsing
- troubleshooting signal extraction

---

# Incident Context Collector

Implemented:
```text
app/tools/kubernetes/incident_context.py
```

Purpose:
- normalize operational data
- structure Kubernetes incident context
- improve AI reasoning quality

Collected:
- pod metadata
- pod phase
- node information
- container states
- pod conditions
- Kubernetes events

---

# AI RCA Workflow

Implemented:
```text
app/agents/sre/rca_agent.py
```

The workflow:
- collected structured incident context
- converted operational data to JSON
- sent normalized context to Ollama
- generated AI-assisted RCA

---

# AI RCA Output

Example analysis areas:
- incident summary
- root cause
- impact analysis
- severity assessment
- remediation guidance
- preventive measures

---

# Architectural Evolution

## Initial Workflow

```text
Events → Plain Text → LLM
```

## Improved Workflow

```text
Kubernetes
    ↓
Structured Incident Context
    ↓
Normalized JSON
    ↓
AI Reasoning
    ↓
RCA + Remediation
```

This significantly improved operational AI design quality.

---

# Key Engineering Learnings

## 1. Operational Context Matters

AI troubleshooting quality depends heavily on:
- structured data
- normalized operational context
- metadata correlation

---

## 2. Kubernetes Operational Nuances

Pod phase alone is insufficient for troubleshooting.

Container state analysis is required.

---

## 3. Modular Architecture Importance

Separating:
- tooling
- context collection
- AI reasoning

creates scalable operational AI architecture.

---

# Future Improvements

## Planned Enhancements

- OOMKilled incident analysis
- Prometheus metrics integration
- log correlation
- remediation recommendation engine
- Jira incident integration
- Confluence runbook ingestion
- operational dashboards
- historical incident correlation

---

# Screenshots

Add:
- kubectl outputs
- AI RCA output
- repository structure
- incident workflow diagrams

Location:
```text
screenshots/
```

---

# Day 2 Summary

Day 2 successfully established the first operational AI troubleshooting workflow capable of:

- collecting Kubernetes operational context
- normalizing incident intelligence
- integrating local LLM reasoning
- generating AI-assisted RCA workflows

This established the foundation for future enterprise-grade AI-SRE automation systems.

