from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.orchestration.linux_disk_workflow import run_linux_disk_workflow


class LinuxDiskWorkflowTests(unittest.TestCase):
    @patch(
        "app.orchestration.linux_disk_workflow.store_linux_disk_incident"
    )
    @patch("app.orchestration.linux_disk_workflow.analyze_disk_evidence")
    @patch("app.orchestration.linux_disk_workflow.collect_disk")
    def test_collects_analyzes_and_persists(
        self,
        collect_disk,
        analyze_disk_evidence,
        store_linux_disk_incident,
    ) -> None:
        collect_disk.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_disk_evidence.return_value = investigation
        store_linux_disk_incident.return_value = "memory.json"

        result, saved_path = run_linux_disk_workflow(
            scan_path="/var",
            top=20,
            recent_minutes=30,
            large_size_mb=500,
            persist=True,
        )

        self.assertIs(result, investigation)
        self.assertEqual(saved_path, "memory.json")
        collect_disk.assert_called_once_with(
            scan_path="/var",
            top=20,
            recent_minutes=30,
            large_size_mb=500,
        )
        analyze_disk_evidence.assert_called_once_with(
            collect_disk.return_value
        )
        store_linux_disk_incident.assert_called_once_with(investigation)

    @patch(
        "app.orchestration.linux_disk_workflow.store_linux_disk_incident"
    )
    @patch("app.orchestration.linux_disk_workflow.analyze_disk_evidence")
    @patch("app.orchestration.linux_disk_workflow.collect_disk")
    def test_no_persist_skips_memory(
        self,
        collect_disk,
        analyze_disk_evidence,
        store_linux_disk_incident,
    ) -> None:
        collect_disk.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_disk_evidence.return_value = investigation

        _, saved_path = run_linux_disk_workflow(persist=False)

        self.assertIsNone(saved_path)
        store_linux_disk_incident.assert_not_called()


if __name__ == "__main__":
    unittest.main()
