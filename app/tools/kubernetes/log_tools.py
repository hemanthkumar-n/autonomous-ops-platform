from kubernetes import client, config

config.load_kube_config()

v1 = client.CoreV1Api()


def get_pod_logs(
    pod_name,
    namespace="none",
    tail_lines=50
):

    logs = v1.read_namespaced_pod_log(
        name=pod_name,
        namespace=namespace,
        tail_lines=tail_lines
    )

    return logs


if __name__ == "__main__":

    pod_name = "memory-stress"

    logs = get_pod_logs(pod_name)

    print("\n===== POD LOGS =====\n")

    print(logs)
