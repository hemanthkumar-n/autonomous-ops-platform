from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

SYSTEM_NAMESPACES = {
    "kube-system",
    "kube-public",
    "kube-node-lease",
}


def load_clients() -> tuple[client.CoreV1Api, client.VersionApi]:
    """
    Load Kubernetes clients from kubeconfig or in-cluster configuration.
    """

    try:
        config.load_kube_config()
    except ConfigException:
        config.load_incluster_config()

    return client.CoreV1Api(), client.VersionApi()


def load_apps_client() -> client.AppsV1Api:
    """
    Load the Kubernetes workload API client.
    """

    try:
        config.load_kube_config()
    except ConfigException:
        config.load_incluster_config()

    return client.AppsV1Api()


def _container_state(status: Any) -> tuple[str, str | None]:
    state = status.state

    if state.waiting:
        return state.waiting.reason or "Waiting", state.waiting.message

    if state.terminated:
        return (
            state.terminated.reason or "Terminated",
            state.terminated.message,
        )

    if state.running:
        return "Running", None

    return "Unknown", None


def _pod_ready(pod: Any) -> bool:
    statuses = pod.status.container_statuses or []
    return bool(statuses) and all(status.ready for status in statuses)


def _pod_status(pod: Any) -> str:
    statuses = pod.status.container_statuses or []

    for status in statuses:
        state, _ = _container_state(status)
        if state != "Running":
            return state

    return pod.status.phase or "Unknown"


def _pod_age(created_at: datetime | None) -> str:
    if created_at is None:
        return "-"

    now = datetime.now(timezone.utc)
    seconds = max(0, int((now - created_at).total_seconds()))

    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def list_pods(
    namespace: str | None = None,
    unhealthy_only: bool = False,
    include_system: bool = False,
) -> list[dict]:
    """
    Return normalized pod status records.
    """

    core, _ = load_clients()
    response = (
        core.list_namespaced_pod(namespace)
        if namespace
        else core.list_pod_for_all_namespaces()
    )
    records = []

    for pod in response.items:
        pod_namespace = pod.metadata.namespace

        if not include_system and pod_namespace in SYSTEM_NAMESPACES:
            continue

        statuses = pod.status.container_statuses or []
        ready_count = sum(1 for status in statuses if status.ready)
        restart_count = sum(status.restart_count for status in statuses)
        ready = _pod_ready(pod)
        status = _pod_status(pod)
        healthy = (
            pod.status.phase == "Succeeded"
            or (
                ready
                and status == "Running"
            )
        )

        if unhealthy_only and healthy:
            continue

        involved = event.involved_object
        object_kind = (
            involved.kind
            if involved and involved.kind
            else "Object"
        )
        object_name = (
            involved.name
            if involved and involved.name
            else "unknown"
        )

        records.append(
            {
                "namespace": pod_namespace,
                "pod": pod.metadata.name,
                "ready": f"{ready_count}/{len(statuses)}",
                "status": status,
                "restarts": restart_count,
                "node": pod.spec.node_name or "-",
                "age": _pod_age(pod.metadata.creation_timestamp),
                "healthy": healthy,
            }
        )

    return sorted(
        records,
        key=lambda item: (
            item["healthy"],
            item["namespace"],
            item["pod"],
        ),
    )


def cluster_health(
    namespace: str | None = None,
) -> dict:
    """
    Return a concise deterministic cluster health snapshot.
    """

    core, version_api = load_clients()
    version = version_api.get_code()
    nodes = core.list_node().items
    pods = list_pods(
        namespace=namespace,
        unhealthy_only=False,
    )

    ready_nodes = 0
    node_records = []

    for node in nodes:
        ready_condition = next(
            (
                condition
                for condition in node.status.conditions or []
                if condition.type == "Ready"
            ),
            None,
        )
        ready = bool(
            ready_condition
            and ready_condition.status == "True"
        )
        ready_nodes += int(ready)
        node_records.append(
            {
                "node": node.metadata.name,
                "ready": ready,
                "reason": (
                    ready_condition.reason
                    if ready_condition
                    else "Unknown"
                ),
            }
        )

    unhealthy = [
        pod
        for pod in pods
        if not pod["healthy"]
    ]

    return {
        "version": version.git_version,
        "namespace": namespace or "all non-system namespaces",
        "nodes": {
            "ready": ready_nodes,
            "total": len(nodes),
            "items": node_records,
        },
        "pods": {
            "healthy": len(pods) - len(unhealthy),
            "unhealthy": len(unhealthy),
            "total": len(pods),
            "items": unhealthy,
        },
    }


