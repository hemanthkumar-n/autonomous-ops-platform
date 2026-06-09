from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.orchestration.incident_workflow import (
    run_incident_workflow,
)
from app.schemas.ai import RCAResponse, RemediationResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import ContainerState, IncidentContext


class IncidentWorkflowTests(unittest.TestCase):
    @patch(
        "app.orchestration.incident_workflow.LLMClient"
    )
    @patch(
        "app.orchestration.incident_workflow.generate_all_remediations"
    )
    @patch(
        "app.orchestration.incident_workflow.generate_rca"
    )
    @patch(
        "app.orchestration.incident_workflow.classify_incident"
    )
    @patch(
        "app.orchestration.incident_workflow.collect_incident_context"
    )
    def test_runs_aligned_workflow_without_persistence(
        self,
        collect_context,
        classify,
        generate_rca,
        generate_remediations,
        llm_client_class,
    ) -> None:
        incident = IncidentContext(
            pod_name="checkout",
            namespace="payments",
            phase="Running",
            container_states=[
                ContainerState(
                    container="app",
                    state="OOMKilled",
                    restart_count=5,
                )
            ],
        )
        classification = IncidentClassification(
            pod_name="checkout",
            namespace="payments",
            container="app",
            container_state="OOMKilled",
            restart_count=5,
            incident_type="MemoryExhaustion",
            severity="Critical",
            confidence=99,
            recommended_team="Application / Platform Engineering",
        )
        rca = RCAResponse(
            pod_name="checkout",
            incident_type="MemoryExhaustion",
            rca="Memory limit exceeded.",
        )
        remediation = RemediationResponse(
            pod_name="checkout",
            incident_type="MemoryExhaustion",
            remediation="Validate memory use and adjust limits.",
        )

        collect_context.return_value = [incident]
        classify.return_value = [classification]
        generate_rca.return_value = rca
        generate_remediations.return_value = [remediation]
        llm_client_class.return_value = Mock()

        workflow, saved_path = run_incident_workflow(
            namespace="payments",
            persist=False,
        )

        self.assertIsNotNone(workflow)
        self.assertIsNone(saved_path)
        self.assertEqual(
            workflow.classified_incidents[0].incident_type,
            "MemoryExhaustion",
        )
        collect_context.assert_called_once_with(
            namespace="payments",
            pod_name=None,
        )
        llm_client_class.return_value.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
