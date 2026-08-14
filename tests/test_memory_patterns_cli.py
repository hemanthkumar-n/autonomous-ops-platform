from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from app.cli.main import main


class MemoryPatternsCLITests(unittest.TestCase):
    def test_memory_patterns_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self._write_pattern_memory(Path(temp_dir))

            with patch("app.memory.incident_patterns.patterns.settings.INCIDENT_HISTORY_DIR", temp_dir):
                result = CliRunner().invoke(
                    main,
                    ["memory", "patterns", "--min-count", "2"],
                )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("AOP incident patterns", result.output)
        self.assertIn("occurrences: 2", result.output)
        self.assertIn("MemoryExhaustion", result.output)

    def test_memory_patterns_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self._write_pattern_memory(Path(temp_dir))

            with patch("app.memory.incident_patterns.patterns.settings.INCIDENT_HISTORY_DIR", temp_dir):
                result = CliRunner().invoke(
                    main,
                    [
                        "memory",
                        "patterns",
                        "--min-count",
                        "2",
                        "--format",
                        "json",
                    ],
                )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["total_patterns"], 1)
        self.assertEqual(payload["patterns"][0]["occurrence_count"], 2)

    def _write_pattern_memory(self, storage: Path) -> None:
        payload = [
            self._item("k8s-1", "2026-08-14T00:00:00Z"),
            self._item("k8s-2", "2026-08-14T01:00:00Z"),
        ]
        (storage / "incident_memory_20260814_000000.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def _item(self, incident_id: str, timestamp: str) -> dict:
        return {
            "incident_id": incident_id,
            "timestamp": timestamp,
            "environment": "test",
            "fingerprint": {
                "incident_type": "MemoryExhaustion",
                "namespace": "payments",
                "workload_name": "checkout",
                "failure_reason": "OOMKilled",
            },
            "severity": "critical",
            "confidence": 95,
            "pod_name": "checkout",
            "namespace": "payments",
            "node": "worker-01",
            "incident_type": "MemoryExhaustion",
            "rca_summary": "Container exceeded memory limit.",
            "remediation_summary": "Review limits and heap growth.",
            "source_workflow_version": "v1",
        }


if __name__ == "__main__":
    unittest.main()
