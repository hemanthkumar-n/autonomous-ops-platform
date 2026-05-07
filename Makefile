run-rca:
	python -m app.agents.sre.rca_agent

run-context:
	python -m app.tools.kubernetes.incident_context

run-pods:
	python -m app.tools.kubernetes.pod_tools