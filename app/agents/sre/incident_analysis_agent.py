from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.llm.client import LLMClient
from app.memory.retrieval.hybrid_search import hybrid_incident_search
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.memory import MemoryQuery
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)

MAX_ANALYSIS_WORKERS = 2

_thread_local = threading.local()


def get_llm() -> LLMClient:
    """
    Thread-local LLM client.
    Avoid repeated provider initialization per worker.
    """
    if not hasattr(_thread_local, "llm"):
        _thread_local.llm = LLMClient()

    return _thread_local.llm


def build_historical_context(
    classification: IncidentClassification,
    incident: IncidentContext,
) -> str:
    """
    Retrieve relevant historical operational memory.
    """
    failure_reason = None

    if incident.container_states:
        first = incident.container_states[0]

        if (
            first.last_termination
            and isinstance(first.last_termination, dict)
        ):
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

    return json.dumps(
        results,
        indent=2,
        default=str,
    )


def build_incident_summary(
    incident: IncidentContext,
) -> dict:
    """
    Build compact LLM-safe incident summary.
    """
    containers = []

    for container in incident.container_states:
        containers.append(
            {
                "container": container.container,
                "state": container.state,
                "restart_count": container.restart_count,
                "last_termination": container.last_termination,
            }
        )

    metrics = {}

    if incident.metrics:
        metrics = incident.metrics.model_dump()

    return {
        "pod_name": incident.pod_name,
        "namespace": incident.namespace,
        "phase": incident.phase,
        "node": incident.node,
        "containers": containers,
        "events": incident.events[-3:],
        "metrics": metrics,
    }


def build_prompt(
    incident: IncidentContext,
    classification: IncidentClassification,
    history: str,
) -> str:
    """
    Build production-safe analysis prompt.
    """
    summary = build_incident_summary(
        incident
    )

    return f"""
You are a senior Kubernetes Site Reliability Engineer.

Analyze this production incident.

Return EXACTLY:

### Incident Summary
### Root Cause Analysis
### Immediate Safe Actions
### Kubernetes Validation Commands
### Escalation Recommendation
### Preventive Recommendations
### Risk Notes

Rules:
- validation-first
- no destructive remediation
- recommend escalation when uncertain
- prioritize operational safety
- keep guidance practical and executable

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
    """
    Execute AI incident analysis.
    """
    llm = get_llm()

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
            "Analyzing pod=%s incident=%s",
            incident.pod_name,
            classification.incident_type,
        )

        response = llm.generate(
            prompt
        )

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
    """
    Manual incident analysis workflow.
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

    results: list[dict | None] = [None] * len(
        incidents
    )

    future_map = {}

    with ThreadPoolExecutor(
        max_workers=MAX_ANALYSIS_WORKERS
    ) as executor:

        for idx, (
            incident,
            classification,
        ) in enumerate(
            zip(
                incidents,
                classifications,
                strict=False,
            )
        ):
            future = executor.submit(
                analyze_incident,
                incident,
                classification,
            )

            future_map[future] = idx

    for future in as_completed(
        future_map
    ):
        idx = future_map[future]

        try:
            results[idx] = future.result()

        except Exception:
            logger.exception(
                "Worker execution failure"
            )

            results[idx] = {
                "analysis": "Worker failed"
            }

    print(
        json.dumps(
            results,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()