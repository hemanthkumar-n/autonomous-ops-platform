import json
import requests

from app.tools.kubernetes.incident_context import collect_incident_context
from app.agents.sre.incident_classifier import classify_incident

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:latest"


def generate_remediation(single_incident, full_context):
    """
    Generate remediation plan for one incident only.
    """

    prompt = f"""
You are a senior Site Reliability Engineer responsible for SAFE incident remediation.

Analyze ONE incident only.

Use all available operational signals.

Available signals:
- Kubernetes pod lifecycle state
- container runtime state
- restart counts
- last termination reasons
- resource requests and limits
- Kubernetes events
- container logs
- Prometheus metrics
    - memory usage
    - CPU usage
    - restart telemetry

Your responsibilities:

1. Recommend SAFE remediation steps
2. Avoid destructive actions
3. Recommend Kubernetes validation commands
4. Suggest rollback or escalation where appropriate
5. Correlate remediation with incident type

Incident handling guidance:

ImagePullFailure:
- validate image tag
- validate registry access
- validate deployment spec
- validate imagePullSecrets

MemoryExhaustion:
- validate memory pressure
- compare limits vs workload demand
- inspect restart storms
- inspect capacity constraints
- recommend resource tuning

CrashLoopBackOff:
- inspect startup logs
- inspect probes
- inspect dependency failures
- inspect config changes

FailedScheduling:
- inspect node capacity
- inspect taints / tolerations
- inspect quota constraints

Output format:

### Incident
### Immediate Safe Actions
### Kubernetes Validation Commands
### Escalation Recommendation
### Preventive Recommendations
### Risk Notes

Incident Classification:
{json.dumps(single_incident, indent=2)}

Relevant Incident Context:
{json.dumps(full_context, indent=2)}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    return result["response"]


def map_incident_context(incident_context):
    """
    Map pod name -> incident context.
    """

    context_map = {}

    for incident in incident_context:
        context_map[incident["pod_name"]] = incident

    return context_map


def generate_all_remediations(classified_incidents, incident_context):
    """
    Generate remediation per incident.
    """

    context_map = map_incident_context(incident_context)

    remediation_results = []

    for incident in classified_incidents:
        pod_name = incident["pod_name"]

        relevant_context = context_map.get(pod_name, {})

        print(f"Generating remediation for: {pod_name}")

        remediation = generate_remediation(
            single_incident=incident,
            full_context=relevant_context
        )

        remediation_results.append({
            "pod_name": pod_name,
            "incident_type": incident["incident_type"],
            "remediation": remediation
        })

    return remediation_results


def main():
    """
    Remediation execution workflow.
    """

    print("\nCollecting incident context...\n")

    incident_context = collect_incident_context()

    if not incident_context:
        print("No incidents detected.")
        return

    print("Classifying incidents...\n")

    classified_incidents = classify_incident(incident_context)

    print("Generating incident-by-incident remediation plans...\n")

    remediation_results = generate_all_remediations(
        classified_incidents=classified_incidents,
        incident_context=incident_context
    )

    print("\n===== REMEDIATION OUTPUT =====\n")

    for result in remediation_results:
        print("=" * 80)
        print(f"Pod: {result['pod_name']}")
        print(f"Incident Type: {result['incident_type']}")
        print("=" * 80)
        print(result["remediation"])
        print("\n")


if __name__ == "__main__":
    main()