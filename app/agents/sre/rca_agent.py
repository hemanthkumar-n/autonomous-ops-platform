import json
import requests

from app.tools.kubernetes.incident_context import collect_incident_context
from app.agents.sre.incident_classifier import classify_incident

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:latest"


def generate_rca(incident_context, classified_incidents):
    """
    Generate observability-aware AI RCA.
    """

    prompt = f"""
You are a senior Site Reliability Engineer specializing in Kubernetes incident response.

Analyze the incidents using ALL available operational signals.

Signal sources include:
- Kubernetes pod lifecycle state
- container runtime state
- restart counts
- last termination reasons
- resource requests and limits
- Kubernetes events
- container logs
- Prometheus observability metrics
    - memory usage
    - CPU usage
    - restart telemetry

Your responsibilities:

1. Identify the most likely root cause
2. Correlate Kubernetes runtime signals with Prometheus telemetry
3. Detect restart storms
4. Detect memory pressure / exhaustion
5. Detect image pull failures
6. Detect configuration failures
7. Assess severity
8. Recommend ownership team
9. Suggest preventive engineering actions

Output format:

### Incident Summary
### Root Cause Analysis
### Signal Correlation
### Severity Assessment
### Team Ownership Recommendation
### Preventive Recommendations

Incident Classification:
{json.dumps(classified_incidents, indent=2)}

Incident Context:
{json.dumps(incident_context, indent=2)}
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


def main():
    """
    RCA execution workflow.
    """

    print("\nCollecting incident context...\n")

    incident_context = collect_incident_context()

    if not incident_context:
        print("No incidents detected.")
        return

    print("Classifying incidents...\n")

    classified_incidents = classify_incident(incident_context)

    print("Generating observability-aware RCA...\n")

    rca_output = generate_rca(
        incident_context=incident_context,
        classified_incidents=classified_incidents
    )

    print("\n===== AI RCA OUTPUT =====\n")
    print(rca_output)


if __name__ == "__main__":
    main()