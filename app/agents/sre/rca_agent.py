from __future__ import annotations

import json

from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.llm.client import LLMClient
from app.schemas.ai import RCAResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)


def build_rca_prompt(
    incident: IncidentContext,
    classification: IncidentClassification,
) -> str:
    """
    Build RCA analysis prompt.
    """

    return f"""
You are a senior Site Reliability Engineer specializing in Kubernetes incident response.

Analyze the incident using ALL available operational signals.

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
{classification.model_dump_json(indent=2)}

Incident Context:
{incident.model_dump_json(indent=2)}
"""


def generate_rca(
    incident: IncidentContext,
    classification: IncidentClassification,
    llm_client: LLMClient | None = None,
) -> RCAResponse:
    """
    Generate RCA using central LLM client.
    """

    llm = llm_client or LLMClient()

    prompt = build_rca_prompt(
        incident=incident,
        classification=classification,
    )

    try:
        logger.info(
            "Generating RCA for pod=%s incident=%s",
            incident.pod_name,
            classification.incident_type,
        )

        response = llm.generate(prompt)

        return RCAResponse(
            pod_name=incident.pod_name,
            incident_type=classification.incident_type,
            rca=response,
        )

    except Exception:
        logger.exception(
            "RCA generation failed pod=%s",
            incident.pod_name,
        )

        return RCAResponse(
            pod_name=incident.pod_name,
            incident_type=classification.incident_type,
            rca="AI RCA unavailable. Manual investigation required.",
        )


def main() -> None:
    """
    RCA execution workflow.
    """

    logger.info("Collecting incident context")

    incidents = collect_incident_context()

    if not incidents:
        logger.warning("No incidents detected")
        print("No incidents detected.")
        return

    logger.info("Classifying incidents")

    classifications = classify_incident(incidents)

    results = []

    for incident, classification in zip(
        incidents,
        classifications,
        strict=False,
    ):
        results.append(
            generate_rca(
                incident=incident,
                classification=classification,
            ).model_dump()
        )

    print(
        json.dumps(
            results,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
