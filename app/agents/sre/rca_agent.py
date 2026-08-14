from __future__ import annotations

from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.llm.client import LLMClient
from app.memory.fingerprints.signature import extract_failure_reason
from app.memory.incident_patterns.patterns import (
    format_pattern_guidance_for_prompt,
)
from app.memory.retrieval.knowledge import (
    format_knowledge_context_for_prompt,
    retrieve_knowledge,
)
from app.prompts.shared.cross_domain import (
    KUBERNETES_LINUX_CORRELATION_POLICY,
)
from app.schemas.ai import RCAResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.memory import (
    IncidentPatternGuidance,
    KnowledgeQuery,
)
from app.tools.kubernetes.incident_context import (
    collect_incident_context,
)

logger = get_logger(__name__)


def build_knowledge_context(
    classification: IncidentClassification,
    incident: IncidentContext,
) -> tuple[str, bool]:
    """
    Retrieve one bounded context across guidance and operational memory.
    """

    query = KnowledgeQuery(
        domain="kubernetes",
        incident_type=classification.incident_type,
        text=(
            f"{incident.phase} {classification.container_state} "
            f"{classification.incident_type} {incident.model_dump_json()}"
        ),
        namespace=incident.namespace,
        workload_name=incident.pod_name,
        failure_reason=extract_failure_reason(incident),
        severity=classification.severity,
        evidence_references=[
            f"kubernetes://{incident.namespace}/pod/{incident.pod_name}"
        ],
        limit=3,
    )
    result = retrieve_knowledge(query)
    has_history = any(
        (
            source.startswith("incident_memory")
            or source == "incident_pattern"
        )
        and count > 0
        for source, count in result.source_counts.items()
    )
    return format_knowledge_context_for_prompt(result), has_history


def build_historical_context(
    classification: IncidentClassification,
    incident: IncidentContext,
) -> tuple[str, bool]:
    """Compatibility wrapper for callers using the previous helper name."""

    return build_knowledge_context(classification, incident)


def build_rca_prompt(
    incident: IncidentContext,
    classification: IncidentClassification,
    pattern_guidance: IncidentPatternGuidance | None = None,
) -> str:
    """
    Build RCA analysis prompt.
    """

    historical_context, has_history = (
        build_knowledge_context(
            classification=classification,
            incident=incident,
        )
    )

    historical_guidance = ""
    pattern_context = format_pattern_guidance_for_prompt(pattern_guidance)

    if has_history:
        historical_guidance = """
Historical reasoning responsibilities:
4. Compare against similar historical incidents
5. Detect recurrence patterns
6. Highlight recurring operational risks
7. Treat exact pattern recurrence as a clue, not proof
8. Use trusted runbook context only as bounded guidance
"""
    else:
        historical_guidance = """
Historical reasoning responsibilities:
4. No historical incidents available. Base analysis only on current runtime evidence.
5. Still review exact pattern memory if present, but do not infer missing facts.
6. Use trusted runbook context only as bounded guidance.
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

8. Recommend ownership team
9. Suggest preventive engineering actions

Important telemetry note:
Prometheus metrics represent point-in-time observations and may not reflect historical peak resource usage before failure.

{KUBERNETES_LINUX_CORRELATION_POLICY}

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

Bounded Incident Pattern Memory:
{pattern_context}

Bounded Runbook/RAG Context (Unified Knowledge Retrieval):
{historical_context}
"""

def generate_rca(
    incident: IncidentContext,
    classification: IncidentClassification,
    llm_client: LLMClient | None = None,
    pattern_guidance: IncidentPatternGuidance | None = None,
) -> RCAResponse:
    """
    Generate memory-aware RCA.
    """

    llm = llm_client or LLMClient()
    owns_client = llm_client is None

    prompt = build_rca_prompt(
        incident=incident,
        classification=classification,
        pattern_guidance=pattern_guidance,
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
    finally:
        if owns_client:
            llm.close()


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
