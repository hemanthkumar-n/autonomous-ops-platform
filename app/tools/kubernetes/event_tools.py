from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


def get_pod_events(
    pod_name,
    namespace
):
    """
    Fetch Kubernetes events related to a pod.
    """

    pod_events = []

    try:
        config.load_kube_config()
    except ConfigException:
        config.load_incluster_config()

    v1 = client.CoreV1Api()

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
