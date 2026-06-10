from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from app.cli.main import main
from app.schemas.linux import (
    LinuxDiskFinding,
    LinuxDiskInvestigation,
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
        run_workflow.assert_called_once_with(
            scan_path="/var",
            top=20,
            recent_minutes=30,
            large_size_mb=500,
            persist=False,
        )


if __name__ == "__main__":
    unittest.main()
