from openai import OpenAI
from app.tools.kubernetes.incident_context import (
    collect_incident_context
)

import json


client_ai = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)


def analyze_incident():

    # Collect structured Kubernetes incident data
    incident_context = collect_incident_context()

    # Convert Python object to formatted JSON
    formatted_context = json.dumps(
        incident_context,
        indent=2
    )

    # Send structured operational context to local LLM
    response = client_ai.chat.completions.create(
        model="qwen2.5-coder",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior Kubernetes SRE engineer.\n"
                    "Analyze the Kubernetes incident context and provide:\n\n"
                    "1. Incident Summary\n"
                    "2. Root Cause\n"
                    "3. Severity\n"
                    "4. Impact\n"
                    "5. Recommended Remediation\n"
                    "6. Preventive Measures\n"
                )
            },
            {
                "role": "user",
                "content": formatted_context
            }
        ]
    )

    print("\n===== AI INCIDENT RCA =====\n")

    print(response.choices[0].message.content)


if __name__ == "__main__":
    analyze_incident()