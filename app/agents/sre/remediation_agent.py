import json
import requests

from app.tools.kubernetes.incident_context import collect_incident_context
from app.agents.sre.incident_classifier import classify_incident
from app.agents.sre.rca_agent import generate_rca

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:latest"


def generate_remediation_plan(
    incident_context,
    classified_incidents,
    rca_output
):
    """
    Generate remediation plan using AI.
    """

    prompt = f"""
You are a senior Site Reliability Engineer.

Generate a SAFE remediation plan for the Kubernetes incidents.

Provide:

1. Immediate Actions
2. Kubernetes Validation Commands
3. Escalation Recommendation
4. Preventive Recommendations
5. Risk Notes

Rules:
- Do NOT suggest destructive commands without explanation.
- Prefer safe operational recovery steps.
- Be precise and actionable.

Incident Classification:
{json.dumps(classified_incidents, indent=2)}

Incident Context:
{json.dumps(incident_context, indent=2)}

RCA Analysis:
{rca_output}
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
    Full remediation workflow.
    """

    print("\nCollecting incident context...\n")

    incident_context = collect_incident_context()

    if not incident_context:
        print("No problematic incidents detected.")
        return

    print("Classifying incidents...\n")

    classified_incidents = classify_incident(incident_context)

    print("Generating RCA...\n")

    rca_output = generate_rca(
        incident_context=incident_context,
        classified_incidents=classified_incidents
    )

    print("Generating remediation plan...\n")

    remediation_output = generate_remediation_plan(
        incident_context=incident_context,
        classified_incidents=classified_incidents,
        rca_output=rca_output
    )

    print("\n===== REMEDIATION PLAN =====\n")
    print(remediation_output)


if __name__ == "__main__":
    main()