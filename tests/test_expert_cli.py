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

    def test_lx_list_shows_shortcuts(self) -> None:
        result = CliRunner().invoke(main, ["lx", "list"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("boot", result.output)
        self.assertIn("grubby", result.output)
        self.assertIn("storage", result.output)

    def test_lx_boot_renders_safe_checks_and_dangerous_commands(self) -> None:
        result = CliRunner().invoke(main, ["lx", "boot"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Linux Boot", result.output)
        self.assertIn("journalctl --list-boots", result.output)
        self.assertIn("Dangerous commands to avoid", result.output)
        self.assertIn("reboot", result.output)
        self.assertIn("Do not assume", result.output)

    def test_lx_grub_mentions_grubby_and_boot_args(self) -> None:
        result = CliRunner().invoke(main, ["lx", "grub"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("grubby --default-kernel", result.output)
        self.assertIn("cat /proc/cmdline", result.output)
        self.assertIn("rollback kernel", result.output)

    def test_lx_storage_json_contains_dangerous_guardrails(self) -> None:
        result = CliRunner().invoke(
            main,
            ["lx", "explain", "storage", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["topic"], "storage")
        self.assertIn("xfs_repair <device>", payload["dangerous"])
        self.assertIn(
            "aop investigate linux disk --path /var",
            payload["aop_commands"],
        )


if __name__ == "__main__":
    unittest.main()
