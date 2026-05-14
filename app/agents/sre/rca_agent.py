import json
import requests

from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.response_validator import validate_llm_response
from app.schemas.ai import RCAResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)


def generate_rca(
    incident_context: list[IncidentContext],
    classified_incidents: list[IncidentClassification],
) -> list[RCAResponse]:
    """
    Generate typed RCA responses.
    """

    rca_results = []

    for incident in classified_incidents:
        logger.info(
            "Generating RCA for pod=%s incident=%s",
            incident.pod_name,
            incident.incident_type,
        )

        relevant_context = [
            ctx
            for ctx in incident_context
            if ctx.pod_name == incident.pod_name
        ]

        prompt = f"""
You are a senior Site Reliability Engineer specializing in Kubernetes incident response.

Analyze this incident using ALL available operational signals.

Signal sources include:
- Kubernetes pod lifecycle state
- container runtime state
- restart counts
- last termination reasons
- resource requests and limits
- Kubernetes events
- container logs
- Prometheus observability metrics

Responsibilities:
1. Identify root cause
2. Correlate Kubernetes runtime + telemetry
3. Assess severity
4. Recommend ownership
5. Suggest preventive engineering actions

Incident Classification:
{json.dumps(incident.model_dump(), indent=2)}

Incident Context:
{json.dumps([ctx.model_dump() for ctx in relevant_context], indent=2)}
"""

        payload = {
            "model": settings.MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        }

        endpoint = f"{settings.OLLAMA_BASE_URL}/api/generate"

        try:
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

            rca_results.append(
                RCAResponse(
                    pod_name=incident.pod_name,
                    incident_type=incident.incident_type,
                    rca=llm_response,
                )
            )

        except requests.exceptions.RequestException:
            logger.exception(
                "RCA generation failed pod=%s",
                incident.pod_name,
            )

            rca_results.append(
                RCAResponse(
                    pod_name=incident.pod_name,
                    incident_type=incident.incident_type,
                    rca="AI RCA unavailable. Manual investigation required.",
                )
            )

    return rca_results


def main():
    """
    RCA execution workflow.
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

    logger.info("Generating RCA responses")

    rca_results = generate_rca(
        incident_context=incident_context,
        classified_incidents=classified_incidents,
    )

    print(
        json.dumps(
            [result.model_dump() for result in rca_results],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()