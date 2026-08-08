from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.orchestration.linux_network_workflow import run_linux_network_workflow


class LinuxNetworkWorkflowTests(unittest.TestCase):
    @patch(
        "app.orchestration.linux_network_workflow.store_linux_network_incident"
    )
    @patch("app.orchestration.linux_network_workflow.analyze_network_evidence")
    @patch("app.orchestration.linux_network_workflow.collect_network")
    def test_collects_analyzes_and_persists(
        self,
        collect_network,
        analyze_network_evidence,
        store_linux_network_incident,
    ) -> None:
        collect_network.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_network_evidence.return_value = investigation
        store_linux_network_incident.return_value = "memory.json"

        result, saved_path = run_linux_network_workflow(
            iface="ens5",
            persist=True,
        )

        self.assertIs(result, investigation)
        self.assertEqual(saved_path, "memory.json")
        collect_network.assert_called_once_with(iface="ens5")
        analyze_network_evidence.assert_called_once_with(
            collect_network.return_value
        )
        store_linux_network_incident.assert_called_once_with(investigation)

    @patch(
        "app.orchestration.linux_network_workflow.store_linux_network_incident"
    )
    @patch("app.orchestration.linux_network_workflow.analyze_network_evidence")
    @patch("app.orchestration.linux_network_workflow.collect_network")
    def test_no_persist_skips_memory(
        self,
        collect_network,
        analyze_network_evidence,
        store_linux_network_incident,
    ) -> None:
        collect_network.return_value = {"status": "collected"}
        investigation = Mock(status="diagnosed")
        analyze_network_evidence.return_value = investigation

        _, saved_path = run_linux_network_workflow(persist=False)

        self.assertIsNone(saved_path)
        store_linux_network_incident.assert_not_called()


if __name__ == "__main__":
    unittest.main()
