from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.orchestration.linux_service_workflow import run_linux_service_workflow


class LinuxServiceWorkflowTests(unittest.TestCase):
    @patch(
        "app.orchestration.linux_service_workflow.store_linux_service_incident"
    )
    @patch("app.orchestration.linux_service_workflow.analyze_service_evidence")
    @patch("app.orchestration.linux_service_workflow.collect_service")
    def test_collects_analyzes_and_persists(
        self,
        collect_service,
        analyze_service_evidence,
        store_linux_service_incident,
    ) -> None:
        collect_service.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_service_evidence.return_value = investigation
        store_linux_service_incident.return_value = "memory.json"

        result, saved_path = run_linux_service_workflow(
            service="nginx",
            persist=True,
        )

        self.assertIs(result, investigation)
        self.assertEqual(saved_path, "memory.json")
        collect_service.assert_called_once_with(service="nginx")
        analyze_service_evidence.assert_called_once_with(
            collect_service.return_value
        )
        store_linux_service_incident.assert_called_once_with(investigation)

    @patch(
        "app.orchestration.linux_service_workflow.store_linux_service_incident"
    )
    @patch("app.orchestration.linux_service_workflow.analyze_service_evidence")
    @patch("app.orchestration.linux_service_workflow.collect_service")
    def test_no_persist_skips_memory(
        self,
        collect_service,
        analyze_service_evidence,
        store_linux_service_incident,
    ) -> None:
        collect_service.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_service_evidence.return_value = investigation

        _, saved_path = run_linux_service_workflow(
            service="nginx",
            persist=False,
        )

        self.assertIsNone(saved_path)
        store_linux_service_incident.assert_not_called()


if __name__ == "__main__":
    unittest.main()
