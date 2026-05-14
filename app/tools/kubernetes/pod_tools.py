from kubernetes import client, config
from app.config.logging_config import get_logger
logger = get_logger(__name__)

config.load_kube_config()

v1 = client.CoreV1Api()


def get_pods(namespace="default"):
    pods = v1.list_namespaced_pod(namespace)

    for pod in pods.items:
        logger.info(f"Pod: {pod.metadata.name}")

        logger.info(f"Pod Phase: {pod.status.phase}")

        if pod.status.container_statuses:
            for container in pod.status.container_statuses:

                waiting_state = (
                    container.state.waiting.reason
                    if container.state.waiting
                    else "Running"
                )

                logger.info(f"Container State: {waiting_state}")

        logger.info("-" * 50)


if __name__ == "__main__":
    get_pods("*")
