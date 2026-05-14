def memory_usage_query(pod_name, namespace):
    """
    PromQL query for pod memory usage.
    """

    return (
        f'container_memory_usage_bytes'
        f'{{pod="{pod_name}",namespace="{namespace}"}}'
    )


def cpu_usage_query(pod_name, namespace):
    """
    PromQL query for pod CPU usage.
    """

    return (
        f'rate(container_cpu_usage_seconds_total'
        f'{{pod="{pod_name}",namespace="{namespace}"}}[5m])'
    )


def restart_count_query(pod_name, namespace):
    """
    PromQL query for restart count.
    """

    return (
        f'kube_pod_container_status_restarts_total'
        f'{{pod="{pod_name}",namespace="{namespace}"}}'
    )