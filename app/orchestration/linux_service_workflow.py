from __future__ import annotations

from app.agents.linux.service_agent import analyze_service_evidence
from app.config.settings import settings
from app.memory.incident_history.store_linux_incident import (
    store_linux_service_incident,
)
from app.schemas.linux import LinuxServiceInvestigation
from app.tools.linux.operations import collect_service


def run_linux_service_workflow(
    service: str,
    persist: bool | None = None,
) -> tuple[LinuxServiceInvestigation, str | None]:
    """
    Collect, diagnose, and optionally persist one Linux service investigation.
    """

    evidence = collect_service(service=service)
    investigation = analyze_service_evidence(evidence)
    should_persist = settings.PERSIST_INCIDENTS if persist is None else persist

    saved_path = None
    if should_persist and investigation.status == "diagnosed":
        saved_path = store_linux_service_incident(investigation)

    return investigation, saved_path
