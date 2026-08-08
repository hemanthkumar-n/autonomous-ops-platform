from __future__ import annotations

import re

from app.schemas.linux import (
    LinuxNetworkFinding,
    LinuxNetworkInvestigation,
)


_DROP_ERROR_PATTERN = re.compile(r"\b(errors|dropped|overruns|carrier)\b", re.I)


def _result_map(results: list[dict]) -> dict[str, dict]:
    return {item["key"]: item for item in results}


def _data_lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.strip()]


def _nic_signal(nic_results: dict[str, dict], key_suffix: str) -> str | None:
    for key, result in nic_results.items():
        if key.endswith(key_suffix) and result.get("status") == "ok":
            return result.get("output", "").strip()
    return None


def _has_counter_pressure(output: str) -> bool:
    lines = output.splitlines()
    for index, line in enumerate(lines):
        if not _DROP_ERROR_PATTERN.search(line):
            continue
        if any(token.isdigit() and int(token) > 0 for token in line.split()):
            return True
        if index + 1 < len(lines):
            next_values = [
                int(token)
                for token in lines[index + 1].split()
                if token.isdigit()
            ]
            if len(next_values) >= 4 and any(value > 0 for value in next_values[2:]):
                return True
    return False


def _finding(
    code: str,
    severity: str,
    confidence: int,
    summary: str,
    evidence: list[str],
    next_step: str,
) -> LinuxNetworkFinding:
    return LinuxNetworkFinding(
        code=code,
        severity=severity,
        confidence=confidence,
        summary=summary,
        evidence=evidence,
        next=next_step,
        next_explanation=_next_explanation(code),
    )


def _next_explanation(code: str) -> str:
    explanations = {
        "interface_down": (
            "An interface that is down or unknown breaks every higher layer "
            "above it. Fixing DNS, routes, Kubernetes, or the application "
            "will not help until link state is understood."
        ),
        "no_carrier": (
            "No carrier means the NIC does not see a physical or virtual link. "
            "Check cable, switch port, hypervisor attachment, cloud ENI, or "
            "bond/team member state before chasing application symptoms."
        ),
        "interface_error_pressure": (
            "RX/TX errors, drops, overruns, or carrier changes indicate packet "
            "loss or driver/link pressure below TCP and the application."
        ),
        "speed_or_duplex_unknown": (
            "Missing or unknown speed/duplex evidence can hide negotiation "
            "problems. Confirm ethtool and sysfs before concluding the link is "
            "healthy."
        ),
        "missing_default_route": (
            "Without a default route, off-subnet traffic cannot leave the "
            "host even if the interface and local network are healthy."
        ),
        "missing_dns_resolver": (
            "Without a usable resolver, IP connectivity can work while DNS "
            "name lookups fail. Separate DNS from raw network reachability."
        ),
        "insufficient_evidence": (
            "AOP needs interface, route, resolver, and NIC evidence before "
            "making a reliable network diagnosis."
        ),
    }
    return explanations.get(code, "")


