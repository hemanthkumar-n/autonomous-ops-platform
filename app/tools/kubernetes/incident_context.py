from kubernetes import client, config
from app.tools.kubernetes.log_tools import (
    get_pod_logs
)

import json

# Load Kubernetes configuration
config.load_kube_config()

# Kubernetes Core API
v1 = client.CoreV1Api()


def collect_incident_context(
    namespace=None,
    pod_name=None
):

    # Fetch pods
    if namespace:
        pods = v1.list_namespaced_pod(namespace)

    else:
        pods = v1.list_pod_for_all_namespaces()

    incident_data = []

    for pod in pods.items:

        # Filter specific pod if requested
        if pod_name and pod.metadata.name != pod_name:
            continue

        pod_info = {
            "pod_name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "phase": pod.status.phase,
            "node": pod.spec.node_name,
            "conditions": [],
            "container_states": [],
            "events": []
        }

        # ---------------------------------------------------
        # Pod Conditions
        # ---------------------------------------------------

        if pod.status.conditions:

            for condition in pod.status.conditions:

                pod_info["conditions"].append({
                    "type": condition.type,
                    "status": condition.status
                })

        # ---------------------------------------------------
        # Container States
        # ---------------------------------------------------

        if pod.status.container_statuses:

            for container in pod.status.container_statuses:

                state = "unknown"

                restart_count = container.restart_count

                last_termination = None

                resources = {}

                logs = ""

                # Current state
                if container.state.waiting:

                    state = container.state.waiting.reason

                elif container.state.running:

                    state = "Running"

                elif container.state.terminated:

                    state = container.state.terminated.reason

                # Previous termination details
                if container.last_state.terminated:

                    last_termination = {
                        "reason": (
                            container.last_state.terminated.reason
                        ),
                        "exit_code": (
                            container.last_state.terminated.exit_code
                        )
                    }

                # Resource limits and requests
                for spec_container in pod.spec.containers:

                    if spec_container.name == container.name:

                        if spec_container.resources:

                            resources = {
                                "limits": (
                                    spec_container.resources.limits
                                ),
                                "requests": (
                                    spec_container.resources.requests
                                )
                            }

                # Fetch logs
                try:

                    logs = get_pod_logs(
                        pod.metadata.name,
                        pod.metadata.namespace
                    )

                except Exception as e:

                    logs = str(e)

                # Append structured container data
                pod_info["container_states"].append({
                    "container": container.name,
                    "state": state,
                    "restart_count": restart_count,
                    "last_termination": last_termination,
                    "resources": resources,
                    "logs": logs
                })

        # ---------------------------------------------------
        # Kubernetes Events
        # ---------------------------------------------------

        events = v1.list_namespaced_event(
            pod.metadata.namespace
        )

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