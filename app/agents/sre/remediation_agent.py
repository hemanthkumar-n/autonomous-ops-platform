import json
import requests

from app.tools.kubernetes.incident_context import collect_incident_context
from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.response_validator import validate_llm_response

logger = get_logger(__name__)


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
        "model": settings.MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    endpoint = f"{settings.OLLAMA_BASE_URL}/api/generate"

    try:
        response = requests.post(
            endpoint,
            json=payload,
            timeout=settings.AI_REQUEST_TIMEOUT
        )

        response.raise_for_status()

        result = response.json()

        llm_response = result.get("response")

        validated_response = validate_llm_response(llm_response)

        logger.info("Remediation generated successfully")

        return validated_response

    except requests.exceptions.RequestException:
        logger.exception("LLM remediation request failed")
        return "Remediation generation failed due to LLM connectivity issue."

    except Exception:
        logger.exception("Unexpected remediation generation failure")
        return "Unexpected remediation generation failure."


def map_incident_context(incident_context):
    """
    Map pod name -> incident context.
    """

    context_map = {}

    if not incident_context:
        return context_map

    for incident in incident_context:
        pod_name = incident.get("pod_name")

        if pod_name:
            context_map[pod_name] = incident

    return context_map


def generate_all_remediations(classified_incidents, incident_context):
    """
    Generate remediation per incident.
    """

    context_map = map_incident_context(incident_context)

    remediation_results = []

    for incident in classified_incidents:
        try:
            pod_name = incident.get("pod_name")

            relevant_context = context_map.get(pod_name, {})

            logger.info("Generating remediation for pod=%s", pod_name)

            remediation = generate_remediation(
                single_incident=incident,
                full_context=relevant_context
            )

            remediation_results.append({
                "pod_name": pod_name,
                "incident_type": incident.get("incident_type"),
                "remediation": remediation
            })

        except Exception:
            logger.exception(
                "Remediation generation failed for pod=%s",
                incident.get("pod_name")
            )

    return remediation_results


def main():
    """
    Remediation execution workflow.
    """

    logger.info("Collecting incident context")

    incident_context = collect_incident_context()

    if not incident_context:
        logger.warning("No incidents detected")
        return

    logger.info("Classifying incidents")

    classified_incidents = classify_incident(incident_context)

    logger.info("Generating remediation plans")

    remediation_results = generate_all_remediations(
        classified_incidents=classified_incidents,
        incident_context=incident_context
    )

    print(json.dumps(remediation_results, indent=2))


if __name__ == "__main__":
    main()