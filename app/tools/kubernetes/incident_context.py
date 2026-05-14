import json

from kubernetes import client, config

from app.config.logging_config import get_logger
from app.tools.kubernetes.log_tools import get_pod_logs
from app.tools.kubernetes.event_tools import get_pod_events
from app.tools.prometheus.metrics_tools import get_pod_metrics

logger = get_logger(__name__)

EXCLUDED_NAMESPACES = {
    "kube-system",
    "kube-public",
    "kube-node-lease",
}


def get_kubernetes_client():
    """
    Lazy Kubernetes client initialization.
    """

    config.load_kube_config()
    return client.CoreV1Api()


def is_problematic_pod(pod):
    """
    Identify unhealthy pods only.
    """

    if pod.metadata.namespace in EXCLUDED_NAMESPACES:
        return False

    if not pod.status.container_statuses:
        return False

    for container in pod.status.container_statuses:
        if container.restart_count > 0:
            return True

        if container.state.waiting:
            return True

        if container.state.terminated:
            return True

    return False


def collect_incident_context(namespace=None, pod_name=None):
    """
    Collect structured operational incident context.
    """

    logger.info(
        "Collecting incident context namespace=%s pod_name=%s",
        namespace,
        pod_name,
    )

    v1 = get_kubernetes_client()

    if namespace:
        pods = v1.list_namespaced_pod(namespace)

    else:
        pods = v1.list_pod_for_all_namespaces()

    incident_data = []

    for pod in pods.items:
        pod_namespace = pod.metadata.namespace
        pod_actual_name = pod.metadata.name

        if pod_name and pod_actual_name != pod_name:
            continue

        if not is_problematic_pod(pod):
            continue

        logger.info(
            "Processing problematic pod=%s namespace=%s",
            pod_actual_name,
            pod_namespace,
        )

        try:
            logs = get_pod_logs(
                pod_name=pod_actual_name,
                namespace=pod_namespace
            )
        except Exception:
            logger.exception(
                "Log collection failed pod=%s",
                pod_actual_name,
            )
            logs = ""

        try:
            events = get_pod_events(
                pod_name=pod_actual_name,
                namespace=pod_namespace
            )
        except Exception:
            logger.exception(
                "Event collection failed pod=%s",
                pod_actual_name,
            )
            events = []

        try:
            metrics = get_pod_metrics(
                pod_name=pod_actual_name,
                namespace=pod_namespace
            )
        except Exception:
            logger.exception(
                "Metrics enrichment failed pod=%s",
                pod_actual_name,
            )
            metrics = {}

        pod_info = {
            "pod_name": pod_actual_name,
            "namespace": pod_namespace,
            "phase": pod.status.phase,
            "node": pod.spec.node_name,
            "conditions": [],
            "container_states": [],
            "events": events,
            "metrics": metrics,
        }

        if pod.status.conditions:
            for condition in pod.status.conditions:
                pod_info["conditions"].append({
                    "type": condition.type,
                    "status": condition.status,
                })

        for container in pod.status.container_statuses:
            state = "unknown"
            restart_count = container.restart_count
            last_termination = None
            resources = {}

            if container.state.waiting:
                state = container.state.waiting.reason

            elif container.state.running:
                state = "Running"

            elif container.state.terminated:
                state = container.state.terminated.reason

            if container.last_state.terminated:
                last_termination = {
                    "reason": container.last_state.terminated.reason,
                    "exit_code": container.last_state.terminated.exit_code,
                }

            for spec_container in pod.spec.containers:
                if spec_container.name == container.name:
                    if spec_container.resources:
                        resources = {
                            "limits": spec_container.resources.limits,
                            "requests": spec_container.resources.requests,
                        }

            pod_info["container_states"].append({
                "container": container.name,
                "state": state,
                "restart_count": restart_count,
                "last_termination": last_termination,
                "resources": resources,
                "logs": logs,
            })

        incident_data.append(pod_info)

    logger.info(
        "Incident context collection completed incidents=%s",
        len(incident_data),
    )

    return incident_data


if __name__ == "__main__":
    data = collect_incident_context()
    print(json.dumps(data, indent=2))