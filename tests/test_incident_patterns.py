from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.memory.incident_patterns.patterns import (
    build_kubernetes_pattern_fingerprint,
    build_linux_pattern_fingerprint,
    find_incident_patterns,
)
from app.schemas.memory import IncidentMemory, LinuxIncidentMemory


class IncidentPatternTests(unittest.TestCase):
    def test_builds_kubernetes_pattern_fingerprint(self) -> None:
        memory = IncidentMemory.model_validate(
            {
                "incident_id": "k8s-1",
                "timestamp": "2026-08-14T00:00:00Z",
                "environment": "test",
                "fingerprint": {
                    "incident_type": "MemoryExhaustion",
                    "namespace": "payments",
                    "workload_name": "checkout-abc",
                    "failure_reason": "OOMKilled",
                },
                "severity": "critical",
                "confidence": 95,
                "pod_name": "checkout-abc",
                "namespace": "payments",
                "node": "worker-01",
                "incident_type": "MemoryExhaustion",
                "rca_summary": "Container exceeded memory limit.",
                "remediation_summary": "Review limits and heap growth.",
                "source_workflow_version": "v1",
            }
        )

        self.assertEqual(
            build_kubernetes_pattern_fingerprint(memory),
            "kubernetes:payments:checkout-abc:memoryexhaustion:oomkilled",
        )

    def test_builds_linux_pattern_fingerprint(self) -> None:
        memory = LinuxIncidentMemory.model_validate(
            {
                "incident_id": "linux-1",
                "timestamp": "2026-08-14T00:00:00Z",
                "environment": "test",
                "domain": "linux.disk",
                "hostname": "worker-01",
                "target": "/var",
                "incident_type": "filesystem_bytes_exhausted",
                "severity": "critical",
                "confidence": 90,
                "summary": "Filesystem is full.",
                "findings": [
                    {
                        "code": "filesystem_full",
                        "summary": "Use is above threshold.",
                    }
                ],
                "evidence_gaps": [],
                "source_workflow_version": "v1",
            }
        )

        self.assertEqual(
            build_linux_pattern_fingerprint(memory),
            "linux:linux.disk:worker-01:_var:filesystem_bytes_exhausted:filesystem_full",
        )

    def test_finds_recurring_kubernetes_and_linux_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Path(temp_dir)
            self._write_kubernetes_memory(storage)
            self._write_linux_memory(storage, "linux-1", "2026-08-14T00:00:00Z")
            self._write_linux_memory(storage, "linux-2", "2026-08-14T01:00:00Z")

            with patch("app.memory.incident_patterns.patterns.settings.INCIDENT_HISTORY_DIR", temp_dir):
                report = find_incident_patterns(min_count=2)

        self.assertEqual(report.total_patterns, 2)
        fingerprints = {pattern.fingerprint for pattern in report.patterns}
        self.assertIn(
            "kubernetes:payments:checkout-abc:memoryexhaustion:oomkilled",
            fingerprints,
        )
        self.assertIn(
            "linux:linux.disk:worker-01:_var:filesystem_bytes_exhausted:filesystem_full",
            fingerprints,
        )

    def test_filters_patterns_by_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Path(temp_dir)
            self._write_kubernetes_memory(storage)
            self._write_linux_memory(storage, "linux-1", "2026-08-14T00:00:00Z")
            self._write_linux_memory(storage, "linux-2", "2026-08-14T01:00:00Z")

            with patch("app.memory.incident_patterns.patterns.settings.INCIDENT_HISTORY_DIR", temp_dir):
                report = find_incident_patterns(
                    min_count=2,
                    domain="linux.disk",
                )

        self.assertEqual(report.total_patterns, 1)
        self.assertEqual(report.patterns[0].domain, "linux.disk")

    def _write_kubernetes_memory(self, storage: Path) -> None:
        payload = [
            self._kubernetes_item("k8s-1", "2026-08-14T00:00:00Z"),
            self._kubernetes_item("k8s-2", "2026-08-14T01:00:00Z"),
        ]
        (storage / "incident_memory_20260814_000000.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def _kubernetes_item(self, incident_id: str, timestamp: str) -> dict:
        return {
            "incident_id": incident_id,
            "timestamp": timestamp,
            "environment": "test",
            "fingerprint": {
                "incident_type": "MemoryExhaustion",
                "namespace": "payments",
                "workload_name": "checkout-abc",
                "failure_reason": "OOMKilled",
            },
            "severity": "critical",
            "confidence": 95,
            "pod_name": "checkout-abc",
            "namespace": "payments",
            "node": "worker-01",
            "incident_type": "MemoryExhaustion",
            "rca_summary": "Container exceeded memory limit.",
            "remediation_summary": "Review limits and heap growth.",
            "source_workflow_version": "v1",
        }

    def _write_linux_memory(
        self,
        storage: Path,
        incident_id: str,
        timestamp: str,
    ) -> None:
        payload = {
            "incident_id": incident_id,
            "timestamp": timestamp,
            "environment": "test",
            "domain": "linux.disk",
            "hostname": "worker-01",
            "target": "/var",
            "incident_type": "filesystem_bytes_exhausted",
            "severity": "critical",
            "confidence": 90,
            "summary": "Filesystem is full.",
            "findings": [
                {
                    "code": "filesystem_full",
                    "summary": "Use is above threshold.",
                }
            ],
            "evidence_gaps": [],
            "source_workflow_version": "v1",
        }
        filename = f"linux_disk_incident_{incident_id}.json"
        (storage / filename).write_text(
            json.dumps(payload),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
