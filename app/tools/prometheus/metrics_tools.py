from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Any

from app.config.logging_config import get_logger
from app.schemas.metrics import PodMetrics
from app.tools.prometheus.prometheus_client import query_prometheus
from app.tools.prometheus.queries import (
    memory_usage_query,
    cpu_usage_query,
    restart_count_query,
)

logger = get_logger(__name__)


def _empty_metrics() -> PodMetrics:
    """
    Default empty typed metrics contract.
    """

    return PodMetrics(
        memory_usage_bytes=None,
        cpu_usage=None,
        restart_metric=None,
    )


def extract_metric_value(result: Any) -> Optional[float]:
    """
    Extract numeric metric value from Prometheus vector response.
    """

    if not result:
        return None

    if not isinstance(result, list):
        logger.warning("Unexpected Prometheus result type=%s", type(result))
        return None

    first = result[0]

    if not isinstance(first, dict):
        logger.warning(
            "Unexpected Prometheus metric payload type=%s",
            type(first),
        )
        return None

    value = first.get("value")

    if not value or len(value) < 2:
        logger.warning("Missing Prometheus metric value payload")
        return None

    try:
        return float(value[1])

    except (TypeError, ValueError):
        logger.exception("Failed parsing Prometheus metric value")
        return None


def _fetch_metric(query: str, metric_name: str) -> Optional[float]:
    """
    Fetch a single Prometheus metric safely.
    """

    logger.info("Querying Prometheus metric=%s", metric_name)

    try:
        raw_result = query_prometheus(query)

        metric_value = extract_metric_value(raw_result)

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


def get_pod_metrics(pod_name: str, namespace: str) -> PodMetrics:
    """
    Collect Prometheus metrics for a Kubernetes pod in parallel.
    Returns typed schema contract.
    """

    if not pod_name:
        logger.warning("Missing pod_name for Prometheus enrichment")
        return _empty_metrics()

    if not namespace:
        logger.warning("Missing namespace for Prometheus enrichment")
        return _empty_metrics()

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

    logger.info(
        "Prometheus metrics contract created pod=%s namespace=%s",
        pod_name,
        namespace,
    )

    return metrics


if __name__ == "__main__":
    from app.tools.kubernetes.incident_context import collect_incident_context

    incidents = collect_incident_context()

    if not incidents:
        print("No incidents detected.")
        raise SystemExit(0)

    for incident in incidents:
        print(
            f"\nFetching metrics for "
            f"{incident['namespace']}/{incident['pod_name']}"
        )

        metrics = get_pod_metrics(
            pod_name=incident["pod_name"],
            namespace=incident["namespace"],
        )

        print(metrics.model_dump())