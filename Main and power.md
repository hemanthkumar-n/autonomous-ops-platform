# Autonomous Ops Platform (AOP)

AI-native operational intelligence platform for Linux, Kubernetes, AWS, and DevOps troubleshooting.

---

# Vision

Autonomous Ops Platform (AOP) is designed to reduce operational cognitive load for SRE and DevOps teams through:

- operational evidence collection
- deterministic troubleshooting
- AI-assisted RCA
- runbook generation
- remediation planning
- incident memory
- future autonomous workflows

The project is inspired by real-world SRE operational experience across:
- Linux
- AWS
- Kubernetes
- Terraform
- observability
- incident management

---

# Core Philosophy

AOP is NOT:
- a chatbot wrapper
- a Kubernetes-only tool
- an AI demo project

AOP is intended to become:
# an operational intelligence runtime.

---

# Current Focus

The current implementation focuses on:

- Kubernetes evidence collection
- Linux operational diagnostics
- structured RCA generation
- command-driven workflows
- local LLM integration using Ollama

---

# Architecture

text Commands ↓ Collectors ↓ Evidence ↓ Detectors ↓ Reasoning ↓ RCA ↓ Remediation Suggestions 

---

# Repository Structure

text autonomous-ops-platform/  ├── app/ │ │   ├── cli/ │   │ │   ├── core/ │   │   ├── context/ │   │   ├── evidence/ │   │   ├── reasoning/ │   │   ├── remediation/ │   │   └── utils/ │   │ │   ├── domains/ │   │   ├── linux/ │   │   ├── kubernetes/ │   │   ├── aws/ │   │   ├── terraform/ │   │   └── observability/ │   │ │   ├── llm/ │   │ │   ├── memory/ │   │ │   └── integrations/ │ ├── docs/ ├── tests/ ├── scripts/ └── output/ 

---

# Example Commands

bash aop investigate k8s --namespace payments aop diagnose linux --host prod-app-01 aop investigate aws --service ec2 aop explain terraform --plan tfplan.json aop remediate k8s --issue oomkilled --dry-run 

---

# Initial MVP Goal

First milestone:

bash aop investigate k8s --namespace ai-lab --save 

The command should:
1. collect pod/events/logs
2. detect ImagePullBackOff, OOMKilled, CrashLoopBackOff
3. generate structured RCA
4. save markdown reports
5. suggest dry-run remediation

---

# Key Principles

- Evidence before AI reasoning
- Deterministic checks first
- Safe remediation only
- Real operational workflows
- Linux and AWS are first-class domains
- Kubernetes is the initial operational playground

---

# Long-Term Vision

text Signals ↓ Collectors ↓ Context ↓ Reasoning ↓ RCA ↓ Remediation ↓ Operational Memory ↓ Autonomous Operations 

---

# Status

Current Stage:
Early operational intelligence prototype.

Current Priority:
- collectors
- evidence models
- CLI workflows
- structured RCA
- Linux/Kubernetes operational intelligence

---

# Future Goals

- incident memory
- replay systems
- AWS operational intelligence
- Linux diagnostics engine
- Terraform explainability
- guarded autonomous remediation
- operational runbook generation

---

# Author

Built from real-world SRE operational experience with:
- Linux
- AWS
- Kubernetes
- DevOps
- observability
- incident management
- automation engineering