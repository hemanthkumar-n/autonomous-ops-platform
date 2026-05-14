import requests

PROMETHEUS_URL = "http://localhost:9090"


def query_prometheus(promql_query):
    """
    Execute PromQL query against Prometheus.
    """

    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql_query},
            timeout=10
        )

        response.raise_for_status()

        result = response.json()

        if result["status"] != "success":
            return None

        return result["data"]["result"]

    except Exception as error:
        print(f"Prometheus query failed: {error}")
        return None