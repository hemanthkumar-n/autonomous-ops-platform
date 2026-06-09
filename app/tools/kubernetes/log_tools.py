from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException


def get_pod_logs(
    pod_name,
    namespace,
    tail_lines=20
):
    """
    Fetch recent pod logs.

    Args:
        pod_name (str): Kubernetes pod name
        namespace (str): Kubernetes namespace
        tail_lines (int): Number of recent log lines

    Returns:
        str: Pod logs or normalized operational message
    """

    try:
        try:
            config.load_kube_config()
        except ConfigException:
            config.load_incluster_config()

        v1 = client.CoreV1Api()

        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines
        )

        return logs

    except ApiException as e:

        if e.status == 400:
            return "Container not started yet. Logs unavailable."

        return f"Kubernetes API error: {e}"

    except Exception as e:
        return f"Unexpected log retrieval error: {e}"


if __name__ == "__main__":

    pod_name = "memory-stress"
    namespace = "ai-lab"

    logs = get_pod_logs(
        pod_name=pod_name,
        namespace=namespace
    )

    print("\n===== POD LOGS =====\n")
    print(logs)
