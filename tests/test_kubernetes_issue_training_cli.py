from __future__ import annotations

import json
import unittest

from click.testing import CliRunner

from app.cli.main import main


class KubernetesIssueTrainingCLITests(unittest.TestCase):
    def test_summary_renders_causes_evidence_and_sources(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-knowledge",
                "--symptom",
                "OOMKilled",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Kubernetes issue knowledge: OOMKilled", result.output)
        self.assertIn("Common causes", result.output)
        self.assertIn("Linux evidence", result.output)
        self.assertIn("Node-pressure Eviction", result.output)

    def test_json_renders_structured_knowledge(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-knowledge",
                "--symptom",
                "DiskPressure",
                "--format",
                "json",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["symptom"], "DiskPressure")
        self.assertIn("inode exhaustion", payload["common_causes"])

    def test_list_supported_symptoms(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-knowledge",
                "--list",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("CrashLoopBackOff", result.output)
        self.assertIn("NetworkUnavailable", result.output)

    def test_requires_symptom_or_list(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "k8s-knowledge",
            ],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Provide --symptom", result.output)


if __name__ == "__main__":
    unittest.main()
