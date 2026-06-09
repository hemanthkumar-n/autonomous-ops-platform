from __future__ import annotations

import json

from app.agents.sre.incident_classifier import classify_incident
from app.agents.sre.rca_agent import generate_rca
from app.config.logging_config import get_logger
from app.llm.client import LLMClient
from app.memory.fingerprints.signature import extract_failure_reason
from app.memory.retrieval.hybrid_search import (
    hybrid_incident_search,
)
from app.schemas.ai import RemediationResponse
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

    query = MemoryQuery(
        incident_type=classification.incident_type,
        namespace=incident.namespace,
        workload_name=incident.pod_name,
        failure_reason=extract_failure_reason(incident),
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


def build_remediation_prompt(
    incident: IncidentContext,
    classification: IncidentClassification,
    rca: str,
) -> str:
    """
    Build remediation prompt.
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
- Compare remediation options with similar historical incidents
- Prefer historically successful low-risk actions
- Highlight repeated operational failure patterns
"""
    else:
        historical_guidance = """
Historical reasoning responsibilities:
- No historical incidents available
- Base remediation only on current incident evidence
"""

    return f"""
You are a senior Site Reliability Engineer specializing in Kubernetes remediation guidance.

Generate SAFE operational remediation guidance.

Inputs:
- incident runtime context
- classification
- root cause analysis
- historical operational memory

Core responsibilities:

1. Recommend immediate low-risk actions
2. Suggest Kubernetes validation commands
3. Recommend escalation path
4. Suggest preventive improvements

{historical_guidance}

Safety rules:
- Never recommend destructive actions automatically
- Prefer validation-first remediation
- Recommend escalation when confidence is limited
- Preserve operational safety

Output format:

### Incident
### Historical Similarity Analysis
### Immediate Safe Actions
### Kubernetes Validation Commands
### Escalation Recommendation
### Preventive Recommendations
### Risk Notes

Incident Classification:
{classification.model_dump_json(indent=2)}

Incident Context:
{incident.model_dump_json(indent=2)}

Root Cause Analysis:
{rca}

Historical Operational Memory:
{historical_context}
"""


def generate_remediation(
    incident: IncidentContext,
    classification: IncidentClassification,
    rca: str,
    llm_client: LLMClient | None = None,
) -> RemediationResponse:
    """
    Generate memory-aware remediation guidance.
    """

    llm = llm_client or LLMClient()
    owns_client = llm_client is None

    prompt = build_remediation_prompt(
        incident=incident,
        classification=classification,
        rca=rca,
    )

    try:
        logger.info(
            "Generating remediation pod=%s incident=%s",
            incident.pod_name,
            classification.incident_type,
        )

        response = llm.generate(
            prompt
        )

        return RemediationResponse(
            pod_name=incident.pod_name,
            incident_type=classification.incident_type,
            remediation=response,
        )

    except Exception:
        logger.exception(
            "Remediation generation failed pod=%s",
            incident.pod_name,
        )

        return RemediationResponse(
            pod_name=incident.pod_name,
            incident_type=classification.incident_type,
            remediation=(
                "AI remediation unavailable. "
                "Manual intervention required."
            ),
        )
    finally:
        if owns_client:
            llm.close()


def generate_all_remediations(
    incidents: list[IncidentContext],
    classifications: list[IncidentClassification],
    rca_results: list | None = None,
    llm_client: LLMClient | None = None,
) -> list[RemediationResponse]:
    """
    Generate remediation guidance for aligned incident results.
    """

    results = []

    for index, (incident, classification) in enumerate(
        zip(
            incidents,
            classifications,
            strict=False,
        )
    ):
        if rca_results and index < len(rca_results):
            rca_text = rca_results[index].rca
        else:
            rca_text = generate_rca(
                incident=incident,
                classification=classification,
                llm_client=llm_client,
            ).rca

        results.append(
            generate_remediation(
                incident=incident,
                classification=classification,
                rca=rca_text,
                llm_client=llm_client,
            )
        )

    return results


def main() -> None:
    """
    Manual remediation workflow.
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

    classifications = classify_incident(
        incidents
    )

    results = []

    for incident, classification in zip(
        incidents,
        classifications,
        strict=False,
    ):
        rca = generate_rca(
            incident=incident,
            classification=classification,
        )

        results.append(
            generate_remediation(
                incident=incident,
                classification=classification,
                rca=rca.rca,
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
