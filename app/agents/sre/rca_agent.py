from __future__ import annotations

import json

from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.llm.client import LLMClient
from app.memory.retrieval.search import search_incident_memory
from app.schemas.ai import RCAResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.memory import MemoryQuery
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)


def build_historical_context(
    classification: IncidentClassification,
    incident: IncidentContext,
) -> str:
    """
    Retrieve similar historical incidents for RCA enrichment.
    """

    query = MemoryQuery(
        incident_type=classification.incident_type,
        namespace=incident.namespace,
        limit=3,
    )

    try:
        results = search_incident_memory(query)

    except Exception:
        logger.exception(
            "Historical memory retrieval failed"
        )
        return "Historical memory unavailable."

    if not results.matches:
        return "No similar historical incidents found."

    history = []

    for memory in results.matches:
        history.append(
            {
                "incident_type": memory.incident_type,
                "severity": memory.severity,
                "failure_reason": memory.fingerprint.failure_reason,
                "rca_summary": memory.rca_summary,
                "remediation_summary": memory.remediation_summary,
            }
        )

    logger.info(
        "Historical incident context retrieved matches=%s",
        len(results.matches),
    )

    return json.dumps(
        history,
        indent=2,
    )


def build_rca_prompt(
    incident: IncidentContext,
    classification: IncidentClassification,
) -> str:
    """
    Build RCA analysis prompt.
    """

    historical_context = build_historical_context(
        classification=classification,
        incident=incident,
    )

    return f"""
You are a senior Site Reliability Engineer specializing in Kubernetes incident response.

Analyze the incident using ALL available operational signals and relevant historical incident memory.

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
- historical incident memory
    - prior RCA outcomes
    - prior remediation actions
    - prior failure patterns

Your responsibilities:

1. Identify the most likely root cause
2. Correlate Kubernetes runtime signals with Prometheus telemetry
3. Detect restart storms
4. Detect memory pressure / exhaustion
5. Detect image pull failures
6. Detect configuration failures
7. Compare with historical operational incidents
8. Assess severity
9. Recommend ownership team
10. Suggest preventive engineering actions

Output format:

### Incident Summary
### Historical Similarity Analysis
### Root Cause Analysis
### Signal Correlation
### Severity Assessment
### Team Ownership Recommendation
### Preventive Recommendations

Incident Classification:
{classification.model_dump_json(indent=2)}

Historical Incident Memory:
{historical_context}

Incident Context:
{incident.model_dump_json(indent=2)}
"""


def generate_rca(
    incident: IncidentContext,
    classification: IncidentClassification,
    llm_client: LLMClient | None = None,
) -> RCAResponse:
    """
    Generate AI-assisted RCA.
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

        logger.info(
            "RCA generation completed pod=%s",
            incident.pod_name,
        )

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


def generate_all_rcas(
    incidents: list[IncidentContext],
    classifications: list[IncidentClassification],
) -> list[RCAResponse]:
    """
    Generate RCA responses for all incidents.
    """

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
            )
        )

    logger.info(
        "RCA generation completed count=%s",
        len(results),
    )

    return results


def main() -> None:
    """
    Standalone RCA workflow.
    """

    logger.info("Collecting incident context")

    incidents = collect_incident_context()

    if not incidents:
        logger.warning("No incidents detected")
        print("No incidents detected.")
        return

    logger.info("Classifying incidents")

    classifications = classify_incident(
        incidents
    )

    logger.info("Generating RCA responses")

    results = generate_all_rcas(
        incidents=incidents,
        classifications=classifications,
    )

    print(
        json.dumps(
            [result.model_dump() for result in results],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()