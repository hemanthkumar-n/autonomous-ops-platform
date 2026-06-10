from __future__ import annotations

import unittest

from app.agents.linux.disk_agent import analyze_disk_evidence


def _result(
    key: str,
    output: str = "",
    status: str = "ok",
) -> dict:
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


def _evidence(
    filesystem: str = "/dev/sda1 ext4 100G 96G 4G 96% /var",
    inodes: str = "/dev/sda1 100000 40000 60000 40% /var",
    mount: str = "/dev/sda1 ext4 rw,relatime /var",
    recent: str = "",
    deleted: str = "",
    kernel: str = "-- No entries --",
) -> dict:
    return {
        "domain": "disk",
        "status": "collected",
        "host": "db-01",
        "platform": "Linux",
        "message": "",
        "path": "/var",
        "results": [
            _result(
                "filesystem",
                "Filesystem Type Size Used Avail Use% Mounted on\n"
                + filesystem,
            ),
            _result(
                "inodes",
                "Filesystem Inodes IUsed IFree IUse% Mounted on\n"
                + inodes,
            ),
            _result(
                "mount",
                "SOURCE FSTYPE OPTIONS TARGET\n" + mount,
            ),
            _result("directory_usage", "9000\t/var/log"),
            _result("large_recent_files", recent),
            _result("deleted_open_files", deleted),
            _result("kernel_storage_errors", kernel),
        ],
    }


class LinuxDiskAgentTests(unittest.TestCase):
    def test_classifies_byte_capacity_exhaustion(self) -> None:
        investigation = analyze_disk_evidence(_evidence())

        self.assertEqual(
            investigation.primary_diagnosis,
            "filesystem_capacity_exhaustion",
        )
        self.assertEqual(investigation.severity, "critical")
        self.assertEqual(investigation.filesystem_use_percent, 96)
        self.assertEqual(investigation.inode_use_percent, 40)

    def test_inode_exhaustion_is_distinct_from_large_files(self) -> None:
        investigation = analyze_disk_evidence(
            _evidence(
                filesystem="/dev/sda1 ext4 100G 50G 50G 50% /var",
                inodes="/dev/sda1 100000 97000 3000 97% /var",
                recent="5000000000\t2026-06-10T10:00:00\t/var/big.log",
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "inode_exhaustion",
        )
        self.assertIn("small files", investigation.findings[0].next)

    def test_read_only_mount_outranks_capacity(self) -> None:
        investigation = analyze_disk_evidence(
            _evidence(
                mount="/dev/sda1 ext4 ro,relatime /var",
                kernel=(
                    "kernel: EXT4-fs error: remounting filesystem read-only"
                ),
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "read_only_filesystem",
        )
        self.assertEqual(investigation.confidence, 98)

    def test_deleted_files_and_growth_are_causal_findings(self) -> None:
        investigation = analyze_disk_evidence(
            _evidence(
                filesystem="/dev/sda1 ext4 100G 88G 12G 88% /var",
                recent=(
                    "5000000000\t2026-06-10T10:00:00\t/var/log/app.log"
                ),
                deleted=(
                    "COMMAND PID USER FD TYPE DEVICE SIZE/OFF NLINK NAME\n"
                    "java 42 app 4w REG 8,1 4G 0 /var/log/app.log"
                ),
            )
        )

        codes = [item.code for item in investigation.findings]
        self.assertIn("deleted_open_files", codes)
        self.assertIn("rapid_file_growth", codes)

    def test_missing_df_becomes_insufficient_evidence(self) -> None:
        evidence = _evidence()
        evidence["results"][0] = _result(
            "filesystem",
            status="unavailable",
        )

        investigation = analyze_disk_evidence(evidence)

        self.assertEqual(
            investigation.primary_diagnosis,
            "insufficient_evidence",
        )
        self.assertTrue(investigation.evidence_gaps)

    def test_unsupported_platform_has_no_false_disk_findings(self) -> None:
        investigation = analyze_disk_evidence(
            {
                "status": "unsupported",
                "host": "laptop",
                "platform": "macOS",
                "path": "/",
                "message": "Linux diagnostics require a Linux host",
                "results": [],
            }
        )

        self.assertEqual(investigation.status, "unsupported")
        self.assertEqual(
            investigation.primary_diagnosis,
            "unsupported_platform",
        )
        self.assertEqual(investigation.findings, [])


if __name__ == "__main__":
    unittest.main()
