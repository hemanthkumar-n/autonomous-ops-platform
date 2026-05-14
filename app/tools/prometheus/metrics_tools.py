from app.tools.prometheus.prometheus_client import query_prometheus
from app.tools.prometheus.queries import (
    memory_usage_query,
    cpu_usage_query,
    restart_count_query
)


def extract_metric_value(result):
    """
    Extract numeric value from Prometheus response.
    """

    if not result:
        return None

    try:
        return float(result[0]["value"][1])
    except Exception:
        return None


def get_pod_metrics(pod_name, namespace):
    """
    Collect Prometheus metrics for a specific pod.
    """

    memory_result = query_prometheus(
        memory_usage_query(pod_name, namespace)
    )

    cpu_result = query_prometheus(
        cpu_usage_query(pod_name, namespace)
    )

    restart_result = query_prometheus(
        restart_count_query(pod_name, namespace)
    )

    return {
        "memory_usage_bytes": extract_metric_value(memory_result),
        "cpu_usage": extract_metric_value(cpu_result),
        "restart_metric": extract_metric_value(restart_result)
    }


if __name__ == "__main__":
    pod_name = input("Enter pod name: ").strip()
    namespace = input("Enter namespace: ").strip()

    metrics = get_pod_metrics(
        pod_name=pod_name,
        namespace=namespace
    )

    print(metrics)