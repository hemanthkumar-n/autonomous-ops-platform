

from openai import OpenAI
from kubernetes import client, config

config.load_kube_config()

v1 = client.CoreV1Api()

client_ai = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)


def get_events(namespace="ai-lab"):
    events = v1.list_namespaced_event(namespace)

    output = []

    for event in events.items:
        output.append(
            f"Type: {event.type}, "
            f"Reason: {event.reason}, "
            f"Message: {event.message}"
        )

    return "\n".join(output)


def analyze_incident():

    events = get_events()

    response = client_ai.chat.completions.create(
        model="qwen2.5-coder",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior Kubernetes SRE engineer. "
                    "Analyze Kubernetes events and provide:\n"
                    "- Root cause\n"
                    "- Impact\n"
                    "- Recommended remediation\n"
                    "- Severity"
                )
            },
            {
                "role": "user",
                "content": events
            }
        ]
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    analyze_incident()
