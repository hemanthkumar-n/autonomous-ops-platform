from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from app.cli.main import main
from app.schemas.linux import (
    LinuxDiskFinding,
    LinuxDiskInvestigation,
    LinuxMemoryFinding,
    LinuxMemoryInvestigation,
)


def _investigation() -> LinuxDiskInvestigation:
    return LinuxDiskInvestigation(
        status="diagnosed",
        hostname="db-01",
        path="/var",
        platform="Linux",
        primary_diagnosis="inode_exhaustion",
        severity="critical",
        confidence=98,
        summary="Inode utilization is 97%.",
        filesystem_use_percent=60,
        inode_use_percent=97,
        findings=[
            LinuxDiskFinding(
                code="inode_exhaustion",
                severity="critical",
                confidence=98,
                summary="Inode utilization is 97%.",
                evidence=["/dev/sda1 100000 97000 3000 97% /var"],
                next="Find directories creating many small files.",
                next_explanation=(
                    "Inode exhaustion can cause writes to fail even when "
                    "byte capacity is available."
                ),
            )
        ],
    )


def _memory_investigation() -> LinuxMemoryInvestigation:
    return LinuxMemoryInvestigation(
        status="diagnosed",
        hostname="web-01",
        platform="Linux",
        pid=4242,
        primary_diagnosis="kernel_oom_kill",
        severity="critical",
        confidence=98,
        summary="Recent kernel evidence contains OOM kill activity.",
        mem_total_kb=16_000_000,
        mem_available_kb=1_000_000,
        mem_available_percent=6.25,
        swap_total_kb=2_000_000,
        swap_free_kb=1_000_000,
        swap_used_percent=50.0,
        swap_in_per_second=20,
        swap_out_per_second=0,
        findings=[
            LinuxMemoryFinding(
                code="kernel_oom_kill",
                severity="critical",
                confidence=98,
                summary="Recent kernel evidence contains OOM kill activity.",
                evidence=["kernel: Out of memory: Killed process 4242"],
                next="Identify the victim process and owning service.",
                next_explanation=(
                    "Kernel OOM evidence proves a process or cgroup could "
                    "not satisfy memory allocation."
                ),
            )
        ],
    )


class LinuxInvestigateCLITests(unittest.TestCase):
    @patch(
        "app.orchestration.linux_disk_workflow.run_linux_disk_workflow"
    )
    def test_summary_renders_diagnosis_and_memory(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_investigation(), "memory.json")

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "disk",
                "--path",
                "/var",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("inode_exhaustion", result.output)
        self.assertIn("Inode use: 97%", result.output)
        self.assertIn("Why:", result.output)
        self.assertIn("byte capacity is available", result.output)
        self.assertIn("memory.json", result.output)

    @patch(
        "app.orchestration.linux_disk_workflow.run_linux_disk_workflow"
    )
    def test_json_forwards_scope_and_no_persist(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_investigation(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "disk",
                "--path",
                "/var",
                "--top",
                "20",
                "--recent-minutes",
                "30",
                "--large-size-mb",
                "500",
                "--format",
                "json",
                "--no-persist",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["primary_diagnosis"], "inode_exhaustion")
        self.assertIn(
            "byte capacity is available",
            payload["findings"][0]["next_explanation"],
        )
        run_workflow.assert_called_once_with(
            scan_path="/var",
            top=20,
            recent_minutes=30,
            large_size_mb=500,
            persist=False,
        )

    @patch(
        "app.orchestration.linux_memory_workflow.run_linux_memory_workflow"
    )
    def test_memory_summary_renders_diagnosis_and_memory(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_memory_investigation(), "memory.json")

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "memory",
                "--pid",
                "4242",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("kernel_oom_kill", result.output)
        self.assertIn("MemAvailable: 6.2%", result.output)
        self.assertIn("Swap activity: si=20 so=0", result.output)
        self.assertIn("Why:", result.output)
        self.assertIn("memory.json", result.output)

    @patch(
        "app.orchestration.linux_memory_workflow.run_linux_memory_workflow"
    )
    def test_memory_json_forwards_scope_and_no_persist(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_memory_investigation(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "memory",
                "--pid",
                "4242",
                "--top",
                "20",
                "--recent-minutes",
                "30",
                "--format",
                "json",
                "--no-persist",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["primary_diagnosis"], "kernel_oom_kill")
        self.assertIn(
            "memory allocation",
            payload["findings"][0]["next_explanation"],
        )
        run_workflow.assert_called_once_with(
            pid=4242,
            top=20,
            recent_minutes=30,
            persist=False,
        )


if __name__ == "__main__":
    unittest.main()
