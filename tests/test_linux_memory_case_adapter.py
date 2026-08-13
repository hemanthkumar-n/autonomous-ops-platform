import unittest

from app.investigation.adapters import linux_memory_to_case
from app.schemas.linux import LinuxMemoryFinding, LinuxMemoryInvestigation


class LinuxMemoryCaseAdapterTests(unittest.TestCase):
    def test_high_confidence_memory_result_becomes_rca_candidate(self) -> None:
        investigation = LinuxMemoryInvestigation(
            status="diagnosed",
            hostname="node-a",
            platform="linux",
            primary_diagnosis="kernel_oom_kill",
            severity="critical",
            confidence=98,
            summary="Recent kernel evidence contains OOM kill activity.",
            mem_total_kb=1_000_000,
            mem_available_kb=40_000,
            mem_available_percent=4.0,
            oom_events=["Out of memory: Killed process 4242"],
            findings=[
                LinuxMemoryFinding(
                    code="kernel_oom_kill",
                    severity="critical",
                    confidence=98,
                    summary="Kernel OOM kill confirmed.",
                    evidence=["Out of memory: Killed process 4242"],
                    next="Identify the victim process and owning workload.",
                )
            ],
        )

        case = linux_memory_to_case(investigation, case_id="case-1", environment="test")

        self.assertEqual(case.id, "case-1")
        self.assertIsNotNone(case.decision)
        assert case.decision is not None
        self.assertEqual(case.decision.state, "rca_candidate")
        self.assertEqual(case.root_cause, "kernel_oom_kill")
        self.assertGreaterEqual(case.decision.confidence, 0.98)
        self.assertTrue(any(item.id == "linux.memory.kernel_oom" for item in case.evidence))

    def test_insufficient_memory_evidence_blocks_rca(self) -> None:
        investigation = LinuxMemoryInvestigation(
            status="diagnosed",
            hostname="node-b",
            platform="linux",
            primary_diagnosis="insufficient_evidence",
            severity="info",
            confidence=30,
            summary="Memory evidence is insufficient for diagnosis.",
            evidence_gaps=["meminfo: unavailable", "vmstat: missing"],
            findings=[
                LinuxMemoryFinding(
                    code="insufficient_evidence",
                    severity="info",
                    confidence=30,
                    summary="Required memory evidence is unavailable.",
                    evidence=[],
                    next="Collect meminfo and vmstat evidence.",
                )
            ],
        )

        case = linux_memory_to_case(investigation, case_id="case-2")

        self.assertIsNotNone(case.decision)
        assert case.decision is not None
        self.assertEqual(case.decision.state, "collect_more_evidence")
        self.assertIsNone(case.root_cause)
        self.assertTrue(case.decision.blocked_by_gaps)
        self.assertTrue(all(gap.blocks_rca for gap in case.evidence_gaps))

    def test_cgroup_non_numeric_values_do_not_break_adapter(self) -> None:
        investigation = LinuxMemoryInvestigation(
            status="diagnosed",
            hostname="node-c",
            platform="linux",
            pid=99,
            primary_diagnosis="cgroup_memory_high",
            severity="warning",
            confidence=85,
            summary="Cgroup memory.high pressure detected.",
            cgroup_memory={
                "memory_max": "max",
                "event_high": 2,
                "event_oom": 0,
            },
            findings=[
                LinuxMemoryFinding(
                    code="cgroup_memory_high",
                    severity="warning",
                    confidence=85,
                    summary="memory.high events are active.",
                    evidence=["event_high=2"],
                    next="Inspect workload memory growth and cgroup limits.",
                )
            ],
        )

        case = linux_memory_to_case(investigation, case_id="case-3")

        self.assertIsNotNone(case.decision)
        assert case.decision is not None
        self.assertEqual(case.decision.state, "rca_candidate")
        cgroup = next(item for item in case.evidence if item.id == "linux.memory.cgroup")
        self.assertEqual(cgroup.severity, "warning")
        self.assertTrue(any(resource.kind == "process" for resource in case.affected_resources))


if __name__ == "__main__":
    unittest.main()
