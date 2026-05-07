from kubernetes import client, config

config.load_kube_config()

v1 = client.CoreV1Api()


def get_pods(namespace="default"):
    pods = v1.list_namespaced_pod(namespace)

    for pod in pods.items:
        print(f"Pod: {pod.metadata.name}")

        print(f"Pod Phase: {pod.status.phase}")

        if pod.status.container_statuses:
            for container in pod.status.container_statuses:

                waiting_state = (
                    container.state.waiting.reason
                    if container.state.waiting
                    else "Running"
                )

                print(f"Container State: {waiting_state}")

        print("-" * 50)


if __name__ == "__main__":
    get_pods("ai-lab")