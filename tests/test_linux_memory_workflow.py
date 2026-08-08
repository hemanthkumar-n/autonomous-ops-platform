from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.orchestration.linux_memory_workflow import run_linux_memory_workflow


class LinuxMemoryWorkflowTests(unittest.TestCase):
    @patch(
        "app.orchestration.linux_memory_workflow.store_linux_memory_incident"
    )
    @patch("app.orchestration.linux_memory_workflow.analyze_memory_evidence")
    @patch("app.orchestration.linux_memory_workflow.collect_memory")
    def test_collects_analyzes_and_persists(
        self,
        collect_memory,
        analyze_memory_evidence,
        store_linux_memory_incident,
    ) -> None:
        collect_memory.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_memory_evidence.return_value = investigation
        store_linux_memory_incident.return_value = "memory.json"

        result, saved_path = run_linux_memory_workflow(
            pid=4242,
            top=20,
            recent_minutes=30,
            persist=True,
        )

        self.assertIs(result, investigation)
        self.assertEqual(saved_path, "memory.json")
        collect_memory.assert_called_once_with(
            pid=4242,
            top=20,
            recent_minutes=30,
        )
        analyze_memory_evidence.assert_called_once_with(
            collect_memory.return_value
        )
        store_linux_memory_incident.assert_called_once_with(investigation)

    @patch(
        "app.orchestration.linux_memory_workflow.store_linux_memory_incident"
    )
    @patch("app.orchestration.linux_memory_workflow.analyze_memory_evidence")
    @patch("app.orchestration.linux_memory_workflow.collect_memory")
    def test_no_persist_skips_memory(
        self,
        collect_memory,
        analyze_memory_evidence,
        store_linux_memory_incident,
    ) -> None:
        collect_memory.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_memory_evidence.return_value = investigation

        _, saved_path = run_linux_memory_workflow(persist=False)

        self.assertIsNone(saved_path)
        store_linux_memory_incident.assert_not_called()


if __name__ == "__main__":
    unittest.main()