def list_nodes() -> list[dict]:
    """
    Return normalized node readiness and capacity.
    """

    core, _ = load_clients()
    records = []

    for node in core.list_node().items:
        conditions = {
            condition.type: condition
            for condition in node.status.conditions or []
        }
        ready = conditions.get("Ready")
        pressure = [
            name
            for name in (
                "MemoryPressure",
                "DiskPressure",
                "PIDPressure",
                "NetworkUnavailable",
            )
            if conditions.get(name)
            and conditions[name].status == "True"
        ]
        capacity = node.status.capacity or {}

        records.append(
            {
                "node": node.metadata.name,
                "ready": bool(
                    ready
                    and ready.status == "True"
                ),
                "pressure": ",".join(pressure) or "-",
                "cpu": capacity.get("cpu", "-"),
                "memory": capacity.get("memory", "-"),
                "pods": capacity.get("pods", "-"),
                "kubelet": (
                    node.status.node_info.kubelet_version
                    if node.status.node_info
                    else "-"
                ),
                "age": _pod_age(
                    node.metadata.creation_timestamp
                ),
            }
        )

    return sorted(
        records,
        key=lambda item: (
            item["ready"],
            item["node"],
        ),
    )


def list_namespaces() -> list[dict]:
    """
    Return namespace phase and age.
    """

    core, _ = load_clients()
    records = []

    for namespace in core.list_namespace().items:
        records.append(
            {
                "namespace": namespace.metadata.name,
                "phase": namespace.status.phase or "Unknown",
                "age": _pod_age(
                    namespace.metadata.creation_timestamp
                ),
            }
        )

    return sorted(
        records,
        key=lambda item: item["namespace"],
    )


def list_deployments(
    namespace: str | None = None,
) -> list[dict]:
    """
    Return deployment replica health.
    """

    apps = load_apps_client()
    response = (
        apps.list_namespaced_deployment(namespace)
        if namespace
        else apps.list_deployment_for_all_namespaces()
    )
    records = []

    for deployment in response.items:
        desired = deployment.spec.replicas or 0
        ready = deployment.status.ready_replicas or 0
        available = deployment.status.available_replicas or 0

        records.append(
            {
                "namespace": deployment.metadata.namespace,
                "deployment": deployment.metadata.name,
                "ready": f"{ready}/{desired}",
                "available": available,
                "updated": (
                    deployment.status.updated_replicas
                    or 0
                ),
                "healthy": ready == desired and available == desired,
                "age": _pod_age(
                    deployment.metadata.creation_timestamp
                ),
            }
        )

    return sorted(
        records,
        key=lambda item: (
            item["healthy"],
            item["namespace"],
            item["deployment"],
        ),
    )


def list_services(
    namespace: str | None = None,
) -> list[dict]:
    """
    Return service exposure and port information.
    """

    core, _ = load_clients()
    response = (
        core.list_namespaced_service(namespace)
        if namespace
        else core.list_service_for_all_namespaces()
    )
    records = []

    for service in response.items:
        ports = []
        for port in service.spec.ports or []:
            value = str(port.port)
            if port.target_port:
                value = f"{value}->{port.target_port}"
            if port.protocol:
                value = f"{value}/{port.protocol}"
            ports.append(value)

        ingress = []
        if (
            service.status.load_balancer
            and service.status.load_balancer.ingress
        ):
            for item in service.status.load_balancer.ingress:
                ingress.append(item.ip or item.hostname)

        records.append(
            {
                "namespace": service.metadata.namespace,
                "service": service.metadata.name,
                "type": service.spec.type,
                "cluster_ip": service.spec.cluster_ip or "-",
                "external": ",".join(ingress) or "-",
                "ports": ",".join(ports) or "-",
                "age": _pod_age(
                    service.metadata.creation_timestamp
                ),
            }
        )

    return sorted(
        records,
        key=lambda item: (
            item["namespace"],
            item["service"],
        ),
    )


