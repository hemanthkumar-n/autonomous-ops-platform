from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.orchestration.linux_host_workflow import run_linux_host_workflow


def _investigation(
    diagnosis: str,
    severity: str,
    confidence: int,
    summary: str,
):
    finding = Mock()
    finding.code = diagnosis
    return Mock(
        status="diagnosed",
        hostname="worker-01",
        platform="Linux",
        primary_diagnosis=diagnosis,
        severity=severity,
        confidence=confidence,
        summary=summary,
        findings=[finding],
        evidence_gaps=[],
    )


class LinuxHostWorkflowTests(unittest.TestCase):
    @patch("app.orchestration.linux_host_workflow.store_linux_host_incident")
    @patch("app.orchestration.linux_host_workflow.run_linux_boot_kernel_workflow")
    @patch("app.orchestration.linux_host_workflow.run_linux_network_workflow")
    @patch("app.orchestration.linux_host_workflow.run_linux_cpu_workflow")
    @patch("app.orchestration.linux_host_workflow.run_linux_memory_workflow")
    @patch("app.orchestration.linux_host_workflow.run_linux_disk_workflow")
    def test_correlates_domains_and_persists_one_host_record(
        self,
        run_disk,
        run_memory,
        run_cpu,
        run_network,
        run_boot,
        store_host,
    ) -> None:
        run_disk.return_value = (
            _investigation(
                "multipath_path_loss",
                "critical",
                94,
                "Multipath paths failed.",
            ),
            None,
        )
        run_memory.return_value = (
            _investigation("no_immediate_memory_pressure", "info", 80, "OK"),
            None,
        )
        run_cpu.return_value = (
            _investigation("d_state_blocked_tasks", "warning", 92, "D state"),
            None,
        )
        run_network.return_value = (
            _investigation("no_immediate_network_issue", "info", 80, "OK"),
            None,
        )
        run_boot.return_value = (
            _investigation("no_immediate_boot_kernel_issue", "info", 80, "OK"),
            None,
        )
        store_host.return_value = "host.json"

        investigation, saved_path = run_linux_host_workflow(
            scan_path="/data",
            iface="ens5",
            pid=4242,
            top=20,
            recent_minutes=30,
            large_size_mb=500,
            persist=True,
        )

        self.assertEqual(saved_path, "host.json")
        self.assertEqual(
            investigation.primary_diagnosis,
            "disk_multipath_path_loss",
        )
        self.assertEqual(investigation.severity, "critical")
        self.assertEqual(
            [domain.domain for domain in investigation.domains],
            ["disk", "memory", "cpu", "network", "boot"],
        )
        self.assertIn("disk_multipath_path_loss", investigation.findings[0].code)
        run_disk.assert_called_once_with(
            scan_path="/data",
            top=20,
            recent_minutes=30,
            large_size_mb=500,
            persist=False,
        )
        run_memory.assert_called_once_with(
            pid=4242,
            top=20,
            recent_minutes=30,
            persist=False,
        )
        run_cpu.assert_called_once_with(top=20, persist=False)
        run_network.assert_called_once_with(iface="ens5", persist=False)
        run_boot.assert_called_once_with(recent_minutes=30, persist=False)
        store_host.assert_called_once_with(investigation)

    @patch("app.orchestration.linux_host_workflow.store_linux_host_incident")
    @patch("app.orchestration.linux_host_workflow.run_linux_boot_kernel_workflow")
    @patch("app.orchestration.linux_host_workflow.run_linux_network_workflow")
    @patch("app.orchestration.linux_host_workflow.run_linux_cpu_workflow")
    @patch("app.orchestration.linux_host_workflow.run_linux_memory_workflow")
    @patch("app.orchestration.linux_host_workflow.run_linux_disk_workflow")
    def test_no_persist_skips_host_memory(
        self,
        run_disk,
        run_memory,
        run_cpu,
        run_network,
        run_boot,
        store_host,
    ) -> None:
        clean = _investigation("no_immediate_disk_pressure", "info", 80, "OK")
        run_disk.return_value = (clean, None)
        run_memory.return_value = (
            _investigation("no_immediate_memory_pressure", "info", 80, "OK"),
            None,
        )
        run_cpu.return_value = (
            _investigation("no_immediate_cpu_pressure", "info", 80, "OK"),
            None,
        )
        run_network.return_value = (
            _investigation("no_immediate_network_issue", "info", 80, "OK"),
            None,
        )
        run_boot.return_value = (
            _investigation("no_immediate_boot_kernel_issue", "info", 80, "OK"),
            None,
        )

        _, saved_path = run_linux_host_workflow(persist=False)

        self.assertIsNone(saved_path)
        store_host.assert_not_called()


if __name__ == "__main__":
    unittest.main()
