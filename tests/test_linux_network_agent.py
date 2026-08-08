from __future__ import annotations

import unittest

from app.agents.linux.network_agent import analyze_network_evidence


def _result(key: str, output: str = "", status: str = "ok") -> dict:
    return {
        "key": key,
        "label": key.replace("_", " "),
        "command": key,
        "status": status,
        "output": output,
        "error": "",
        "exit_code": 0 if status == "ok" else 1,
        "requires_root": False,
    }


def _nic_result(key: str, output: str) -> dict:
    return _result(f"ens5.{key}", output)


def _evidence(
    operstate: str = "up",
    carrier: str = "1",
    speed: str = "10000",
    duplex: str = "full",
    routes: str = "default via 10.0.0.1 dev ens5\n10.0.0.0/24 dev ens5",
    resolvers: str = "nameserver 10.0.0.2",
    link_stats: str = "RX: bytes packets errors dropped\n0 0 0 0",
) -> dict:
    return {
        "domain": "network",
        "status": "collected",
        "host": "worker-01",
        "platform": "Linux",
        "message": "",
        "iface": "ens5",
        "results": [
            _result("addresses", "ens5 UP 10.0.0.10/24"),
            _result("link_stats", link_stats),
            _result("routes", routes),
            _result("neighbors", "10.0.0.1 dev ens5 lladdr aa:bb REACHABLE"),
            _result("listening", "LISTEN 0 128 0.0.0.0:80"),
            _result("connections", "ESTAB 0 0 10.0.0.10:123 10.0.0.20:443"),
            _result("resolvers", resolvers),
        ],
        "nic": {
            "domain": "nic",
            "status": "collected",
            "iface": "ens5",
            "interfaces": ["ens5"],
            "results": [
                _nic_result("operstate", operstate),
                _nic_result("carrier", carrier),
                _nic_result("speed", speed),
                _nic_result("duplex", duplex),
                _nic_result("driver_stats", "rx_errors: 0\nrx_dropped: 0"),
            ],
        },
    }


class LinuxNetworkAgentTests(unittest.TestCase):
    def test_interface_down_is_primary(self) -> None:
        investigation = analyze_network_evidence(
            _evidence(operstate="down", carrier="0")
        )

        self.assertEqual(investigation.primary_diagnosis, "interface_down")
        self.assertIn("higher layer", investigation.findings[0].next_explanation)

    def test_error_counters_detect_pressure(self) -> None:
        investigation = analyze_network_evidence(
            _evidence(
                link_stats=(
                    "RX: bytes packets errors dropped\n"
                    "0 100 3 4\n"
                )
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "interface_error_pressure",
        )
        self.assertIn("packet loss", investigation.findings[0].next_explanation)

    def test_missing_default_route_is_distinct(self) -> None:
        investigation = analyze_network_evidence(
            _evidence(routes="10.0.0.0/24 dev ens5")
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "missing_default_route",
        )

    def test_missing_dns_resolver_is_detected(self) -> None:
        investigation = analyze_network_evidence(
            _evidence(resolvers="# empty")
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "missing_dns_resolver",
        )
        self.assertIn("raw network", investigation.findings[0].next_explanation)

    def test_unsupported_platform_has_no_false_network_findings(self) -> None:
        investigation = analyze_network_evidence(
            {
                "status": "unsupported",
                "host": "laptop",
                "platform": "macOS",
                "iface": None,
                "message": "Linux diagnostics require a Linux host",
                "results": [],
            }
        )

        self.assertEqual(investigation.status, "unsupported")
        self.assertEqual(investigation.primary_diagnosis, "unsupported_platform")
        self.assertEqual(investigation.findings, [])


if __name__ == "__main__":
    unittest.main()
