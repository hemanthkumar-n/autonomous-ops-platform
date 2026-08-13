from __future__ import annotations

import unittest
from unittest.mock import patch

from app.orchestration.linux_boot_kernel_workflow import (
    run_linux_boot_kernel_workflow,
)
from app.schemas.linux import LinuxBootKernelInvestigation


class LinuxBootKernelWorkflowTests(unittest.TestCase):
    @patch(
        "app.orchestration.linux_boot_kernel_workflow.store_linux_boot_kernel_incident"
    )
    @patch(
        "app.orchestration.linux_boot_kernel_workflow.analyze_boot_kernel_evidence"
    )
    @patch(
        "app.orchestration.linux_boot_kernel_workflow.collect_boot_kernel"
    )
    def test_collects_analyzes_and_persists(
        self,
        collect_boot_kernel,
        analyze_boot_kernel_evidence,
        store_linux_boot_kernel_incident,
    ) -> None:
        collect_boot_kernel.return_value = {"status": "collected"}
        investigation = LinuxBootKernelInvestigation(
            status="diagnosed",
            hostname="worker-1",
            platform="Linux",
            primary_diagnosis="previous_boot_panic",
            severity="critical",
            confidence=96,
            summary="Previous boot contains kernel panic/oops evidence.",
        )
        analyze_boot_kernel_evidence.return_value = investigation
        store_linux_boot_kernel_incident.return_value = "memory.json"

        result, saved_path = run_linux_boot_kernel_workflow(
            recent_minutes=60,
            persist=True,
        )

        self.assertEqual(result.primary_diagnosis, "previous_boot_panic")
        self.assertEqual(saved_path, "memory.json")
        collect_boot_kernel.assert_called_once_with(recent_minutes=60)
        store_linux_boot_kernel_incident.assert_called_once_with(investigation)

    @patch(
        "app.orchestration.linux_boot_kernel_workflow.store_linux_boot_kernel_incident"
    )
    @patch(
        "app.orchestration.linux_boot_kernel_workflow.analyze_boot_kernel_evidence"
    )
    @patch(
        "app.orchestration.linux_boot_kernel_workflow.collect_boot_kernel"
    )
    def test_no_persist_skips_memory(
        self,
        collect_boot_kernel,
        analyze_boot_kernel_evidence,
        store_linux_boot_kernel_incident,
    ) -> None:
        collect_boot_kernel.return_value = {"status": "collected"}
        analyze_boot_kernel_evidence.return_value = LinuxBootKernelInvestigation(
            status="diagnosed",
            hostname="worker-1",
            platform="Linux",
            primary_diagnosis="no_immediate_boot_kernel_failure",
            severity="info",
            confidence=90,
            summary="No immediate issue.",
        )

        _, saved_path = run_linux_boot_kernel_workflow(persist=False)

        self.assertIsNone(saved_path)
        store_linux_boot_kernel_incident.assert_not_called()


if __name__ == "__main__":
    unittest.main()
