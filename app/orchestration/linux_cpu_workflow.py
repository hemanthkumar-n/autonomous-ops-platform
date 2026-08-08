from __future__ import annotations

from app.agents.linux.cpu_agent import analyze_cpu_evidence
from app.config.settings import settings
from app.memory.incident_history.store_linux_incident import (
    store_linux_cpu_incident,
)
from app.schemas.linux import LinuxCpuInvestigation
from app.tools.linux.operations import collect_cpu


def run_linux_cpu_workflow(
    top: int = 10,
    persist: bool | None = None,
) -> tuple[LinuxCpuInvestigation, str | None]:
    """
    Collect, diagnose, and optionally persist one Linux CPU investigation.
    """

    evidence = collect_cpu(top=top)
    investigation = analyze_cpu_evidence(evidence)
    should_persist = settings.PERSIST_INCIDENTS if persist is None else persist

    saved_path = None
    if should_persist and investigation.status == "diagnosed":
        saved_path = store_linux_cpu_incident(investigation)

    return investigation, saved_path
