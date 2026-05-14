import json
import requests

from app.tools.kubernetes.incident_context import collect_incident_context
from app.agents.sre.incident_classifier import classify_incident

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:latest"


def generate_rca(incident_context, classified_incidents):
    """
    Generate RCA using incident context + incident intelligence.
    """

    prompt = f"""
You are a senior Site Reliability Engineer and Kubernetes incident response expert.

Analyze the provided Kubernetes incidents.

Use BOTH:
1. Structured operational incident context
2. Pre-classified incident intelligence

Provide the following:

1. Incident Summary
2. Root Cause
3. Severity Assessment
4. Recommended Immediate Remediation
5. Preventive Recommendations
6. Team Ownership Recommendation

Classified Incident Intelligence:
{json.dumps(classified_incidents, indent=2)}

Operational Incident Context:
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
    Main RCA execution workflow.
    """

    print("\nCollecting incident context...\n")

    incident_context = collect_incident_context()

    if not incident_context:
        print("No problematic incidents detected.")
        return

    print("Classifying incidents...\n")

    classified_incidents = classify_incident(incident_context)

    print("Generating AI RCA...\n")

    rca_output = generate_rca(
        incident_context=incident_context,
        classified_incidents=classified_incidents
    )

    print("\n===== INCIDENT CLASSIFICATION =====\n")
    print(json.dumps(classified_incidents, indent=2))

    print("\n===== AI RCA OUTPUT =====\n")
    print(rca_output)


if __name__ == "__main__":
    main()