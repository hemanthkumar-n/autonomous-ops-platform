from __future__ import annotations

import json

from app.agents.sre.incident_classifier import classify_incident
from app.config.logging_config import get_logger
from app.llm.client import LLMClient
from app.schemas.ai import RemediationResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)


def build_remediation_prompt(
    incident: IncidentContext,
    classification: IncidentClassification,
) -> str:
    """
    Build remediation planning prompt.
    """

    return f"""
You are a senior Site Reliability Engineer responsible for SAFE incident remediation.

Analyze ONE incident only.

Use all available operational signals.

Available signals:
- Kubernetes pod lifecycle state
- container runtime state
- restart counts
- last termination reasons
- resource requests and limits
- Kubernetes events
- container logs
- Prometheus metrics
    - memory usage
    - CPU usage
    - restart telemetry

Your responsibilities:

1. Recommend SAFE remediation steps
2. Avoid destructive actions
3. Recommend Kubernetes validation commands
4. Suggest rollback or escalation where appropriate
5. Correlate remediation with incident type

Incident handling guidance:

ImagePullFailure:
- validate image tag
- validate registry access
- validate deployment spec
- validate imagePullSecrets

MemoryExhaustion:
- validate memory pressure
- compare limits vs workload demand
- inspect restart storms
- inspect capacity constraints
- recommend resource tuning

CrashLoopBackOff:
- inspect startup logs
- inspect probes
- inspect dependency failures
- inspect config changes

FailedScheduling:
- inspect node capacity
- inspect taints / tolerations
- inspect quota constraints

Output format:

### Incident
### Immediate Safe Actions
### Kubernetes Validation Commands
### Escalation Recommendation
### Preventive Recommendations
### Risk Notes

Incident Classification:
{classification.model_dump_json(indent=2)}

Incident Context:
{incident.model_dump_json(indent=2)}
"""


def generate_remediation(
    incident: IncidentContext,
    classification: IncidentClassification,
    llm_client: LLMClient | None = None,
) -> RemediationResponse:
    """
    Generate remediation response.
    """

    llm = llm_client or LLMClient()

    prompt = build_remediation_prompt(
        incident=incident,
        classification=classification,
    )

    try:
        logger.info(
            "Generating remediation for pod=%s incident=%s",
            incident.pod_name,
            classification.incident_type,
        )

        response = llm.generate(prompt)

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
                "Manual SRE intervention required."
            ),
        )


def generate_all_remediations(
    incidents: list[IncidentContext],
    classifications: list[IncidentClassification],
) -> list[RemediationResponse]:
    """
    Generate remediation for all incidents.
    """

    results = []

    for incident, classification in zip(
        incidents,
        classifications,
        strict=False,
    ):
        results.append(
            generate_remediation(
                incident=incident,
                classification=classification,
            )
        )

    logger.info(
        "Remediation generation completed count=%s",
        len(results),
    )

    return results


def main() -> None:
    """
    Standalone remediation execution.
    """

    logger.info("Collecting incident context")

    incidents = collect_incident_context()

    if not incidents:
        logger.warning("No incidents detected")
        print("No incidents detected.")
        return

    logger.info("Classifying incidents")

    classifications = classify_incident(incidents)

    logger.info("Generating remediation responses")

    results = generate_all_remediations(
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
