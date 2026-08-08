from __future__ import annotations

from app.agents.linux.network_agent import analyze_network_evidence
from app.config.settings import settings
from app.memory.incident_history.store_linux_incident import (
    store_linux_network_incident,
)
from app.schemas.linux import LinuxNetworkInvestigation
from app.tools.linux.operations import collect_network


def run_linux_network_workflow(
    iface: str | None = None,
    persist: bool | None = None,
) -> tuple[LinuxNetworkInvestigation, str | None]:
    """
    Collect, diagnose, and optionally persist one Linux network investigation.
    """

    evidence = collect_network(iface=iface)
    investigation = analyze_network_evidence(evidence)
    should_persist = settings.PERSIST_INCIDENTS if persist is None else persist

    saved_path = None
    if should_persist and investigation.status == "diagnosed":
        saved_path = store_linux_network_incident(investigation)

    return investigation, saved_path
