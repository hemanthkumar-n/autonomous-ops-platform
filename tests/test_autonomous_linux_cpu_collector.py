from __future__ import annotations

import unittest

from app.investigation.autonomous_loop import AutonomousInvestigationLoop
from app.investigation.collectors import build_linux_cpu_collector
from app.investigation.models import (
    AffectedResource,
    EvidenceGap,
    Hypothesis,
    InvestigationCase,
)
from app.schemas.linux import LinuxCpuFinding, LinuxCpuInvestigation


class AutonomousLinuxCpuCollectorTests(unittest.TestCase):
    def _case(self) -> InvestigationCase:
        return InvestigationCase(
            id="INC-CPU-1",
            title="High CPU on node-a",
            source="test",
            affected_resources=[
                AffectedResource(domain="linux", kind="host", name="node-a")
            ],
            evidence_gaps=[
                EvidenceGap(
                    id="gap-cpu",
                    description="CPU state is unknown.",
                    recommended_checks=["aop investigate linux cpu"],
                    blocks_rca=True,
                )
            ],
            hypotheses=[
                Hypothesis(
                    id="cpu-contention",
                    statement="Runnable work is competing for CPU.",
                    required_evidence_ids=["linux.cpu.finding.cpu_saturation"],
                    missing_evidence_ids=["gap-cpu"],
                )
            ],
        )

    def _investigation(
        self, diagnosis: str, *, hostname: str = "node-a"
    ) -> LinuxCpuInvestigation:
        findings = []
        if diagnosis != "insufficient_evidence":
            findings.append(
                LinuxCpuFinding(
                    code=diagnosis,
                    severity="warning",
                    confidence=90,
                    summary=f"Observed {diagnosis}.",
                    evidence=[f"signal={diagnosis}"],
                    next="Inspect the affected workload.",
                )
            )
        return LinuxCpuInvestigation(
            status="diagnosed",
            hostname=hostname,
            platform="Linux",
            primary_diagnosis=diagnosis,
            severity="warning",
            confidence=90,
            summary=f"Observed {diagnosis}.",
            load_average=[8.0, 6.0, 4.0],
            cpu_count=4,
            vmstat_cpu={"us": 85, "sy": 5, "wa": 0, "st": 0},
            findings=findings,
            evidence_gaps=["Missing /proc access"] if diagnosis == "insufficient_evidence" else [],
            raw_evidence={
                "results": [
                    {"key": "vmstat", "status": "ok", "command": "vmstat 1 3"}
                ]
            },
        )

    def test_matching_finding_creates_evidence_backed_candidate(self) -> None:
        def workflow(**kwargs):
            self.assertEqual(kwargs, {"persist": False})
            return self._investigation("cpu_saturation"), None

        result = AutonomousInvestigationLoop(
            collectors={"linux_cpu": build_linux_cpu_collector(workflow)}
        ).run(self._case())

        self.assertEqual(result.stop_reason, "rca_candidate")
        self.assertEqual(result.total_requests_executed, 1)
        self.assertIsNone(result.case.root_cause)
        self.assertEqual(result.case.rca_candidate.hypothesis_id, "cpu-contention")
        self.assertEqual(
            result.case.rca_candidate.supporting_evidence_ids,
            ["linux.cpu.finding.cpu_saturation"],
        )
        self.assertEqual(result.case.evidence_by_id()["linux.cpu.vmstat"].command, "vmstat 1 3")
        self.assertFalse(result.case.evidence_gaps)

    def test_io_pressure_does_not_support_cpu_contention(self) -> None:
        result = AutonomousInvestigationLoop(
            collectors={
                "linux_cpu": build_linux_cpu_collector(
                    lambda **kwargs: (self._investigation("io_pressure_behind_load"), None)
                )
            }
        ).run(self._case())

        self.assertNotEqual(result.stop_reason, "rca_candidate")
        self.assertIsNone(result.case.rca_candidate)
        self.assertFalse(result.case.hypotheses[0].supporting_evidence_ids)
        self.assertIn("linux.cpu.finding.io_pressure_behind_load", result.case.evidence_by_id())

    def test_missing_cpu_evidence_keeps_blocking_gap(self) -> None:
        result = AutonomousInvestigationLoop(
            collectors={
                "linux_cpu": build_linux_cpu_collector(
                    lambda **kwargs: (self._investigation("insufficient_evidence"), None)
                )
            }
        ).run(self._case())

        self.assertNotEqual(result.stop_reason, "rca_candidate")
        self.assertIsNone(result.case.rca_candidate)
        self.assertEqual(result.case.evidence_gaps[0].id, "gap-cpu")

    def test_low_source_confidence_keeps_blocking_gap(self) -> None:
        investigation = self._investigation("cpu_saturation")
        investigation.confidence = 70
        investigation.evidence_gaps = ["vmstat sample incomplete"]
        result = AutonomousInvestigationLoop(
            collectors={
                "linux_cpu": build_linux_cpu_collector(
                    lambda **kwargs: (investigation, None)
                )
            }
        ).run(self._case())

        self.assertIsNone(result.case.rca_candidate)
        self.assertEqual(result.case.evidence_gaps[0].id, "gap-cpu")
        self.assertIn("linux.cpu.finding.cpu_saturation", result.case.evidence_by_id())
        self.assertFalse(result.case.hypotheses[0].supporting_evidence_ids)

    def test_other_host_evidence_is_rejected(self) -> None:
        result = AutonomousInvestigationLoop(
            collectors={
                "linux_cpu": build_linux_cpu_collector(
                    lambda **kwargs: (
                        self._investigation("cpu_saturation", hostname="node-b"),
                        None,
                    )
                )
            }
        ).run(self._case())

        self.assertEqual(result.total_requests_executed, 0)
        self.assertFalse(result.case.evidence)
        self.assertTrue(result.case.evidence_gaps)
        self.assertIsNone(result.case.rca_candidate)
        self.assertTrue(
            any(event.action == "collector_error" for event in result.case.audit_timeline)
        )


if __name__ == "__main__":
    unittest.main()
