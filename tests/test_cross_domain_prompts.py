from __future__ import annotations

import unittest
from unittest.mock import patch

from app.agents.sre.incident_analysis_agent import build_prompt
from app.agents.sre.rca_agent import build_rca_prompt
from app.agents.sre.remediation_agent import build_remediation_prompt
from app.prompts.shared.cross_domain import (
    KUBERNETES_LINUX_CORRELATION_POLICY,
)
from app.schemas.classification import IncidentClassification
from app.schemas.incident import ContainerState, IncidentContext
from app.schemas.memory import (
    IncidentPatternGuidance,
    IncidentPatternSummary,
)


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
                restart_count=4,
                last_termination={
                    "reason": "OOMKilled",
                    "exit_code": 137,
                },
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
        restart_count=4,
        incident_type="MemoryExhaustion",
        severity="critical",
        confidence=95,
        recommended_team="SRE",
    )


class CrossDomainPromptTests(unittest.TestCase):
    def test_policy_requires_evidence_not_host_guessing(self) -> None:
        self.assertIn(
            "Never invent host-level facts",
            KUBERNETES_LINUX_CORRELATION_POLICY,
        )
        self.assertIn(
            "AOP Linux diagnostic command",
            KUBERNETES_LINUX_CORRELATION_POLICY,
        )

    @patch(
        "app.agents.sre.rca_agent.build_historical_context",
        return_value=("No history.", False),
    )
    def test_rca_prompt_includes_cross_domain_policy(
        self,
        _history,
    ) -> None:
        prompt = build_rca_prompt(
            _incident(),
            _classification(),
        )

        self.assertIn(
            KUBERNETES_LINUX_CORRELATION_POLICY,
            prompt,
        )

    @patch(
        "app.agents.sre.rca_agent.build_historical_context",
        return_value=("No history.", False),
    )
    def test_rca_prompt_includes_bounded_pattern_memory(
        self,
        _history,
    ) -> None:
        prompt = build_rca_prompt(
            _incident(),
            _classification(),
            pattern_guidance=IncidentPatternGuidance(
                pod_name="checkout",
                namespace="payments",
                container="checkout",
                incident_type="MemoryExhaustion",
                fingerprint="kubernetes:payments:checkout:memoryexhaustion:oomkilled",
                patterns=[
                    IncidentPatternSummary(
                        fingerprint=(
                            "kubernetes:payments:checkout:memoryexhaustion:oomkilled"
                        ),
                        domain="kubernetes",
                        incident_type="MemoryExhaustion",
                        occurrence_count=3,
                        latest_timestamp="2026-08-14T00:00:00Z",
                        severities=["critical"],
                        resources=["payments/checkout"],
                        occurrences=[],
                    )
                ],
            ),
        )

        self.assertIn("Bounded Incident Pattern Memory", prompt)
        self.assertIn("3 previous occurrence", prompt)
        self.assertIn("clue, not proof", prompt)

    @patch(
        "app.agents.sre.rca_agent.build_historical_context",
        return_value=("No history.", False),
    )
    def test_rca_prompt_includes_bounded_runbook_context(
        self,
        _history,
    ) -> None:
        prompt = build_rca_prompt(
            _incident(),
            _classification(),
        )

        self.assertIn("Bounded Runbook/RAG Context", prompt)
        self.assertIn("Kubernetes OOMKilled", prompt)
        self.assertIn("guidance, not proof", prompt)

    def test_combined_analysis_prompt_includes_policy(self) -> None:
        prompt = build_prompt(
            _incident(),
            _classification(),
            "No history.",
        )

        self.assertIn(
            KUBERNETES_LINUX_CORRELATION_POLICY,
            prompt,
        )

    @patch(
        "app.agents.sre.remediation_agent.build_historical_context",
        return_value=("No history.", False),
    )
    def test_remediation_prompt_includes_policy(
        self,
        _history,
    ) -> None:
        prompt = build_remediation_prompt(
            _incident(),
            _classification(),
            "Memory limit was exceeded.",
        )

        self.assertIn(
            KUBERNETES_LINUX_CORRELATION_POLICY,
            prompt,
        )


if __name__ == "__main__":
    unittest.main()
