from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.llm.client import LLMClient
from app.memory.retrieval.hybrid_search import hybrid_incident_search
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.memory import MemoryQuery
from app.tools.kubernetes.incident_context import collect_incident_context
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = get_logger(__name__)

MAX_ANALYSIS_WORKERS = 2


def build_historical_context(
    classification: IncidentClassification,
    incident: IncidentContext,
) -> str:
    failure_reason = None

    if incident.container_states:
        first = incident.container_states[0]

        if first.last_termination:
            failure_reason = first.last_termination.get(
                "reason"
            )

    query = MemoryQuery(
        incident_type=classification.incident_type,
        namespace=incident.namespace,
        workload_name=incident.pod_name,
        failure_reason=failure_reason,
        severity=classification.severity,
        limit=3,
    )

    results = hybrid_incident_search(query)

    if (
        results["exact_match_count"] == 0
        and results["semantic_match_count"] == 0
    ):
        return "No historical incidents found."

    return json.dumps(results, indent=2)


def build_incident_summary(
    incident: IncidentContext,
) -> dict:
    containers = []

    for c in incident.container_states:
        containers.append(
            {
                "container": c.container,
                "state": c.state,
                "restart_count": c.restart_count,
                "last_termination": c.last_termination,
            }
        )

    return {
        "pod_name": incident.pod_name,
        "namespace": incident.namespace,
        "phase": incident.phase,
        "node": incident.node,
        "containers": containers,
        "events": incident.events[-5:],
        "metrics": incident.metrics,
    }


def build_prompt(
    incident: IncidentContext,
    classification: IncidentClassification,
    history: str,
) -> str:
    summary = build_incident_summary(incident)

    return f"""
You are a senior Kubernetes SRE.

Analyze this incident.

Return:

### Incident Summary
### Root Cause Analysis
### Immediate Safe Actions
### Kubernetes Validation Commands
### Escalation Recommendation
### Preventive Recommendations
### Risk Notes

Rules:
- validation-first
- no destructive actions
- recommend escalation when uncertain

Classification:
{classification.model_dump_json(indent=2)}

Incident:
{json.dumps(summary, indent=2, default=str)}

Historical Context:
{history}
"""


def analyze_incident(
    incident: IncidentContext,
    classification: IncidentClassification,
) -> dict:
    llm = LLMClient()

    try:
        history = build_historical_context(
            classification,
            incident,
        )

        prompt = build_prompt(
            incident,
            classification,
            history,
        )

        logger.info(
            "Analyzing pod=%s",
            incident.pod_name,
        )

        response = llm.generate(prompt)

        return {
            "pod_name": incident.pod_name,
            "incident_type": classification.incident_type,
            "analysis": response,
        }

    except Exception:
        logger.exception(
            "Analysis failed pod=%s",
            incident.pod_name,
        )

        return {
            "pod_name": incident.pod_name,
            "incident_type": classification.incident_type,
            "analysis": "AI analysis unavailable.",
        }


def main() -> None:
    logger.info("Collecting incident context")

    incidents = collect_incident_context()

    if not incidents:
        print("No incidents detected.")
        return

    classifications = classify_incident(incidents)

    results = []

    with ThreadPoolExecutor(
        max_workers=MAX_ANALYSIS_WORKERS
    ) as executor:
        futures = []

        for incident, classification in zip(
            incidents,
            classifications,
            strict=False,
        ):
            futures.append(
                executor.submit(
                    analyze_incident,
                    incident,
                    classification,
                )
            )

        for future in as_completed(futures):
            results.append(
                future.result()
            )

    print(json.dumps(results, indent=10))


if __name__ == "__main__":
    main()