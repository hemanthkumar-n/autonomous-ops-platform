from __future__ import annotations

import argparse

from app.investigation.autonomous_loop import AutonomousInvestigationLoop
from app.investigation.collectors.linux_cpu import build_linux_cpu_collector
from app.investigation.collectors.linux_disk import build_linux_disk_collector
from app.investigation.collectors.linux_network import build_linux_network_collector
from app.investigation.models import AffectedResource, EvidenceGap, Hypothesis, InvestigationCase
from app.schemas.linux import (
    LinuxCpuFinding,
    LinuxCpuInvestigation,
    LinuxDiskFinding,
    LinuxDiskInvestigation,
    LinuxNetworkFinding,
    LinuxNetworkInvestigation,
)


def _case() -> InvestigationCase:
    return InvestigationCase(
        id="AOP-DEMO-MULTI-1",
        title="Node degradation with CPU, disk, and network symptoms",
        source="fixture",
        environment="demo",
        severity="critical",
        symptoms=["high latency", "node pressure", "packet loss"],
        affected_resources=[
            AffectedResource(domain="linux", kind="host", name="worker-07"),
        ],
        evidence_gaps=[
            EvidenceGap(id="gap-cpu", description="CPU evidence missing", priority="critical", recommended_checks=["aop investigate linux cpu"], blocks_rca=True),
            EvidenceGap(id="gap-disk", description="Disk evidence missing", priority="high", recommended_checks=["aop investigate linux disk"], blocks_rca=True),
            EvidenceGap(id="gap-network", description="Network evidence missing", priority="high", recommended_checks=["aop investigate linux network"], blocks_rca=True),
        ],
        hypotheses=[
            Hypothesis(
                id="multi-domain-host-pressure",
                statement="Combined host resource pressure is degrading the workload.",
                missing_evidence_ids=["gap-cpu", "gap-disk", "gap-network"],
            )
        ],
    )


def _cpu_workflow(**kwargs):
    del kwargs
    return LinuxCpuInvestigation(
        status="diagnosed", hostname="worker-07", platform="linux",
        primary_diagnosis="cpu_saturation", severity="critical", confidence=91,
        summary="CPU saturation confirmed.", load_average=[12.0, 10.0, 8.0], cpu_count=4,
        findings=[LinuxCpuFinding(code="cpu_saturation", severity="critical", confidence=91,
            summary="Runnable demand exceeds available CPU capacity.", evidence=["load=12 cpu=4"],
            next="Inspect top CPU consumers.")],
    ), None


def _disk_workflow(**kwargs):
    del kwargs
    return LinuxDiskInvestigation(
        status="diagnosed", hostname="worker-07", path="/", platform="linux",
        primary_diagnosis="storage_latency", severity="warning", confidence=86,
        summary="Storage latency pressure confirmed.", filesystem_use_percent=74.0,
        io_sample={"util_percent": 94.0, "await_ms": 42.0},
        findings=[LinuxDiskFinding(code="storage_latency", severity="warning", confidence=86,
            summary="Block-device latency and utilization are elevated.", evidence=["util=94%", "await=42ms"],
            next="Inspect device queue and backing storage.")],
    ), None


def _network_workflow(**kwargs):
    del kwargs
    return LinuxNetworkInvestigation(
        status="diagnosed", hostname="worker-07", platform="linux", iface="eth0",
        primary_diagnosis="interface_errors", severity="warning", confidence=84,
        summary="Network interface errors confirmed.", interfaces=["eth0 UP"],
        nic_signals={"rx_errors": "31", "tx_errors": "7"},
        findings=[LinuxNetworkFinding(code="interface_errors", severity="warning", confidence=84,
            summary="NIC error counters show packet-path degradation.", evidence=["rx_errors=31", "tx_errors=7"],
            next="Inspect NIC and upstream network path.")],
    ), None


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run AOP v0.43 multi-collector autonomy.")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    args = parser.parse_args()

    result = AutonomousInvestigationLoop(
        collectors={
            "linux_cpu": build_linux_cpu_collector(_cpu_workflow),
            "linux_disk": build_linux_disk_collector(_disk_workflow),
            "linux_network": build_linux_network_collector(_network_workflow),
        }
    ).run(_case())

    if args.format == "json":
        print(result.model_dump_json(indent=2))
        return

    print("AOP autonomous investigation v0.43 - multi collector")
    print(f"case: {result.case.id}")
    print(f"stop_reason: {result.stop_reason}")
    print(f"requests_executed: {result.total_requests_executed}")
    print(f"evidence_added: {result.total_evidence_added}")
    print(f"remaining_gaps: {len(result.case.evidence_gaps)}")
    for step in result.steps:
        print(f"step {step.number}: {', '.join(step.executed_request_ids)} -> {step.decision_state} ({step.confidence:.0%})")
    if result.case.rca_candidate:
        print(f"rca_candidate: {result.case.rca_candidate.statement}")
        print(f"confidence: {result.case.rca_candidate.confidence:.0%}")
        for reason in result.case.rca_candidate.why:
            print(f"  + {reason}")
    print(f"confirmed_root_cause: {result.case.root_cause or 'none'}")
    print("safety: existing read-only Linux workflows only; persistence disabled; no remediation")


if __name__ == "__main__":
    main()
