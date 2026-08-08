from __future__ import annotations

import json
import unittest

from click.testing import CliRunner

from app.cli.main import main


class KubernetesLinuxCorrelationCLITests(unittest.TestCase):
    def test_summary_renders_linux_follow_up_commands(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-linux",
                "--incident",
                "OOMKilled",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Kubernetes to Linux correlation: OOMKilled", result.output)
        self.assertIn("aop investigate linux memory --pid <container-pid>", result.output)
        self.assertIn("Do not assume", result.output)
        self.assertIn("Memory note:", result.output)

    def test_json_renders_structured_plan(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-linux",
                "--incident",
                "DiskPressure",
                "--format",
                "json",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["incident"], "DiskPressure")
        self.assertIn(
            "aop investigate linux disk --path /var/lib/kubelet",
            payload["next_aop_commands"],
        )

    def test_list_supported_incidents(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-linux",
                "--list",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("CrashLoopBackOff", result.output)
        self.assertIn("NodeNotReady", result.output)

    def test_requires_incident_or_list(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-linux",
            ],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Provide --incident", result.output)


if __name__ == "__main__":
    unittest.main()
