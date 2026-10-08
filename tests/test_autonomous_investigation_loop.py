from __future__ import annotations

import unittest

from app.investigation.autonomous_loop import (
    AutonomousInvestigationLoop,
    EvidenceCollectionResult,
    InvestigationLoopPolicy,
)
from app.investigation.collectors import build_linux_memory_collector
from app.investigation.evidence_planner import EvidencePlanner
from app.investigation.models import (
    AffectedResource,
    EvidenceGap,
    Hypothesis,
    InvestigationCase,
)
from app.schemas.evidence import EvidenceItem
from app.schemas.linux import LinuxMemoryFinding, LinuxMemoryInvestigation


class AutonomousInvestigationLoopTests(unittest.TestCase):
    def _case_with_gap(self) -> InvestigationCase:
        return InvestigationCase(
            id="INC-AUTO-1",
            title="Possible memory exhaustion",
            source="test",
            affected_resources=[
                AffectedResource(
                    domain="kubernetes",
                    kind="pod",
                    name="api-abc",
                    namespace="payments",
                    cluster="cluster-a",
                    node="node-3",
                ),
                AffectedResource(domain="linux", kind="host", name="node-3"),
            ],
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

    def test_planner_prioritizes_gap_and_carries_resource_identity(self) -> None:
        request = EvidencePlanner().plan(self._case_with_gap()).requests[0]
        self.assertEqual(request.collector, "linux_memory")
        self.assertTrue(request.read_only)
        self.assertEqual(request.metadata["cluster"], "cluster-a")
        self.assertEqual(request.metadata["namespace"], "payments")
        self.assertEqual(request.metadata["pod"], "api-abc")
        self.assertEqual(request.metadata["node"], "node-3")
        self.assertEqual(request.metadata["host"], "node-3")

    def test_loop_creates_explicit_candidate_with_why_and_keeps_root_cause_unconfirmed(self) -> None:
        case = self._case_with_gap()

        def collector(request, current_case):
            del current_case
            evidence = EvidenceItem(
                id="linux.memory.live",
                domain="linux",
                source="test-linux-memory",
                title="Live memory evidence",
                summary="Host memory pressure is confirmed.",
                severity="critical",
            )
            return EvidenceCollectionResult(
                request_id=request.id,
                evidence=[evidence],
                supporting_evidence={"memory-pressure": [evidence.id]},
                supporting_reasons={"memory-pressure": ["MemAvailable is critically low."]},
                contradicting_reasons={
                    "memory-pressure": ["Container-only exhaustion is not independently proven."]
                },
                resolved_gap_ids=["gap-node-memory"],
            )

        result = AutonomousInvestigationLoop(
            collectors={"linux_memory": collector}
        ).run(case)

        self.assertEqual(result.stop_reason, "rca_candidate")
        self.assertIsNotNone(result.case.rca_candidate)
        self.assertEqual(result.case.rca_candidate.hypothesis_id, "memory-pressure")
        self.assertIn("MemAvailable is critically low.", result.case.rca_candidate.why)
        self.assertTrue(result.case.rca_candidate.why_not)
        self.assertIsNone(result.case.root_cause)

    def test_real_linux_memory_adapter_contract_with_injected_workflow(self) -> None:
        case = InvestigationCase(
            id="INC-AUTO-REAL-1",
            title="OOM investigation",
            source="test",
            affected_resources=[AffectedResource(domain="linux", kind="host", name="node-a")],
            evidence_gaps=[
                EvidenceGap(
                    id="gap-memory",
                    description="Need Linux memory evidence",
                    priority="critical",
                    recommended_checks=["aop investigate linux memory"],
                    blocks_rca=True,
                )
            ],
            hypotheses=[
                Hypothesis(
                    id="kernel-oom",
                    statement="Kernel OOM caused the incident.",
                    required_evidence_ids=["linux.memory.finding.1.kernel_oom_kill"],
                    missing_evidence_ids=["gap-memory"],
                )
            ],
        )

        def fake_workflow(**kwargs):
            self.assertFalse(kwargs["persist"])
            investigation = LinuxMemoryInvestigation(
                status="diagnosed",
                hostname="node-a",
                platform="linux",
                primary_diagnosis="kernel_oom_kill",
                severity="critical",
                confidence=98,
                summary="Recent kernel evidence contains OOM kill activity.",
                oom_events=["Out of memory: Killed process 4242"],
                findings=[
                    LinuxMemoryFinding(
                        code="kernel_oom_kill",
                        severity="critical",
                        confidence=98,
                        summary="Kernel OOM kill confirmed.",
                        evidence=["Out of memory: Killed process 4242"],
                        next="Identify the victim workload.",
                    )
                ],
            )
            return investigation, None

        result = AutonomousInvestigationLoop(
            collectors={"linux_memory": build_linux_memory_collector(fake_workflow)}
        ).run(case)

        self.assertEqual(result.stop_reason, "rca_candidate")
        self.assertIsNotNone(result.case.rca_candidate)
        self.assertIn("Kernel OOM kill confirmed.", result.case.rca_candidate.why)
        self.assertTrue(any(item.source == "aop-linux-memory" for item in result.case.evidence))

    def test_loop_stops_when_safe_collector_is_not_registered(self) -> None:
        case = self._case_with_gap()
        result = AutonomousInvestigationLoop(collectors={}).run(case)
        self.assertEqual(result.stop_reason, "no_registered_safe_collector")
        self.assertEqual(result.total_requests_executed, 0)
        self.assertIsNone(result.case.rca_candidate)

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
                        summary="Context that does not resolve the blocking gap.",
                    )
                ],
            )

        result = AutonomousInvestigationLoop(
            collectors={"linux_memory": collector_without_resolution},
            policy=InvestigationLoopPolicy(max_steps=3, max_total_requests=1),
        ).run(case)
        self.assertEqual(result.stop_reason, "request_budget_exhausted")
        self.assertEqual(result.case.decision.state, "collect_more_evidence")
        self.assertIsNone(result.case.rca_candidate)


if __name__ == "__main__":
    unittest.main()
