def memory_usage_query(pod_name: str, namespace: str) -> str:
    """
    Memory usage query.
    Compatible with modern Kubernetes / cAdvisor.
    """

    return (
        f'container_memory_working_set_bytes'
        f'{{pod="{pod_name}",namespace="{namespace}"}}'
    )


def cpu_usage_query(pod_name: str, namespace: str) -> str:
    """
    CPU usage query.
    """

    return (
        f'rate(container_cpu_usage_seconds_total'
        f'{{pod="{pod_name}",namespace="{namespace}"}}[5m])'
    )


def restart_count_query(pod_name: str, namespace: str) -> str:
    """
    Restart count query.
    """

    return (
        f'kube_pod_container_status_restarts_total'
        f'{{pod="{pod_name}",namespace="{namespace}"}}'
    )