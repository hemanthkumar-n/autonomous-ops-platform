from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from app.agents.sre.k8s_linux_correlation_agent import correlate_k8s_linux
from app.agents.sre.kubernetes_issue_training_agent import (
    get_kubernetes_issue_knowledge,
)
from app.cli.main import main
from app.schemas.ai import RCAResponse, RemediationResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import ContainerState, IncidentContext
from app.schemas.workflow import (
    IncidentKnowledgeGuidance,
    WorkflowExecutionResponse,
)
from app.schemas.memory import (
    IncidentPatternGuidance,
    IncidentPatternOccurrence,
    IncidentPatternSummary,
)


def _workflow() -> WorkflowExecutionResponse:
    return WorkflowExecutionResponse(
        incident_context=[
            IncidentContext(
                pod_name="checkout",
                namespace="payments",
                phase="Running",
                container_states=[
                    ContainerState(
                        container="app",
                        state="OOMKilled",
                        restart_count=3,
                    )
                ],
            )
        ],
        classified_incidents=[
            IncidentClassification(
                pod_name="checkout",
                namespace="payments",
                container="app",
                container_state="OOMKilled",
                restart_count=3,
                incident_type="MemoryExhaustion",
                severity="Critical",
                confidence=99,
                recommended_team="Application / Platform Engineering",
            )
        ],
        rca_results=[
            RCAResponse(
                pod_name="checkout",
                incident_type="MemoryExhaustion",
                rca="Container exceeded memory.",
            )
        ],
        remediation_results=[
            RemediationResponse(
                pod_name="checkout",
                incident_type="MemoryExhaustion",
                remediation="Validate memory usage.",
            )
        ],
        correlation_guidance=[
            IncidentKnowledgeGuidance(
                pod_name="checkout",
                namespace="payments",
                container="app",
                symptom="OOMKilled",
                incident_type="MemoryExhaustion",
                kubernetes_knowledge=get_kubernetes_issue_knowledge("OOMKilled"),
                linux_correlation=correlate_k8s_linux("OOMKilled"),
            )
        ],
        pattern_guidance=[
            IncidentPatternGuidance(
                pod_name="checkout",
                namespace="payments",
                container="app",
                incident_type="MemoryExhaustion",
                fingerprint="kubernetes:payments:checkout:memoryexhaustion:oomkilled",
                patterns=[
                    IncidentPatternSummary(
                        fingerprint=(
                            "kubernetes:payments:checkout:memoryexhaustion:oomkilled"
                        ),
                        domain="kubernetes",
                        incident_type="MemoryExhaustion",
                        occurrence_count=2,
                        latest_timestamp="2026-08-14T00:00:00Z",
                        severities=["Critical"],
                        resources=["payments/checkout"],
                        occurrences=[
                            IncidentPatternOccurrence(
                                incident_id="previous-1",
                                timestamp="2026-08-14T00:00:00Z",
                                domain="kubernetes",
                                resource="payments/checkout",
                                incident_type="MemoryExhaustion",
                                severity="Critical",
                                summary="Previous memory exhaustion.",
                                source_file="memory.json",
                            )
                        ],
                    )
                ],
            )
        ],
    )


class KubernetesInvestigateGuidanceCLITests(unittest.TestCase):
    @patch("app.orchestration.incident_workflow.run_incident_workflow")
    def test_summary_includes_knowledge_and_linux_commands(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_workflow(), None)

        result = CliRunner().invoke(
            main,
            ["investigate", "k8s", "-n", "payments"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("K8s symptom: OOMKilled", result.output)
        self.assertIn("Pattern memory", result.output)
        self.assertIn("2 previous occurrence", result.output)
        self.assertIn("Linux evidence needed", result.output)
        self.assertIn(
            "aop investigate linux memory --pid <container-pid>",
            result.output,
        )
        self.assertIn("Do not assume", result.output)

    @patch("app.orchestration.incident_workflow.run_incident_workflow")
    def test_json_includes_correlation_guidance(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_workflow(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s",
                "-n",
                "payments",
                "--format",
                "json",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        guidance = payload["correlation_guidance"][0]
        pattern_guidance = payload["pattern_guidance"][0]
        self.assertEqual(guidance["symptom"], "OOMKilled")
        self.assertEqual(pattern_guidance["patterns"][0]["occurrence_count"], 2)
        self.assertEqual(
            guidance["kubernetes_knowledge"]["symptom"],
            "OOMKilled",
        )
        self.assertIn(
            "aop investigate linux memory --pid <container-pid>",
            guidance["linux_correlation"]["next_aop_commands"],
        )

    @patch("app.orchestration.incident_workflow.run_incident_workflow")
    def test_markdown_includes_guidance_sections(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_workflow(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s",
                "-n",
                "payments",
                "--format",
                "markdown",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("### Incident Pattern Memory", result.output)
        self.assertIn("2` previous occurrence", result.output)
        self.assertIn("### Kubernetes Knowledge", result.output)
        self.assertIn("Linux evidence needed", result.output)
        self.assertIn("Do not assume", result.output)


if __name__ == "__main__":
    unittest.main()
