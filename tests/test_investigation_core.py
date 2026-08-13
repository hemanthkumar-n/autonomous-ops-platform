from __future__ import annotations

import unittest

from app.investigation.confidence import evaluate_case_confidence
from app.investigation.models import EvidenceGap, Hypothesis, InvestigationCase
from app.investigation.orchestrator import InvestigationOrchestrator
from app.investigation.reasoning import build_reasoning_summary
from app.schemas.evidence import EvidenceItem


class InvestigationCoreTests(unittest.TestCase):
    def _evidence(self, evidence_id: str, summary: str) -> EvidenceItem:
        return EvidenceItem(
            id=evidence_id,
            domain="kubernetes",
            source="test",
            title=evidence_id,
            summary=summary,
        )

    def test_strong_supported_hypothesis_becomes_rca_candidate(self) -> None:
        case = InvestigationCase(
            id="INC-1",
            title="Pod OOM",
            source="test",
            evidence=[
                self._evidence("termination", "Container terminated OOMKilled"),
                self._evidence("limit", "Peak memory approached configured limit"),
                self._evidence("node", "Node MemoryPressure is false"),
            ],
            hypotheses=[
                Hypothesis(
                    id="container-limit",
                    statement="Container memory limit exhaustion",
                    supporting_evidence_ids=["termination", "limit", "node"],
                    required_evidence_ids=["termination", "limit", "node"],
                )
            ],
        )

        decision = evaluate_case_confidence(case)

        self.assertEqual(decision.state, "rca_candidate")
        self.assertEqual(decision.leading_hypothesis_id, "container-limit")
        self.assertGreaterEqual(decision.confidence, 0.80)
        self.assertEqual(case.hypotheses[0].status, "supported")

    def test_blocking_gap_prevents_rca_even_with_support(self) -> None:
        case = InvestigationCase(
            id="INC-2",
            title="Possible OOM",
            source="test",
            evidence=[self._evidence("termination", "OOMKilled observed")],
            evidence_gaps=[
                EvidenceGap(
                    id="node-memory",
                    description="Node memory state unavailable",
                    priority="high",
                    blocks_rca=True,
                    recommended_checks=["aop investigate linux memory"],
                )
            ],
            hypotheses=[
                Hypothesis(
                    id="node-pressure",
                    statement="Node-wide memory pressure",
                    supporting_evidence_ids=["termination"],
                    required_evidence_ids=["termination"],
                )
            ],
        )

        decision = evaluate_case_confidence(case)

        self.assertEqual(decision.state, "collect_more_evidence")
        self.assertIn("node-memory", decision.blocked_by_gaps)
        self.assertIn("aop investigate linux memory", decision.next_checks)

    def test_contradicting_evidence_reduces_confidence(self) -> None:
        case = InvestigationCase(
            id="INC-3",
            title="Node memory hypothesis",
            source="test",
            evidence=[
                self._evidence("oom", "Container OOMKilled"),
                self._evidence("pressure", "Node MemoryPressure is false"),
            ],
            hypotheses=[
                Hypothesis(
                    id="node-pressure",
                    statement="Node-wide memory pressure",
                    supporting_evidence_ids=["oom"],
                    contradicting_evidence_ids=["pressure"],
                    required_evidence_ids=["oom", "pressure"],
                )
            ],
        )

        decision = evaluate_case_confidence(case)

        self.assertNotEqual(decision.state, "rca_candidate")
        self.assertLess(decision.confidence, 0.80)

    def test_reasoning_summary_exposes_why_and_why_not(self) -> None:
        hypothesis = Hypothesis(
            id="container-limit",
            statement="Container limit exhaustion",
            supporting_evidence_ids=["limit"],
            contradicting_evidence_ids=["node"],
            missing_evidence_ids=["heap-profile"],
            why=["Repeated restart pattern matches memory exhaustion"],
            why_not=["Node-wide pressure is not observed"],
        )
        case = InvestigationCase(
            id="INC-4",
            title="OOM reasoning",
            source="test",
            evidence=[
                self._evidence("limit", "Peak memory approached configured limit"),
                self._evidence("node", "Node MemoryPressure is false"),
            ],
            hypotheses=[hypothesis],
        )

        summary = build_reasoning_summary(case, hypothesis)

        self.assertIn("Peak memory approached configured limit", summary["why"])
        self.assertIn("Node MemoryPressure is false", summary["why_not"])
        self.assertIn("heap-profile", summary["missing_evidence"])
        self.assertFalse(summary["evidence_complete"])

    def test_reasoning_summary_selects_leading_hypothesis(self) -> None:
        case = InvestigationCase(
            id="INC-4B",
            title="Automatic reasoning selection",
            source="test",
            evidence=[self._evidence("oom", "Kernel OOM kill confirmed")],
            hypotheses=[
                Hypothesis(
                    id="kernel-oom",
                    statement="Kernel OOM occurred",
                    supporting_evidence_ids=["oom"],
                    required_evidence_ids=["oom"],
                )
            ],
        )
        evaluate_case_confidence(case)

        summary = build_reasoning_summary(case)

        self.assertEqual(summary["hypothesis_id"], "kernel-oom")
        self.assertIn("Kernel OOM kill confirmed", summary["why"])

    def test_orchestrator_adds_audit_event_and_reasoning(self) -> None:
        case = InvestigationCase(
            id="INC-5",
            title="CPU saturation",
            source="test",
            evidence=[
                EvidenceItem(
                    id="cpu",
                    domain="linux",
                    source="test",
                    title="cpu",
                    summary="CPU utilization is sustained above threshold",
                )
            ],
            hypotheses=[
                Hypothesis(
                    id="cpu-saturation",
                    statement="CPU saturation",
                    supporting_evidence_ids=["cpu"],
                    required_evidence_ids=["cpu"],
                )
            ],
        )
        orchestrator = InvestigationOrchestrator()

        decision = orchestrator.evaluate(case)
        reasoning = orchestrator.reasoning(case)

        self.assertEqual(decision.state, "rca_candidate")
        self.assertEqual(case.audit_timeline[-1].action, "confidence_evaluated")
        self.assertEqual(reasoning["hypothesis"]["hypothesis_id"], "cpu-saturation")


if __name__ == "__main__":
    unittest.main()