def analyze_network_evidence(evidence: dict) -> LinuxNetworkInvestigation:
    """
    Convert network and NIC evidence into deterministic diagnosis.
    """

    if evidence.get("status") != "collected":
        return LinuxNetworkInvestigation(
            status="unsupported",
            hostname=evidence.get("host", "unknown"),
            platform=evidence.get("platform", "unknown"),
            iface=evidence.get("iface"),
            primary_diagnosis="unsupported_platform",
            severity="info",
            confidence=100,
            summary=evidence.get(
                "message",
                "Linux network evidence is unavailable.",
            ),
            raw_evidence=evidence,
        )

    results = _result_map(evidence.get("results", []))
    nic = evidence.get("nic") or {}
    nic_results = _result_map(nic.get("results", [])) if nic else {}
    gaps = [
        f"{item['label']}: {item['status']}"
        for item in evidence.get("results", [])
        if item.get("status") != "ok"
    ]
    gaps.extend(
        f"{item['label']}: {item['status']}"
        for item in nic.get("results", [])
        if item.get("status") != "ok"
    )

    addresses = _data_lines(results.get("addresses", {}).get("output", ""))
    routes = _data_lines(results.get("routes", {}).get("output", ""))
    resolvers = [
        line
        for line in _data_lines(results.get("resolvers", {}).get("output", ""))
        if line.startswith("nameserver")
    ]
    interfaces = nic.get("interfaces", []) or []
    iface = evidence.get("iface")
    nic_signals = {
        "operstate": _nic_signal(nic_results, ".operstate") or "",
        "carrier": _nic_signal(nic_results, ".carrier") or "",
        "speed": _nic_signal(nic_results, ".speed") or "",
        "duplex": _nic_signal(nic_results, ".duplex") or "",
    }

    findings: list[LinuxNetworkFinding] = []

    if nic_signals["operstate"] in {"down", "unknown", "notpresent"}:
        findings.append(
            _finding(
                "interface_down",
                "critical",
                96,
                f"Interface operational state is {nic_signals['operstate']}.",
                [f"operstate={nic_signals['operstate']}"],
                "Inspect link state, driver, hypervisor/cloud attachment, and switch side.",
            )
        )

    if nic_signals["carrier"] == "0":
        findings.append(
            _finding(
                "no_carrier",
                "critical",
                95,
                "Interface carrier is absent.",
                ["carrier=0"],
                "Check physical link, switch port, bond member, virtual NIC, or cloud ENI attachment.",
            )
        )

    link_stats = results.get("link_stats", {})
    driver_stats = [
        item.get("output", "")
        for key, item in nic_results.items()
        if key.endswith(".driver_stats") and item.get("status") == "ok"
    ]
    if (
        link_stats.get("status") == "ok"
        and _has_counter_pressure(link_stats.get("output", ""))
    ) or any(_has_counter_pressure(output) for output in driver_stats):
        findings.append(
            _finding(
                "interface_error_pressure",
                "warning",
                88,
                "Interface counters show errors, drops, overruns, or carrier pressure.",
                [link_stats.get("output", "")[:500], *driver_stats[:1]],
                "Correlate NIC counters with switch, driver, cable, MTU, queue, or cloud network metrics.",
            )
        )

    if nic_signals["speed"] in {"", "-1", "unknown"} or nic_signals["duplex"] in {
        "",
        "unknown",
    }:
        findings.append(
            _finding(
                "speed_or_duplex_unknown",
                "info",
                70,
                "Speed or duplex evidence is missing or unknown.",
                [
                    f"speed={nic_signals['speed'] or 'missing'}",
                    f"duplex={nic_signals['duplex'] or 'missing'}",
                ],
                "Confirm ethtool/sysfs visibility and validate negotiated link settings.",
            )
        )

    if routes and not any(line.startswith("default ") for line in routes):
        findings.append(
            _finding(
                "missing_default_route",
                "warning",
                85,
                "No default route was found in routing evidence.",
                routes[:5],
                "Check routing table, policy routes, DHCP/cloud-init, and network manager state.",
            )
        )

    if not resolvers:
        findings.append(
            _finding(
                "missing_dns_resolver",
                "warning",
                80,
                "No nameserver entries were found in resolver configuration.",
                _data_lines(results.get("resolvers", {}).get("output", ""))[:5],
                "Check /etc/resolv.conf, systemd-resolved, DHCP, split DNS, or cluster DNS config.",
            )
        )

    if not addresses or not routes:
        findings.append(
            _finding(
                "insufficient_evidence",
                "warning",
                100,
                "Address or route evidence is missing.",
                gaps or ["address or route output missing"],
                "Restore access to ip address and route evidence, then repeat the investigation.",
            )
        )

    priority = {
        "interface_down": 0,
        "no_carrier": 1,
        "interface_error_pressure": 2,
        "missing_default_route": 3,
        "missing_dns_resolver": 4,
        "speed_or_duplex_unknown": 5,
        "insufficient_evidence": 6,
    }
    findings.sort(key=lambda item: priority[item.code])

    if findings:
        primary = findings[0]
        diagnosis = primary.code
        severity = primary.severity
        confidence = primary.confidence
        summary = primary.summary
    else:
        diagnosis = "no_immediate_network_pressure"
        severity = "info"
        confidence = max(60, 95 - (len(gaps) * 8))
        summary = (
            "No immediate link, carrier, error/drop, route, or resolver "
            "problem was identified."
        )

    if gaps and diagnosis != "insufficient_evidence":
        confidence = max(50, confidence - min(20, len(gaps) * 4))

    return LinuxNetworkInvestigation(
        status="diagnosed",
        hostname=evidence.get("host", "unknown"),
        platform=evidence.get("platform", "unknown"),
        iface=iface,
        primary_diagnosis=diagnosis,
        severity=severity,
        confidence=confidence,
        summary=summary,
        interfaces=interfaces,
        routes=routes,
        resolvers=resolvers,
        nic_signals=nic_signals,
        findings=findings,
        evidence_gaps=gaps,
        raw_evidence=evidence,
    )
