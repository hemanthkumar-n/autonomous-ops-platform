from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.orchestration.linux_cpu_workflow import run_linux_cpu_workflow


class LinuxCpuWorkflowTests(unittest.TestCase):
    @patch(
        "app.orchestration.linux_cpu_workflow.store_linux_cpu_incident"
    )
    @patch("app.orchestration.linux_cpu_workflow.analyze_cpu_evidence")
    @patch("app.orchestration.linux_cpu_workflow.collect_cpu")
    def test_collects_analyzes_and_persists(
        self,
        collect_cpu,
        analyze_cpu_evidence,
        store_linux_cpu_incident,
    ) -> None:
        collect_cpu.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_cpu_evidence.return_value = investigation
        store_linux_cpu_incident.return_value = "memory.json"

        result, saved_path = run_linux_cpu_workflow(
            top=20,
            persist=True,
        )

        self.assertIs(result, investigation)
        self.assertEqual(saved_path, "memory.json")
        collect_cpu.assert_called_once_with(top=20)
        analyze_cpu_evidence.assert_called_once_with(collect_cpu.return_value)
        store_linux_cpu_incident.assert_called_once_with(investigation)

    @patch(
        "app.orchestration.linux_cpu_workflow.store_linux_cpu_incident"
    )
    @patch("app.orchestration.linux_cpu_workflow.analyze_cpu_evidence")
    @patch("app.orchestration.linux_cpu_workflow.collect_cpu")
    def test_no_persist_skips_memory(
        self,
        collect_cpu,
        analyze_cpu_evidence,
        store_linux_cpu_incident,
    ) -> None:
        collect_cpu.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_cpu_evidence.return_value = investigation

        _, saved_path = run_linux_cpu_workflow(persist=False)

        self.assertIsNone(saved_path)
        store_linux_cpu_incident.assert_not_called()


if __name__ == "__main__":
    unittest.main()
