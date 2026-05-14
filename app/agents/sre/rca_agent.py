import json
import requests

from app.tools.kubernetes.incident_context import (
    collect_incident_context
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:latest"


def generate_rca(incident_context):

    prompt = f"""
You are a senior Site Reliability Engineer.

Analyze the Kubernetes incident.

Provide:

1. Incident Summary
2. Root Cause
3. Severity
4. Immediate Remediation
5. Preventive Recommendations

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
        json=payload
    )

    result = response.json()

    return result["response"]


if __name__ == "__main__":

    context = collect_incident_context(
        pod_name="memory-stress"
    )

    rca = generate_rca(context)

    print("\n===== AI RCA =====\n")
    print(rca)