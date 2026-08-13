from __future__ import annotations

import json
import unittest

from click.testing import CliRunner

from app.cli.main import main


class KubernetesNodeLinuxCLITests(unittest.TestCase):
    def test_summary_renders_linux_host_commands(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-node",
                "--node",
                "worker-01",
                "--condition",
                "DiskPressure",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Kubernetes node Linux plan: CRITICAL", result.output)
        self.assertIn(
            "node_disk_pressure_requires_linux_storage_check",
            result.output,
        )
        self.assertIn("Linux evidence required", result.output)
        self.assertIn(
            "aop investigate linux host --path /var/lib/kubelet",
            result.output,
        )
        self.assertIn("Do not assume", result.output)

    def test_json_renders_structured_node_plan(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-node",
                "--node",
                "worker-01",
                "--condition",
                "NetworkUnavailable",
                "--format",
                "json",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["node"], "worker-01")
        self.assertEqual(
            payload["primary_diagnosis"],
            "node_network_unavailable_requires_linux_network_check",
        )
        self.assertIn(
            "aop investigate linux network --iface <node-interface>",
            payload["next_aop_commands"],
        )

    def test_list_supported_conditions(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-node",
                "--node",
                "worker-01",
                "--list-conditions",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("DiskPressure", result.output)
        self.assertIn("PIDPressure", result.output)

    def test_default_condition_is_node_not_ready(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-node",
                "--node",
                "worker-01",
                "--format",
                "json",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(
            payload["primary_diagnosis"],
            "node_not_ready_requires_linux_host_check",
        )


if __name__ == "__main__":
    unittest.main()
