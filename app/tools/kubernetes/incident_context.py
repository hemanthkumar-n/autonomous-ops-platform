from concurrent.futures import ThreadPoolExecutor
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.schemas.incident import (
    IncidentContext,
    PodCondition,
    ContainerState,
)
from app.tools.kubernetes.log_tools import get_pod_logs
from app.tools.kubernetes.event_tools import get_pod_events
from app.tools.prometheus.metrics_tools import get_pod_metrics

logger = get_logger(__name__)

EXCLUDED_NAMESPACES = {
    "kube-system",
    "kube-public",
    "kube-node-lease",
}

RESTART_THRESHOLD = 3
IO_WORKERS = 3


def _core_v1_api():
    """
    Build the Kubernetes client only when collection is requested.
    """

    try:
        config.load_kube_config()
    except ConfigException:
        config.load_incluster_config()

    return client.CoreV1Api()


def is_problematic_pod(pod) -> bool:
    """
    Detect unhealthy pods using production-safe heuristics.
    """

    if pod.metadata.namespace in EXCLUDED_NAMESPACES:
        return False

    if not pod.status.container_statuses:
        return False

    for container in pod.status.container_statuses:
        if container.state.waiting:
            return True

        if container.state.terminated:
            return True

        if (
            container.restart_count >= RESTART_THRESHOLD
            and not container.state.running
        ):
            return True

    return False


def collect_incident_context(
    namespace: str | None = None,
    pod_name: str | None = None,
) -> list[IncidentContext]:
    """
    Collect structured Kubernetes incident intelligence.
    """

    logger.info(
        "Collecting incident context namespace=%s pod_name=%s",
        namespace,
        pod_name,
    )

    v1 = _core_v1_api()

    if namespace:
        pods = v1.list_namespaced_pod(namespace)
    else:
        pods = v1.list_pod_for_all_namespaces()

    incident_data: list[IncidentContext] = []

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

        conditions = []

        if pod.status.conditions:
            for condition in pod.status.conditions:
                conditions.append(
                    PodCondition(
                        type=condition.type,
                        status=condition.status,
                    )
                )

        metrics = {}
        events = []
        pod_logs = ""

        with ThreadPoolExecutor(max_workers=IO_WORKERS) as executor:
            futures = {}

            if settings.ENABLE_METRICS_ENRICHMENT:
                futures["metrics"] = executor.submit(
                    get_pod_metrics,
                    pod_actual_name,
                    pod_namespace,
                )

            if settings.ENABLE_EVENT_COLLECTION:
                futures["events"] = executor.submit(
                    get_pod_events,
                    pod_actual_name,
                    pod_namespace,
                )

            if settings.ENABLE_POD_LOG_COLLECTION:
                futures["logs"] = executor.submit(
                    get_pod_logs,
                    pod_actual_name,
                    pod_namespace,
                    settings.MAX_LOG_LINES,
                )

            for signal_name, future in futures.items():
                try:
                    value = future.result()
                    if signal_name == "metrics":
                        metrics = value
                    elif signal_name == "events":
                        events = value
                    else:
                        pod_logs = value
                except Exception as exc:
                    logger.exception(
                        "%s collection failed pod=%s",
                        signal_name.capitalize(),
                        pod_actual_name,
                    )
                    if signal_name == "logs":
                        pod_logs = str(exc)

        container_states = []

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

            if container.last_state and container.last_state.terminated:
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
                    break

            container_states.append(
                ContainerState(
                    container=container.name,
                    state=state,
                    restart_count=restart_count,
                    last_termination=last_termination,
                    resources=resources,
                    logs=pod_logs,
                )
            )

        incident = IncidentContext(
            pod_name=pod_actual_name,
            namespace=pod_namespace,
            phase=pod.status.phase,
            node=pod.spec.node_name,
            conditions=conditions,
            container_states=container_states,
            events=events,
            metrics=metrics,
        )

        incident_data.append(incident)

    logger.info(
        "Incident context collection completed incidents=%s",
        len(incident_data),
    )

    return incident_data


if __name__ == "__main__":
    incidents = collect_incident_context()

    if not incidents:
        print("No incidents detected.")
        raise SystemExit(0)

    for incident in incidents:
        print(incident.model_dump_json(indent=2))
