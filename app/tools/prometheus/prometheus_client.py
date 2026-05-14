import logging
import requests
from app.config.settings import settings

logger = logging.getLogger(__name__)


def query_prometheus(promql_query: str):
    """
    Execute Prometheus instant query.

    Responsibility:
    - Transport only
    - Return raw Prometheus result list
    - No metric parsing here

    Returns:
        list[dict] | None
    """

    endpoint = f"{settings.PROMETHEUS_URL}/api/v1/query"

    try:
        response = requests.get(
            endpoint,
            params={"query": promql_query},
            timeout=settings.PROMETHEUS_TIMEOUT
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("status") != "success":
            logger.error(
                "Prometheus returned unsuccessful response: %s",
                payload
            )
            return None

        return payload.get("data", {}).get("result", [])

    except requests.exceptions.RequestException as error:
        logger.error("Prometheus query failed: %s", error)
        return None

    except (KeyError, ValueError, TypeError) as error:
        logger.error("Prometheus response parsing failed: %s", error)
        return None


if __name__ == "__main__":
    result = query_prometheus("up")

    print(result)