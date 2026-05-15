from __future__ import annotations

import json

from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.llm.client import LLMClient
from app.memory.retrieval.hybrid_search import (
    hybrid_incident_search,
)
from app.schemas.ai import RCAResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.memory import MemoryQuery
from app.tools.kubernetes.incident_context import (
    collect_incident_context,
)

logger = get_logger(__name__)


def build_historical_context(
    classification: IncidentClassification,
    incident: IncidentContext,
) -> tuple[str, bool]:
    """
    Retrieve hybrid operational memory context.
    """

    failure_reason = None

    if incident.container_states:
        first_container = incident.container_states[0]

        if (
            first_container.last_termination
            and hasattr(
                first_container.last_termination,
                "reason",
            )
        ):
            failure_reason = (
                first_container.last_termination.reason
            )

    query = MemoryQuery(
        incident_type=classification.incident_type,
        namespace=incident.namespace,
        workload_name=incident.pod_name,
        failure_reason=failure_reason,
        severity=classification.severity,
        limit=3,
    )

    results = hybrid_incident_search(
        query
    )

    has_history = (
        results["exact_match_count"] > 0
        or results["semantic_match_count"] > 0
    )

    if not has_history:
        return (
            "No relevant historical incidents found.",
            False,
        )

    return (
        json.dumps(
            results,
            indent=2,
        ),
        True,
    )


def build_rca_prompt(
    incident: IncidentContext,
    classification: IncidentClassification,
) -> str:
    """
    Build RCA analysis prompt.
    """

    historical_context, has_history = (
        build_historical_context(
            classification=classification,
            incident=incident,
        )
    )

    historical_guidance = ""

    if has_history:
        historical_guidance = """
Historical reasoning responsibilities:
4. Compare against similar historical incidents
5. Detect recurrence patterns
6. Highlight recurring operational risks
"""
    else:
        historical_guidance = """
Historical reasoning responsibilities:
4. No historical incidents available. Base analysis only on current runtime evidence.
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

Primary responsibilities:

1. Identify the most likely root cause
2. Correlate runtime signals with telemetry
3. Assess severity

{historical_guidance}

Operational responsibilities:

7. Recommend ownership team
8. Suggest preventive engineering actions

Important telemetry note:
Prometheus metrics represent point-in-time observations and may not reflect historical peak resource usage before failure.

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

Incident Context:
{incident.model_dump_json(indent=2)}

Historical Operational Memory:
{historical_context}
"""

def generate_rca(
    incident: IncidentContext,
    classification: IncidentClassification,
    llm_client: LLMClient | None = None,
) -> RCAResponse:
    """
    Generate memory-aware RCA.
    """

    llm = llm_client or LLMClient()

    prompt = build_rca_prompt(
        incident=incident,
        classification=classification,
    )

    try:
        logger.info(
            "Generating RCA pod=%s incident=%s",
            incident.pod_name,
            classification.incident_type,
        )

        response = llm.generate(
            prompt
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
            rca=(
                "AI RCA unavailable. "
                "Manual investigation required."
            ),
        )


def main() -> None:
    """
    RCA execution workflow.
    """
    
    logger.info(
        "Collecting incident context"
    )

    incidents = collect_incident_context()

    if not incidents:
        logger.warning(
            "No incidents detected"
        )
        print("No incidents detected.")
        return

    logger.info(
        "Classifying incidents"
    )

    classifications = classify_incident(
        incidents
    )

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