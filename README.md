# Autonomous Ops Platform

AI-powered SRE and DevOps automation platform focused on Kubernetes troubleshooting, observability, Linux operations, incident analysis, and intelligent operational workflows.

## Goals

- AI-assisted Kubernetes troubleshooting
- Linux operational automation
- Observability intelligence
- Incident RCA automation
- Multi-agent operational workflows
- Autonomous remediation research


autonomous-ops-platform/
│
├── app/
│   │
│   ├── agents/
│   │   │
│   │   ├── base/
│   │   │   ├── base_agent.py
│   │   │   ├── memory_manager.py
│   │   │   ├── context_manager.py
│   │   │   └── agent_registry.py
│   │   │
│   │   ├── sre/
│   │   │   ├── incident_agent.py
│   │   │   ├── remediation_agent.py
│   │   │   ├── rca_agent.py
│   │   │   ├── alert_agent.py
│   │   │   └── healthcheck_agent.py
│   │   │
│   │   ├── kubernetes/
│   │   │   ├── kube_agent.py
│   │   │   ├── deployment_agent.py
│   │   │   ├── pod_agent.py
│   │   │   ├── namespace_agent.py
│   │   │   └── ingress_agent.py
│   │   │
│   │   ├── linux/
│   │   │   ├── linux_agent.py
│   │   │   ├── process_agent.py
│   │   │   ├── disk_agent.py
│   │   │   ├── memory_agent.py
│   │   │   ├── network_agent.py
│   │   │   └── patching_agent.py
│   │   │
│   │   ├── observability/
│   │   │   ├── splunk_agent.py
│   │   │   ├── datadog_agent.py
│   │   │   ├── prometheus_agent.py
│   │   │   ├── grafana_agent.py
│   │   │   ├── newrelic_agent.py
│   │   │   └── dynatrace_agent.py
│   │   │
│   │   ├── devops/
│   │   │   ├── cicd_agent.py
│   │   │   ├── jenkins_agent.py
│   │   │   ├── github_agent.py
│   │   │   ├── terraform_agent.py
│   │   │   ├── docker_agent.py
│   │   │   └── release_agent.py
│   │   │
│   │   ├── cloud/
│   │   │   ├── aws_agent.py
│   │   │   ├── azure_agent.py
│   │   │   ├── cost_agent.py
│   │   │   ├── iam_agent.py
│   │   │   └── backup_agent.py
│   │   │
│   │   ├── security/
│   │   │   ├── vuln_agent.py
│   │   │   ├── compliance_agent.py
│   │   │   ├── qradar_agent.py
│   │   │   ├── wazuh_agent.py
│   │   │   └── secrets_agent.py
│   │   │
│   │   └── future/
│   │
│   ├── tools/
│   │   │
│   │   ├── kubernetes/
│   │   │   ├── pod_tools.py
│   │   │   ├── deployment_tools.py
│   │   │   ├── event_tools.py
│   │   │   ├── log_tools.py
│   │   │   ├── namespace_tools.py
│   │   │   └── metrics_tools.py
│   │   │
│   │   ├── linux/
│   │   │   ├── shell_tools.py
│   │   │   ├── process_tools.py
│   │   │   ├── disk_tools.py
│   │   │   ├── network_tools.py
│   │   │   └── service_tools.py
│   │   │
│   │   ├── splunk/
│   │   │   ├── splunk_search.py
│   │   │   ├── splunk_alerts.py
│   │   │   └── splunk_dashboards.py
│   │   │
│   │   ├── datadog/
│   │   │   ├── datadog_metrics.py
│   │   │   ├── datadog_alerts.py
│   │   │   └── datadog_events.py
│   │   │
│   │   ├── prometheus/
│   │   │   ├── prometheus_queries.py
│   │   │   ├── alert_rules.py
│   │   │   └── metrics_parser.py
│   │   │
│   │   ├── grafana/
│   │   │   ├── dashboard_tools.py
│   │   │   └── datasource_tools.py
│   │   │
│   │   ├── aws/
│   │   ├── terraform/
│   │   ├── jenkins/
│   │   ├── github/
│   │   ├── docker/
│   │   ├── slack/
│   │   └── common/
│   │
│   ├── llm/
│   │   ├── openai/
│   │   ├── claude/
│   │   ├── ollama/
│   │   ├── gemini/
│   │   ├── embeddings/
│   │   └── router.py
│   │
│   ├── orchestration/
│   │   ├── workflows/
│   │   ├── planners/
│   │   ├── execution_engine.py
│   │   ├── task_manager.py
│   │   ├── langgraph/
│   │   ├── crewai/
│   │   └── autogen/
│   │
│   ├── memory/
│   │   ├── vectorstore/
│   │   ├── embeddings/
│   │   ├── incident_history/
│   │   ├── runbooks/
│   │   └── knowledgebase/
│   │
│   ├── prompts/
│   │   ├── sre/
│   │   ├── kubernetes/
│   │   ├── linux/
│   │   ├── observability/
│   │   ├── security/
│   │   └── shared/
│   │
│   ├── api/
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── schemas/
│   │
│   ├── config/
│   │   ├── settings.py
│   │   ├── logging_config.py
│   │   └── constants.py
│   │
│   └── main.py
│
├── kubernetes/
│   ├── broken_apps/
│   ├── incidents/
│   │   ├── crashloop/
│   │   ├── oomkilled/
│   │   ├── imagepull/
│   │   ├── dns/
│   │   └── probes/
│   │
│   ├── manifests/
│   ├── monitoring/
│   ├── ingress/
│   └── helm/
│
├── infra/
│   ├── terraform/
│   ├── docker/
│   ├── aws/
│   └── monitoring/
│
├── docs/
│   ├── architecture/
│   ├── incidents/
│   ├── runbooks/
│   ├── ai-agents/
│   └── demos/
│
├── scripts/
│
├── tests/
│
├── screenshots/
│
├── .env
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── Makefile
├── setup.sh
└── README.md