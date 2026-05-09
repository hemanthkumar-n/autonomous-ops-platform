from app.tools.kubernetes.incident_context import v1


pods = v1.list_pod_for_all_namespaces()