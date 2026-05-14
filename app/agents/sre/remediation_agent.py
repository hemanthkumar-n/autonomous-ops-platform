import json
import requests

from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.response_validator import validate_llm_response
from app.schemas.ai import RemediationResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)


def generate_remediation(
    incident: IncidentClassification,
    relevant_context: list[IncidentContext],
) -> RemediationResponse:
    """
    Generate typed remediation response for one incident.
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
{json.dumps(incident.model_dump(), indent=2)}

Relevant Incident Context:
{json.dumps([ctx.model_dump() for ctx in relevant_context], indent=2)}
"""

    payload = {
        "model": settings.MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    endpoint = f"{settings.OLLAMA_BASE_URL}/api/generate"

    try:
        logger.info(
            "Generating remediation for pod=%s incident=%s",
            incident.pod_name,
            incident.incident_type,
        )

        response = requests.post(
            endpoint,
            json=payload,
            timeout=settings.AI_REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        result = response.json()

        llm_response = validate_llm_response(
            result.get("response")
        )

        logger.info(
            "Remediation generated pod=%s",
            incident.pod_name,
        )

        return RemediationResponse(
            pod_name=incident.pod_name,
            incident_type=incident.incident_type,
            remediation=llm_response,
        )

    except requests.exceptions.RequestException:
        logger.exception(
            "Remediation LLM request failed pod=%s",
            incident.pod_name,
        )

        return RemediationResponse(
            pod_name=incident.pod_name,
            incident_type=incident.incident_type,
            remediation="AI remediation unavailable. Manual remediation required.",
        )

    except Exception:
        logger.exception(
            "Unexpected remediation generation failure pod=%s",
            incident.pod_name,
        )

        return RemediationResponse(
            pod_name=incident.pod_name,
            incident_type=incident.incident_type,
            remediation="AI remediation unavailable. Manual remediation required.",
        )


def generate_all_remediations(
    classified_incidents: list[IncidentClassification],
    incident_context: list[IncidentContext],
) -> list[RemediationResponse]:
    """
    Generate remediation responses for all incidents.
    """

    remediation_results = []

    for incident in classified_incidents:
        relevant_context = [
            ctx
            for ctx in incident_context
            if ctx.pod_name == incident.pod_name
        ]

        remediation = generate_remediation(
            incident=incident,
            relevant_context=relevant_context,
        )

        remediation_results.append(remediation)

    logger.info(
        "Remediation generation completed total=%s",
        len(remediation_results),
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
        print("No incidents detected.")
        return

    logger.info("Classifying incidents")

    classified_incidents = classify_incident(
        incident_context
    )

    logger.info("Generating remediation responses")

    remediation_results = generate_all_remediations(
        classified_incidents=classified_incidents,
        incident_context=incident_context,
    )

    print(
        json.dumps(
            [result.model_dump() for result in remediation_results],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()