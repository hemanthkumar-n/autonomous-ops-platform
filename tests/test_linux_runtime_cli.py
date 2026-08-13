from __future__ import annotations

import json
import unittest

from click.testing import CliRunner

from app.cli.main import main


class LinuxRuntimeCLITests(unittest.TestCase):
    def test_summary_renders_runtime_training_plan(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "runtime",
                "--runtime",
                "containerd",
                "--symptom",
                "image-pull",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Linux runtime plan: WARNING", result.output)
        self.assertIn("containerd_image_pull_requires_runtime_evidence", result.output)
        self.assertIn("Evidence plan", result.output)
        self.assertIn("aop investigate linux network", result.output)
        self.assertIn("Dangerous actions to avoid first", result.output)
        self.assertIn("Do not assume", result.output)

    def test_json_renders_structured_runtime_plan(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "runtime",
                "--runtime",
                "crio",
                "--symptom",
                "disk-pressure",
                "--format",
                "json",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["runtime"], "crio")
        self.assertEqual(payload["symptom"], "disk-pressure")
        self.assertIn("/var/lib/containers", payload["storage_paths"])
        self.assertIn("dangerous_actions", payload)

    def test_list_runtimes_and_symptoms(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "runtime",
                "--list",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("containerd", result.output)
        self.assertIn("image-pull", result.output)
        self.assertIn("cgroup", result.output)


if __name__ == "__main__":
    unittest.main()
