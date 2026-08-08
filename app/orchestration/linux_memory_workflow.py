from __future__ import annotations

from app.agents.linux.memory_agent import analyze_memory_evidence
from app.config.settings import settings
from app.memory.incident_history.store_linux_incident import (
    store_linux_memory_incident,
)
from app.schemas.linux import LinuxMemoryInvestigation
from app.tools.linux.operations import collect_memory


def run_linux_memory_workflow(
    pid: int | None = None,
    top: int = 10,
    recent_minutes: int = 60,
    persist: bool | None = None,
) -> tuple[LinuxMemoryInvestigation, str | None]:
    """
    Collect, diagnose, and optionally persist one Linux memory investigation.
    """

    evidence = collect_memory(
        pid=pid,
        top=top,
        recent_minutes=recent_minutes,
    )
    investigation = analyze_memory_evidence(evidence)
    should_persist = settings.PERSIST_INCIDENTS if persist is None else persist

    saved_path = None
    if should_persist and investigation.status == "diagnosed":
        saved_path = store_linux_memory_incident(investigation)

    return investigation, saved_path
