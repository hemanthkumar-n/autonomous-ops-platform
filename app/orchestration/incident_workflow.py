from __future__ import annotations

import json

from app.agents.sre.incident_classifier import classify_incident
from app.agents.sre.k8s_linux_correlation_agent import (
    correlate_k8s_linux,
)
from app.agents.sre.kubernetes_issue_training_agent import (
    get_kubernetes_issue_knowledge,
)
from app.agents.sre.rca_agent import generate_rca
from app.agents.sre.remediation_agent import generate_all_remediations
from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.client import LLMClient
from app.memory.incident_history.store_incident import store_incident
from app.memory.incident_patterns.patterns import (
    find_kubernetes_pattern_guidance,
)
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.workflow import (
    IncidentKnowledgeGuidance,
    WorkflowExecutionResponse,
)
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)


def _symptom_for_guidance(
    incident: IncidentContext,
    classification: IncidentClassification,
) -> str:
    for container in incident.container_states:
        if container.container != classification.container:
            continue
        termination_reason = (container.last_termination or {}).get("reason")
        if termination_reason:
            return str(termination_reason)
        if container.state:
            return container.state

    return classification.incident_type


def build_correlation_guidance(
    incidents: list[IncidentContext],
    classifications: list[IncidentClassification],
) -> list[IncidentKnowledgeGuidance]:
    guidance: list[IncidentKnowledgeGuidance] = []

    for incident, classification in zip(
        incidents,
        classifications,
        strict=False,
    ):
        symptom = _symptom_for_guidance(
            incident,
            classification,
        )
        kubernetes_knowledge = None
        linux_correlation = None
        evidence_gaps = []

        try:
            kubernetes_knowledge = get_kubernetes_issue_knowledge(symptom)
        except ValueError:
            evidence_gaps.append(
                f"No curated Kubernetes issue knowledge for {symptom}."
            )

        try:
            linux_correlation = correlate_k8s_linux(symptom)
        except ValueError:
            evidence_gaps.append(
                f"No Kubernetes-to-Linux correlation plan for {symptom}."
            )

        guidance.append(
            IncidentKnowledgeGuidance(
                pod_name=classification.pod_name,
                namespace=classification.namespace,
                container=classification.container,
                symptom=symptom,
                incident_type=classification.incident_type,
                kubernetes_knowledge=kubernetes_knowledge,
                linux_correlation=linux_correlation,
                evidence_gaps=evidence_gaps,
            )
        )

    return guidance


def run_incident_workflow(
    namespace: str | None = None,
    pod_name: str | None = None,
    persist: bool | None = None,
) -> tuple[WorkflowExecutionResponse | None, str | None]:
    """
    Run the incident intelligence workflow.
    """

    logger.info("Starting autonomous incident workflow")

    incidents = collect_incident_context(
        namespace=namespace,
        pod_name=pod_name,
    )

    if not incidents:
        logger.warning("No active incidents detected")
        return None, None

    logger.info(
        "Incident context collected count=%s",
        len(incidents),
    )

    classifications = classify_incident(incidents)

    logger.info(
        "Incident classification completed count=%s",
        len(classifications),
    )

    pattern_guidance = find_kubernetes_pattern_guidance(
        incidents=incidents,
        classifications=classifications,
    )

    llm_client = LLMClient()

    try:
        rca_results = []

        for index, (incident, classification) in enumerate(
            zip(
                incidents,
                classifications,
                strict=False,
            )
        ):
            pattern = (
                pattern_guidance[index]
                if index < len(pattern_guidance)
                else None
            )
            rca_results.append(
                generate_rca(
                    incident=incident,
                    classification=classification,
                    llm_client=llm_client,
                    pattern_guidance=pattern,
                )
            )

        logger.info(
            "RCA generation completed count=%s",
            len(rca_results),
        )

        remediation_results = generate_all_remediations(
            incidents=incidents,
            classifications=classifications,
            rca_results=rca_results,
            llm_client=llm_client,
        )
    finally:
        llm_client.close()

    logger.info(
        "Remediation generation completed count=%s",
        len(remediation_results),
    )

    correlation_guidance = build_correlation_guidance(
        incidents=incidents,
        classifications=classifications,
    )
    workflow_execution = WorkflowExecutionResponse(
        incident_context=incidents,
        classified_incidents=classifications,
        rca_results=rca_results,
        remediation_results=remediation_results,
        correlation_guidance=correlation_guidance,
        pattern_guidance=pattern_guidance,
    )

    should_persist = (
        settings.PERSIST_INCIDENTS
        if persist is None
        else persist
    )
    saved_path = None

    if should_persist:
        saved_path = store_incident(workflow_execution)

        logger.info(
            "Workflow persisted path=%s",
            saved_path,
        )

    return workflow_execution, saved_path


def main() -> None:
    """
    Manual incident workflow entrypoint.
    """

    workflow_execution, _ = run_incident_workflow()

    if workflow_execution is None:
        print("No active incidents detected.")
        return

    print(
        json.dumps(
            workflow_execution.model_dump(
                mode="json"
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
