from __future__ import annotations

import unittest

from app.investigation.autonomous_loop import (
    AutonomousInvestigationLoop,
    EvidenceCollectionResult,
    InvestigationLoopPolicy,
)
from app.investigation.evidence_planner import EvidencePlanner
from app.investigation.models import EvidenceGap, Hypothesis, InvestigationCase
from app.schemas.evidence import EvidenceItem


class AutonomousInvestigationLoopTests(unittest.TestCase):
    def _case_with_gap(self) -> InvestigationCase:
        return InvestigationCase(
            id="INC-AUTO-1",
            title="Possible memory exhaustion",
            source="test",
            evidence_gaps=[
                EvidenceGap(
                    id="gap-node-memory",
                    description="Node memory state is unavailable.",
                    priority="critical",
                    reason="Need host memory evidence to confirm or reject memory pressure.",
                    recommended_checks=["aop investigate linux memory"],
                    blocks_rca=True,
                )
            ],
            hypotheses=[
                Hypothesis(
                    id="memory-pressure",
                    statement="Host memory pressure caused the incident.",
                    required_evidence_ids=["linux.memory.live"],
                    missing_evidence_ids=["gap-node-memory"],
                )
            ],
        )

    def test_planner_prioritizes_blocking_gap_with_safe_collector(self) -> None:
        case = self._case_with_gap()
        plan = EvidencePlanner().plan(case)

        self.assertIsNone(plan.stop_reason)
        self.assertEqual(len(plan.requests), 1)
        request = plan.requests[0]
        self.assertEqual(request.gap_id, "gap-node-memory")
        self.assertEqual(request.collector, "linux_memory")
        self.assertTrue(request.read_only)

    def test_loop_collects_evidence_and_reaches_rca_candidate(self) -> None:
        case = self._case_with_gap()

        def linux_memory_collector(request, current_case):
            del current_case
            evidence = EvidenceItem(
                id="linux.memory.live",
                domain="linux",
                source="test-linux-memory",
                title="Live memory evidence",
                summary="Host memory pressure is confirmed by bounded read-only evidence.",
                severity="critical",
            )
            return EvidenceCollectionResult(
                request_id=request.id,
                evidence=[evidence],
                supporting_evidence={"memory-pressure": [evidence.id]},
                resolved_gap_ids=["gap-node-memory"],
            )

        result = AutonomousInvestigationLoop(
            collectors={"linux_memory": linux_memory_collector}
        ).run(case)

        self.assertEqual(result.stop_reason, "rca_candidate")
        self.assertEqual(result.total_requests_executed, 1)
        self.assertEqual(result.total_evidence_added, 1)
        self.assertIsNotNone(result.case.decision)
        self.assertEqual(result.case.decision.state, "rca_candidate")
        self.assertGreaterEqual(result.case.decision.confidence, 0.80)
        self.assertFalse(result.case.evidence_gaps)

    def test_loop_stops_when_safe_collector_is_not_registered(self) -> None:
        case = self._case_with_gap()
        result = AutonomousInvestigationLoop(collectors={}).run(case)

        self.assertEqual(result.stop_reason, "no_registered_safe_collector")
        self.assertEqual(result.total_requests_executed, 0)
        self.assertEqual(result.total_evidence_added, 0)
        self.assertTrue(
            any(event.action == "collector_unavailable" for event in case.audit_timeline)
        )

    def test_request_budget_stops_loop(self) -> None:
        case = self._case_with_gap()

        def collector_without_resolution(request, current_case):
            del current_case
            return EvidenceCollectionResult(
                request_id=request.id,
                evidence=[
                    EvidenceItem(
                        id="context-only",
                        domain="linux",
                        source="test",
                        title="Context only",
                        summary="Additional context that does not resolve the blocking gap.",
                    )
                ],
            )

        result = AutonomousInvestigationLoop(
            collectors={"linux_memory": collector_without_resolution},
            policy=InvestigationLoopPolicy(max_steps=3, max_total_requests=1),
        ).run(case)

        self.assertEqual(result.stop_reason, "request_budget_exhausted")
        self.assertEqual(result.total_requests_executed, 1)
        self.assertEqual(result.case.decision.state, "collect_more_evidence")


if __name__ == "__main__":
    unittest.main()
