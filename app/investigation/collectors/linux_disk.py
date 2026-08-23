from __future__ import annotations

from collections.abc import Callable

from app.investigation.evidence_planner import EvidenceRequest
from app.investigation.models import InvestigationCase
from app.orchestration.linux_disk_workflow import run_linux_disk_workflow
from app.schemas.linux import LinuxDiskInvestigation

from .linux_common import normalize_linux_investigation


DiskWorkflow = Callable[..., tuple[LinuxDiskInvestigation, str | None]]


def build_linux_disk_collector(workflow: DiskWorkflow = run_linux_disk_workflow):
    """Return a registered read-only collector backed by AOP's disk workflow."""

    def collect(request: EvidenceRequest, case: InvestigationCase):
        scan_path = request.metadata.get("path") or "/"
        investigation, _ = workflow(scan_path=scan_path, persist=False)
        return normalize_linux_investigation(
            request=request,
            case=case,
            domain="disk",
            hostname=investigation.hostname,
            primary_diagnosis=investigation.primary_diagnosis,
            confidence=investigation.confidence,
            summary=investigation.summary,
            findings=investigation.findings,
            evidence_gaps=investigation.evidence_gaps,
            structured={
                "path": investigation.path,
                "filesystem_use_percent": investigation.filesystem_use_percent,
                "inode_use_percent": investigation.inode_use_percent,
                "mount_source": investigation.mount_source,
                "filesystem_type": investigation.filesystem_type,
                "mount_point": investigation.mount_point,
                "io_sample": investigation.io_sample,
            },
        )

    return collect
