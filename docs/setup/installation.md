# Installation Guide

Setup instructions for running Autonomous Ops Platform locally.

---

## Prerequisites

Required:

- macOS / Linux / Windows (WSL recommended)
- Python 3.11+
- Git
- Docker Desktop
- Kubernetes enabled
- Ollama
- VS Code (recommended)

---

## Clone Repository

```bash
git clone https://github.com/hemanthkumar-n/autonomous-ops-platform.git
cd autonomous-ops-platform
```

---

## Python Virtual Environment

Create:

```bash
python3 -m venv venv
```

Activate:

macOS / Linux:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

## Install Dependencies

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

---

## Validate AOP CLI

```bash
aop --version
aop --help
aop health
aop kb --help
aop linux --help
```

The expected CLI version is:

```text
aop, version 0.10.0
```

---

## Docker Desktop

Install Docker Desktop.

Enable:

```text
Settings → Kubernetes → Enable Kubernetes
```

Verify:

```bash
kubectl cluster-info
```

Expected:

```text
Kubernetes control plane is running
```

---

## Kubernetes Validation

Check cluster:

```bash
kubectl get nodes
```

Expected:

```text
Ready
```

Check pods:

```bash
kubectl get pods -A
```

---

## Ollama Installation

Install:

macOS:

```bash
brew install ollama
```

Start:

```bash
ollama serve
```

---

## Pull Local AI Model

Recommended:

```bash
ollama pull qwen2.5-coder
ollama pull nomic-embed-text
```

Verify:

```bash
curl http://localhost:11434/api/tags
```

Expected:

```json
{
  "models": [...]
}
```

---

## Showcase Workflow

Create the sample namespace:

```bash
kubectl create namespace ai-lab
```

Apply one or both sample incidents:

```bash
kubectl apply -f kubernetes/incidents/imagepull/broken-nginx.yaml
kubectl apply -f kubernetes/incidents/oomkilled/oom-test.yaml
```

Run the investigation:

```bash
aop investigate k8s --namespace ai-lab
```

Fast SRE triage:

```bash
aop kb health -n ai-lab
aop kb po -n ai-lab
aop kb ev -n ai-lab
```

Export a presentation-ready Markdown report:

```bash
aop investigate k8s \
  --namespace ai-lab \
  --format markdown \
  --output reports/ai-lab-incident.md
```

Inspect learned incident memory:

```bash
aop memory search --namespace ai-lab
```

---

## Module Validation

### Log Tool

```bash
python -m app.tools.kubernetes.log_tools
```

---

### Event Tool

```bash
python -m app.tools.kubernetes.event_tools
```

---

### Incident Context Engine

```bash
python -m app.tools.kubernetes.incident_context
```

---

### AI RCA Engine

```bash
python -m app.agents.sre.rca_agent
```

---

## Generate Sample Kubernetes Incidents

### ImagePullBackOff

Apply:

```bash
kubectl apply -f kubernetes/incidents/imagepull/broken-nginx.yaml
```

Verify:

```bash
kubectl get pods -n ai-lab
```

Expected:

```text
ImagePullBackOff
```

---

### OOMKilled

Apply:

```bash
kubectl apply -f kubernetes/incidents/oomkilled/oom-test.yaml
```

Verify:

```bash
kubectl get pods -n ai-lab
```

Expected:

```text
OOMKilled
CrashLoopBackOff
```

---

## Common Troubleshooting

### pip not found

Use:

```bash
python3 -m pip install -r requirements.txt
```

---

### Kubernetes config issue

Verify:

```bash
kubectl config current-context
```

If missing:

Enable Kubernetes in Docker Desktop.

---

### Module import issue

Wrong:

```bash
python app/agents/sre/rca_agent.py
```

Correct:

```bash
python -m app.agents.sre.rca_agent
```

---

### Ollama connection issue

Check:

```bash
curl http://localhost:11434/api/tags
```

If failed:

```bash
ollama serve
```

---

### No pods visible

Check namespace:

```bash
kubectl get pods -A
```

or:

```bash
kubectl get pods -n ai-lab
```

---

## Development Workflow

Typical workflow:

1. generate incident
2. run `aop health`
3. run `aop investigate k8s`
4. inspect the generated RCA and remediation
5. export a Markdown report
6. query operational memory

Run offline regression tests:

```bash
python -m unittest discover -s tests -v
```

---

## Recommended Next Extensions

Suggested next implementations:

- incident recurrence and pattern intelligence
- approval-gated remediation execution
- richer deployment-level Kubernetes context
- Linux diagnostics
- AWS operational intelligence
- enterprise knowledge integrations

---

## Local Development Notes

Recommended tools:

- VS Code
- Python extension
- Docker Desktop
- Kubernetes CLI
- GitHub CLI (optional)

---

## Verification Checklist

Ensure:

- Python installed
- virtual environment active
- dependencies installed
- Docker Desktop running
- Kubernetes enabled
- kubectl working
- Ollama running
- model downloaded
- sample incidents deployed
- incident context generation working
- AI RCA working
- `aop --help` working
- offline regression tests passing
