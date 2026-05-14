from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Optional, Any

from app.tools.prometheus.prometheus_client import query_prometheus
from app.tools.prometheus.queries import (
    memory_usage_query,
    cpu_usage_query,
    restart_count_query,
)

logger = logging.getLogger(__name__)


@dataclass
class PodMetrics:
    memory_usage_bytes: Optional[float]
    cpu_usage: Optional[float]
    restart_metric: Optional[float]

    def to_dict(self) -> dict:
        return asdict(self)


def extract_metric_value(result: Any) -> Optional[float]:
    """
    Safely extract numeric metric value from Prometheus vector response.

    Expected shape:
    [
        {
            "metric": {...},
            "value": [timestamp, "123.45"]
        }
    ]
    """

    if not result:
        logger.warning("Prometheus returned empty result set")
        return None

    if not isinstance(result, list):
        logger.error("Unexpected Prometheus result type: %s", type(result))
        return None

    first = result[0]

    if not isinstance(first, dict):
        logger.error("Unexpected Prometheus result element type: %s", type(first))
        return None

    value = first.get("value")

    if not value or len(value) < 2:
        logger.error("Prometheus result missing 'value' payload: %s", first)
        return None

    try:
        return float(value[1])
    except (ValueError, TypeError) as exc:
        logger.exception("Failed converting Prometheus metric value: %s", exc)
        return None


def _fetch_metric(query: str, metric_name: str) -> Optional[float]:
    """
    Fetch and parse a single Prometheus metric.
    """

    logger.info("Querying Prometheus for metric=%s", metric_name)

    result = query_prometheus(query)

    metric_value = extract_metric_value(result)

    logger.info(
        "Prometheus metric fetched metric=%s value=%s",
        metric_name,
        metric_value,
    )

    return metric_value


def get_pod_metrics(pod_name: str, namespace: str) -> dict:
    """
    Collect Prometheus metrics for a pod in parallel.
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
                    "Metric collection failed for %s",
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    pod_name = input("Enter pod name: ").strip()
    namespace = input("Enter namespace: ").strip()

    metrics = get_pod_metrics(
        pod_name=pod_name,
        namespace=namespace,
    )

    print(metrics)