

from kubernetes import client, config
import json

config.load_kube_config()

v1 = client.CoreV1Api()


def collect_incident_context(namespace="ai-lab"):

    pods = v1.list_namespaced_pod(namespace)

    incident_data = []

    for pod in pods.items:

        pod_info = {
            "pod_name": pod.metadata.name,
            "namespace": namespace,
            "phase": pod.status.phase,
            "node": pod.spec.node_name,
            "conditions": [],
            "container_states": [],
            "events": []
        }

        # Conditions
        if pod.status.conditions:
            for condition in pod.status.conditions:
                pod_info["conditions"].append({
                    "type": condition.type,
                    "status": condition.status
                })

        # Container states
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:

                state = "unknown"

                if container.state.waiting:
                    state = container.state.waiting.reason

                elif container.state.running:
                    state = "Running"

                elif container.state.terminated:
                    state = container.state.terminated.reason

                pod_info["container_states"].append({
                    "container": container.name,
                    "state": state
                })

        # Events
        events = v1.list_namespaced_event(namespace)

        for event in events.items:
            if pod.metadata.name in event.involved_object.name:

                pod_info["events"].append({
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message
                })

        incident_data.append(pod_info)

    return incident_data


if __name__ == "__main__":

    data = collect_incident_context()

    print(json.dumps(data, indent=2))