def list_events(
    namespace: str | None = None,
    warnings_only: bool = True,
    limit: int = 20,
) -> list[dict]:
    """
    Return recent Kubernetes events.
    """

    core, _ = load_clients()
    response = (
        core.list_namespaced_event(namespace)
        if namespace
        else core.list_event_for_all_namespaces()
    )
    records = []

    for event in response.items:
        if warnings_only and event.type != "Warning":
            continue

        timestamp = (
            event.last_timestamp
            or event.event_time
            or event.metadata.creation_timestamp
        )
        records.append(
            {
                "namespace": event.metadata.namespace or "-",
                "type": event.type or "-",
                "reason": event.reason or "-",
                "object": f"{object_kind}/{object_name}",
                "message": event.message or "",
                "timestamp": (
                    timestamp.isoformat()
                    if timestamp
                    else ""
                ),
            }
        )

    records.sort(
        key=lambda item: item["timestamp"],
        reverse=True,
    )
    return records[:limit]


def get_logs(
    pod_name: str,
    namespace: str,
    container: str | None = None,
    tail_lines: int = 100,
    previous: bool = False,
) -> str:
    """
    Return bounded pod logs.
    """

    core, _ = load_clients()
    return core.read_namespaced_pod_log(
        name=pod_name,
        namespace=namespace,
        container=container,
        tail_lines=tail_lines,
        previous=previous,
        timestamps=True,
    )


def describe_pod(
    pod_name: str,
    namespace: str,
) -> dict:
    """
    Return a normalized troubleshooting view for one pod.
    """

    core, _ = load_clients()
    pod = core.read_namespaced_pod(
        name=pod_name,
        namespace=namespace,
    )
    events = list_events(
        namespace=namespace,
        warnings_only=False,
        limit=100,
    )
    pod_events = [
        event
        for event in events
        if event["object"].endswith(f"/{pod_name}")
    ][:20]
    containers = []

    for status in pod.status.container_statuses or []:
        state, message = _container_state(status)
        last_termination = None

        if status.last_state and status.last_state.terminated:
            terminated = status.last_state.terminated
            last_termination = {
                "reason": terminated.reason,
                "exit_code": terminated.exit_code,
                "finished_at": (
                    terminated.finished_at.isoformat()
                    if terminated.finished_at
                    else None
                ),
            }

        spec = next(
            (
                item
                for item in pod.spec.containers
                if item.name == status.name
            ),
            None,
        )

        containers.append(
            {
                "name": status.name,
                "ready": status.ready,
                "state": state,
                "message": message,
                "restarts": status.restart_count,
                "last_termination": last_termination,
                "image": spec.image if spec else None,
                "requests": (
                    spec.resources.requests
                    if spec and spec.resources
                    else None
                ),
                "limits": (
                    spec.resources.limits
                    if spec and spec.resources
                    else None
                ),
            }
        )

    return {
        "namespace": namespace,
        "pod": pod_name,
        "phase": pod.status.phase,
        "node": pod.spec.node_name,
        "pod_ip": pod.status.pod_ip,
        "host_ip": pod.status.host_ip,
        "created_at": (
            pod.metadata.creation_timestamp.isoformat()
            if pod.metadata.creation_timestamp
            else None
        ),
        "conditions": [
            {
                "type": condition.type,
                "status": condition.status,
                "reason": condition.reason,
                "message": condition.message,
            }
            for condition in pod.status.conditions or []
        ],
        "containers": containers,
        "events": pod_events,
    }
