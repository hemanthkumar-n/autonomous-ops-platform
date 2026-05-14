from kubernetes import client, config

config.load_kube_config()

v1 = client.CoreV1Api()


def get_pod_events(
    pod_name,
    namespace
):
    """
    Fetch Kubernetes events related to a pod.
    """

    pod_events = []

    events = v1.list_namespaced_event(namespace)

    for event in events.items:

        if (
            event.involved_object
            and event.involved_object.name
            and pod_name in event.involved_object.name
        ):
            pod_events.append({
                "type": event.type,
                "reason": event.reason,
                "message": event.message
            })

    return pod_events


if __name__ == "__main__":

    events = get_pod_events(
        pod_name="memory-stress",
        namespace="ai-lab"
    )

    print(events)