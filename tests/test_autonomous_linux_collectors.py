from __future__ import annotations

import unittest

from app.investigation.collectors.linux_cpu import build_linux_cpu_collector
from app.investigation.collectors.linux_disk import build_linux_disk_collector
from app.investigation.collectors.linux_network import build_linux_network_collector
from app.investigation.evidence_planner import EvidencePlanner, EvidenceRequest
from app.investigation.models import EvidenceGap, Hypothesis, InvestigationCase
from app.schemas.linux import (
    LinuxCpuFinding,
    LinuxCpuInvestigation,
    LinuxDiskFinding,
    LinuxDiskInvestigation,
    LinuxNetworkFinding,
    LinuxNetworkInvestigation,
)


class AutonomousLinuxCollectorTests(unittest.TestCase):
    def _case(self, hypothesis_id: str, gap_id: str) -> InvestigationCase:
        return InvestigationCase(
            id="INC-COLLECTOR-1",
            title="Collector contract test",
            source="test",
            evidence_gaps=[
                EvidenceGap(
                    id=gap_id,
                    description="Evidence is missing.",
                    blocks_rca=True,
                )
            ],
            hypotheses=[
                Hypothesis(
                    id=hypothesis_id,
                    statement="Domain pressure caused the incident.",
                    missing_evidence_ids=[gap_id],
                )
            ],
        )

    def test_cpu_collector_normalizes_findings_and_disables_persistence(self) -> None:
        calls = {}

        def workflow(**kwargs):
            calls.update(kwargs)
            return (
                LinuxCpuInvestigation(
                    status="diagnosed",
                    hostname="node-a",
                    platform="linux",
                    primary_diagnosis="cpu_saturation",
                    severity="critical",
                    confidence=92,
                    summary="CPU saturation confirmed.",
                    load_average=[8.0, 7.0, 6.0],
                    cpu_count=4,
                    running_tasks=7,
                    total_tasks=201,
                    findings=[
                        LinuxCpuFinding(
                            code="cpu_saturation",
                            severity="critical",
                            confidence=92,
                            summary="Runnable demand exceeds CPU capacity.",
                            evidence=["load=8 cpu=4"],
                            next="Inspect top CPU consumers.",
                        )
                    ],
                ),
                None,
            )

        case = self._case("cpu-pressure", "gap-cpu")
        request = EvidenceRequest(
            id="req-cpu",
            gap_id="gap-cpu",
            collector="linux_cpu",
            instruction="aop investigate linux cpu",
            purpose="Confirm CPU pressure.",
        )
        result = build_linux_cpu_collector(workflow)(request, case)

        self.assertFalse(calls["persist"])
        self.assertIn("cpu-pressure", result.supporting_evidence)
        self.assertEqual(result.resolved_gap_ids, ["gap-cpu"])
        self.assertTrue(any(item.id.startswith("linux.cpu.finding") for item in result.evidence))

    def test_disk_collector_forwards_path_and_normalizes_storage_evidence(self) -> None:
        calls = {}

        def workflow(**kwargs):
            calls.update(kwargs)
            return (
                LinuxDiskInvestigation(
                    status="diagnosed",
                    hostname="node-b",
                    path="/var/lib/containerd",
                    platform="linux",
                    primary_diagnosis="filesystem_capacity",
                    severity="critical",
                    confidence=90,
                    summary="Filesystem capacity is exhausted.",
                    filesystem_use_percent=97.5,
                    inode_use_percent=61.0,
                    mount_source="/dev/mapper/vg-data",
                    filesystem_type="xfs",
                    mount_point="/var/lib/containerd",
                    findings=[
                        LinuxDiskFinding(
                            code="filesystem_capacity",
                            severity="critical",
                            confidence=90,
                            summary="Filesystem usage crossed the critical threshold.",
                            evidence=["use=97.5%"],
                            next="Inspect largest paths and growth.",
                        )
                    ],
                ),
                None,
            )

        case = self._case("disk-pressure", "gap-disk")
        request = EvidenceRequest(
            id="req-disk",
            gap_id="gap-disk",
            collector="linux_disk",
            instruction="aop investigate linux disk",
            purpose="Confirm disk pressure.",
            metadata={"path": "/var/lib/containerd"},
        )
        result = build_linux_disk_collector(workflow)(request, case)

        self.assertEqual(calls["scan_path"], "/var/lib/containerd")
        self.assertFalse(calls["persist"])
        self.assertEqual(result.resolved_gap_ids, ["gap-disk"])
        summary = next(item for item in result.evidence if item.id == "linux.disk.summary")
        self.assertEqual(summary.structured["filesystem_use_percent"], 97.5)

    def test_network_collector_forwards_interface_and_normalizes_signals(self) -> None:
        calls = {}

        def workflow(**kwargs):
            calls.update(kwargs)
            return (
                LinuxNetworkInvestigation(
                    status="diagnosed",
                    hostname="node-c",
                    platform="linux",
                    iface="eth0",
                    primary_diagnosis="interface_errors",
                    severity="warning",
                    confidence=88,
                    summary="NIC error counters are increasing.",
                    interfaces=["eth0 UP"],
                    routes=["default via 10.0.0.1"],
                    resolvers=["nameserver 10.0.0.2"],
                    nic_signals={"rx_errors": "12", "tx_errors": "3"},
                    findings=[
                        LinuxNetworkFinding(
                            code="interface_errors",
                            severity="warning",
                            confidence=88,
                            summary="Interface error counters indicate packet-path pressure.",
                            evidence=["rx_errors=12", "tx_errors=3"],
                            next="Inspect NIC counters and upstream path.",
                        )
                    ],
                ),
                None,
            )

        case = self._case("network-pressure", "gap-network")
        request = EvidenceRequest(
            id="req-network",
            gap_id="gap-network",
            collector="linux_network",
            instruction="aop investigate linux network",
            purpose="Confirm network pressure.",
            metadata={"iface": "eth0"},
        )
        result = build_linux_network_collector(workflow)(request, case)

        self.assertEqual(calls["iface"], "eth0")
        self.assertFalse(calls["persist"])
        self.assertEqual(result.resolved_gap_ids, ["gap-network"])
        summary = next(item for item in result.evidence if item.id == "linux.network.summary")
        self.assertEqual(summary.structured["nic_signals"]["rx_errors"], "12")

    def test_planner_selects_cpu_disk_and_network_collectors(self) -> None:
        case = InvestigationCase(
            id="INC-MULTI-1",
            title="Multi-domain host pressure",
            source="test",
            evidence_gaps=[
                EvidenceGap(
                    id="gap-cpu",
                    description="CPU evidence missing",
                    recommended_checks=["aop investigate linux cpu"],
                    blocks_rca=True,
                ),
                EvidenceGap(
                    id="gap-disk",
                    description="Disk evidence missing",
                    recommended_checks=["aop investigate linux disk"],
                    blocks_rca=True,
                ),
                EvidenceGap(
                    id="gap-network",
                    description="Network evidence missing",
                    recommended_checks=["aop investigate linux network"],
                    blocks_rca=True,
                ),
            ],
            hypotheses=[Hypothesis(id="host-pressure", statement="Host pressure")],
        )

        plan = EvidencePlanner().plan(case)
        collectors = {request.collector for request in plan.requests}
        self.assertEqual(collectors, {"linux_cpu", "linux_disk", "linux_network"})


if __name__ == "__main__":
    unittest.main()
