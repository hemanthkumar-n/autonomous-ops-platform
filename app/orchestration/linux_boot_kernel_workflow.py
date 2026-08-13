from __future__ import annotations

from app.agents.linux.boot_kernel_agent import analyze_boot_kernel_evidence
from app.config.settings import settings
from app.memory.incident_history.store_linux_incident import (
    store_linux_boot_kernel_incident,
)
from app.schemas.linux import LinuxBootKernelInvestigation
from app.tools.linux.operations import collect_boot_kernel


def run_linux_boot_kernel_workflow(
    recent_minutes: int = 240,
    persist: bool | None = None,
) -> tuple[LinuxBootKernelInvestigation, str | None]:
    """
    Collect, diagnose, and optionally persist Linux boot/kernel evidence.
    """

    evidence = collect_boot_kernel(recent_minutes=recent_minutes)
    investigation = analyze_boot_kernel_evidence(evidence)
    should_persist = settings.PERSIST_INCIDENTS if persist is None else persist

    saved_path = None
    if should_persist and investigation.status == "diagnosed":
        saved_path = store_linux_boot_kernel_incident(investigation)

    return investigation, saved_path
