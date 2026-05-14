from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Optional

from app.config.logging_config import get_logger
from app.tools.prometheus.prometheus_client import query_prometheus
from app.tools.prometheus.queries import (
    memory_usage_query,
    cpu_usage_query,
    restart_count_query,
)

logger = get_logger(__name__)


@dataclass
class PodMetrics:
    """
    Typed Prometheus metrics contract.
    """

    memory_usage_bytes: Optional[float]
    cpu_usage: Optional[float]
    restart_metric: Optional[float]

    def to_dict(self) -> dict:
        return asdict(self)


def _fetch_metric(query: str, metric_name: str) -> Optional[float]:
    """
    Fetch a single Prometheus metric safely.
    """

    logger.info("Querying Prometheus metric=%s", metric_name)

    try:
        metric_value = query_prometheus(query)

        logger.info(
            "Prometheus metric fetched metric=%s value=%s",
            metric_name,
            metric_value,
        )

        return metric_value

    except Exception:
        logger.exception(
            "Prometheus metric collection failed metric=%s",
            metric_name,
        )
        return None


def get_pod_metrics(pod_name: str, namespace: str) -> dict:
    """
    Collect Prometheus metrics for a Kubernetes pod in parallel.
    """

    if not pod_name.strip():
        raise ValueError("pod_name cannot be empty")

    if not namespace.strip():
        raise ValueError("namespace cannot be empty")

    queries = {
        "memory_usage_bytes": memory_usage_query(pod_name, namespace),
        "cpu_usage": cpu_usage_query(pod_name, namespace),
        "restart_metric": restart_count_query(pod_name, namespace),
    }

    results = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_map = {
            executor.submit(_fetch_metric, query, metric_name): metric_name
            for metric_name, query in queries.items()
        }

        for future in as_completed(future_map):
            metric_name = future_map[future]

            try:
                results[metric_name] = future.result()
            except Exception:
                logger.exception(
                    "Parallel metric execution failed metric=%s",
                    metric_name,
                )
                results[metric_name] = None

    metrics = PodMetrics(
        memory_usage_bytes=results.get("memory_usage_bytes"),
        cpu_usage=results.get("cpu_usage"),
        restart_metric=results.get("restart_metric"),
    )

    return metrics.to_dict()


if __name__ == "__main__":
    pod_name = input("Enter pod name: ").strip()
    namespace = input("Enter namespace: ").strip()

    metrics = get_pod_metrics(
        pod_name=pod_name,
        namespace=namespace,
    )

    print(metrics)
