from __future__ import annotations

from app.agents.linux.disk_agent import analyze_disk_evidence
from app.config.settings import settings
from app.memory.incident_history.store_linux_incident import (
    store_linux_disk_incident,
)
from app.schemas.linux import LinuxDiskInvestigation
from app.tools.linux.operations import collect_disk


def run_linux_disk_workflow(
    scan_path: str = "/",
    top: int = 10,
    recent_minutes: int = 60,
    large_size_mb: int = 1024,
    persist: bool | None = None,
) -> tuple[LinuxDiskInvestigation, str | None]:
    """
    Collect, diagnose, and optionally persist one Linux disk investigation.
    """

    evidence = collect_disk(
        scan_path=scan_path,
        top=top,
        recent_minutes=recent_minutes,
        large_size_mb=large_size_mb,
    )
    investigation = analyze_disk_evidence(evidence)
    should_persist = settings.PERSIST_INCIDENTS if persist is None else persist

    saved_path = None
    if should_persist and investigation.status == "diagnosed":
        saved_path = store_linux_disk_incident(investigation)

    return investigation, saved_path
