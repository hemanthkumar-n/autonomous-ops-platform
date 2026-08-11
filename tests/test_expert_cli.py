from __future__ import annotations

import json
import unittest

from click.testing import CliRunner

from app.cli.main import main


class ExpertCLITests(unittest.TestCase):
    def test_kx_list_shows_shortcuts(self) -> None:
        result = CliRunner().invoke(main, ["kx", "list"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("oom", result.output)
        self.assertIn("OOMKilled", result.output)
        self.assertIn("crash", result.output)
        self.assertIn("CrashLoopBackOff", result.output)

    def test_kx_oom_renders_knowledge_and_linux_commands(self) -> None:
        result = CliRunner().invoke(main, ["kx", "oom"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("aop kx oom -> OOMKilled", result.output)
        self.assertIn("Top causes", result.output)
        self.assertIn("Kubernetes checks", result.output)
        self.assertIn("Next AOP commands", result.output)
        self.assertIn(
            "aop investigate linux memory --pid <container-pid>",
            result.output,
        )
        self.assertIn("Do not assume", result.output)

    def test_kx_image_alias_uses_image_pull_backoff(self) -> None:
        result = CliRunner().invoke(main, ["kx", "image"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("ImagePullBackOff", result.output)
        self.assertIn("aop investigate linux network", result.output)

    def test_kx_explain_accepts_full_symptom_json(self) -> None:
        result = CliRunner().invoke(
            main,
            ["kx", "explain", "DiskPressure", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["symptom"], "DiskPressure")
        self.assertIn(
            "aop investigate linux disk --path /var/lib/kubelet",
            payload["linux_correlation"]["next_aop_commands"],
        )


if __name__ == "__main__":
    unittest.main()
