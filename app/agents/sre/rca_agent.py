import json
import requests

from app.tools.kubernetes.incident_context import collect_incident_context
from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.llm.response_validator import validate_llm_response
from app.config.settings import settings

logger = get_logger(__name__)


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
        "model": settings.MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    endpoint = f"{settings.OLLAMA_BASE_URL}/api/generate"

    try:
        logger.info("Submitting RCA request to LLM")

        response = requests.post(
            endpoint,
            json=payload,
            timeout=settings.AI_REQUEST_TIMEOUT
        )

        response.raise_for_status()

        result = response.json()

        llm_response = result.get("response")

        validated_response = validate_llm_response(llm_response)

        logger.info("RCA generated successfully")

        return validated_response

    except requests.exceptions.RequestException:
        logger.exception("LLM request failed during RCA generation")
        return "AI RCA unavailable. Manual investigation required."

    except Exception:
        logger.exception("Unexpected RCA generation failure")
        return "AI RCA unavailable. Manual investigation required."


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

    classified_incidents = classify_incident(incident_context)
    if not classified_incidents:
        logger.warning("No classified incidents available")
        return

    logger.info("Generating observability-aware RCA")

    rca_output = generate_rca(
        incident_context=incident_context,
        classified_incidents=classified_incidents
    )

    print("\n===== AI RCA OUTPUT =====\n")
    print(rca_output)


if __name__ == "__main__":
    main()