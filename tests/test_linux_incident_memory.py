from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.memory.incident_history.store_linux_incident import (
    store_linux_disk_incident,
)
from app.schemas.linux import LinuxDiskInvestigation


class LinuxIncidentMemoryTests(unittest.TestCase):
    @patch(
        "app.memory.incident_history.store_linux_incident.SemanticMemoryClient",
        side_effect=RuntimeError("embedding service unavailable"),
    )
    def test_structured_memory_survives_semantic_failure(
        self,
        _semantic_client,
    ) -> None:
        investigation = LinuxDiskInvestigation(
            status="diagnosed",
            hostname="db-01",
            path="/var",
            platform="Linux",
            primary_diagnosis="filesystem_capacity_exhaustion",
            severity="critical",
            confidence=97,
            summary="Filesystem byte utilization is 96%.",
        )

        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "app.memory.incident_history.store_linux_incident."
                "settings.INCIDENT_HISTORY_DIR",
                directory,
            ):
                saved_path = store_linux_disk_incident(investigation)

            payload = json.loads(
                Path(saved_path).read_text(encoding="utf-8")
            )

        self.assertEqual(payload["domain"], "linux.disk")
        self.assertEqual(
            payload["incident_type"],
            "filesystem_capacity_exhaustion",
        )
        self.assertEqual(payload["hostname"], "db-01")


if __name__ == "__main__":
    unittest.main()
