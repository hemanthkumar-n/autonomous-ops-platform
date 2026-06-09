from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from app.cli.main import main


class KubernetesCLITests(unittest.TestCase):
    @patch(
        "app.tools.kubernetes.operations.cluster_health"
    )
    def test_health_summary(self, cluster_health) -> None:
        cluster_health.return_value = {
            "version": "v1.30.0",
            "namespace": "payments",
            "nodes": {
                "ready": 2,
                "total": 2,
                "items": [],
            },
            "pods": {
                "healthy": 4,
                "unhealthy": 1,
                "total": 5,
                "items": [
                    {
                        "namespace": "payments",
                        "pod": "checkout",
                        "ready": "0/1",
                        "status": "CrashLoopBackOff",
                        "restarts": 6,
                        "node": "worker-1",
                    }
                ],
            },
        }

        result = CliRunner().invoke(
            main,
            ["kb", "health", "-n", "payments"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("2/2 ready", result.output)
        self.assertIn("checkout", result.output)
        self.assertIn("CrashLoopBackOff", result.output)

    @patch(
        "app.tools.kubernetes.operations.list_pods"
    )
    def test_pod_alias_supports_json(self, list_pods) -> None:
        list_pods.return_value = [
            {
                "namespace": "payments",
                "pod": "checkout",
                "ready": "0/1",
                "status": "OOMKilled",
                "restarts": 3,
                "node": "worker-1",
                "age": "2m",
                "healthy": False,
            }
        ]

        result = CliRunner().invoke(
            main,
            ["kb", "po", "-n", "payments", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload[0]["status"], "OOMKilled")
        list_pods.assert_called_once_with(
            namespace="payments",
            unhealthy_only=True,
            include_system=False,
        )

    @patch(
        "app.orchestration.incident_workflow.run_incident_workflow"
    )
    def test_investigate_alias_delegates_to_workflow(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (None, None)

        result = CliRunner().invoke(
            main,
            ["kb", "inv", "-n", "payments", "--no-persist"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "No active incidents detected.",
            result.output,
        )
        run_workflow.assert_called_once_with(
            namespace="payments",
            pod_name=None,
            persist=False,
        )


if __name__ == "__main__":
    unittest.main()
