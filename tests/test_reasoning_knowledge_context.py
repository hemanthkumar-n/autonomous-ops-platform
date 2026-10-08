from __future__ import annotations

import unittest
from unittest.mock import patch

from app.agents.sre.incident_analysis_agent import build_historical_context as analysis_context
from app.agents.sre.remediation_agent import build_historical_context as remediation_context
from app.schemas.classification import IncidentClassification
from app.schemas.incident import ContainerState, IncidentContext


def _incident() -> IncidentContext:
    return IncidentContext(
        pod_name="checkout",
        namespace="payments",
        phase="Running",
        node="worker-1",
        container_states=[
            ContainerState(
                container="checkout",
                state="CrashLoopBackOff",
                restart_count=3,
                last_termination={"reason": "OOMKilled", "exit_code": 137},
            )
        ],
    )


def _classification() -> IncidentClassification:
    return IncidentClassification(
        pod_name="checkout",
        namespace="payments",
        node="worker-1",
        container="checkout",
        container_state="CrashLoopBackOff",
        restart_count=3,
        incident_type="MemoryExhaustion",
        severity="critical",
        confidence=95,
        recommended_team="SRE",
    )


class ReasoningKnowledgeContextTests(unittest.TestCase):
    @patch(
        "app.agents.sre.incident_analysis_agent.retrieve_incident_knowledge_context",
        return_value=("unified analysis context", True, object()),
    )
    def test_incident_analysis_uses_shared_unified_context(self, retrieval) -> None:
        context = analysis_context(_classification(), _incident())

        self.assertEqual(context, "unified analysis context")
        retrieval.assert_called_once()

    @patch(
        "app.agents.sre.remediation_agent.retrieve_incident_knowledge_context",
        return_value=("unified remediation context", True, object()),
    )
    def test_remediation_uses_shared_unified_context(self, retrieval) -> None:
        context, has_history = remediation_context(_classification(), _incident())

        self.assertEqual(context, "unified remediation context")
        self.assertTrue(has_history)
        retrieval.assert_called_once()


if __name__ == "__main__":
    unittest.main()
