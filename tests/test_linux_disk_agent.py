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
    block_devices: str = "",
    lvm_vgs: str = "",
    lvm_lvs: str = "",
    multipath: str = "",
    nfs: str = "",
    iostat: str = "",
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
            _result("block_devices", "NAME KNAME TYPE SIZE FSTYPE MOUNTPOINTS PKNAME MODEL SERIAL ROTA RO STATE\n" + block_devices),
            _result("lvm_pvs", ""),
            _result("lvm_vgs", lvm_vgs),
            _result("lvm_lvs", lvm_lvs),
            _result("multipath", multipath),
            _result("nfs_mountstats", nfs),
            _result("io_stats", iostat),
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
        self.assertIn(
            "No space left on device",
            investigation.findings[0].next_explanation,
        )

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
        deleted_open = next(
            item
            for item in investigation.findings
            if item.code == "deleted_open_files"
        )
        self.assertIn("process still has them open", deleted_open.next_explanation)

    def test_nfs_risk_is_distinct_from_local_disk_capacity(self) -> None:
        investigation = analyze_disk_evidence(
            _evidence(
                filesystem="nfs01:/export nfs4 100G 40G 60G 40% /mnt/share",
                inodes="nfs01:/export 100000 40000 60000 40% /mnt/share",
                mount="nfs01:/export nfs4 rw,soft,timeo=600 /mnt/share",
                kernel="kernel: nfs: server nfs01 not responding, still trying",
            )
        )

        self.assertEqual(investigation.primary_diagnosis, "nfs_mount_risk")
        self.assertIn("NFS", investigation.findings[0].summary)
        self.assertIn("server health", investigation.findings[0].next)

    def test_multipath_path_loss_outranks_capacity(self) -> None:
        investigation = analyze_disk_evidence(
            _evidence(
                filesystem="/dev/mapper/mpatha ext4 100G 88G 12G 88% /data",
                mount="/dev/mapper/mpatha ext4 rw,relatime /data",
                multipath=(
                    "mpatha dm-2 NETAPP,LUN\n"
                    "`- 3:0:0:1 sdb 8:16 failed faulty running"
                ),
            )
        )

        self.assertEqual(investigation.primary_diagnosis, "multipath_path_loss")
        self.assertIn("SAN", investigation.findings[0].next_explanation)

    def test_lvm_thin_pool_pressure_is_reported(self) -> None:
        investigation = analyze_disk_evidence(
            _evidence(
                filesystem="/dev/mapper/vg0-app ext4 100G 50G 50G 50% /app",
                mount="/dev/mapper/vg0-app ext4 rw,relatime /app",
                lvm_lvs=" thinpool vg0 500.00g  95.50  91.00 twi-aotz--",
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "lvm_thin_pool_pressure",
        )
        self.assertIn("Thin-pool", investigation.findings[0].next_explanation)

    def test_storage_latency_pressure_uses_iostat_sample(self) -> None:
        investigation = analyze_disk_evidence(
            _evidence(
                filesystem="/dev/sda1 ext4 100G 50G 50G 50% /var",
                iostat=(
                    "Device r/s w/s rkB/s wkB/s rrqm/s wrqm/s %rrqm %wrqm "
                    "r_await w_await aqu-sz rareq-sz wareq-sz svctm %util\n"
                    "sda 1 20 4 800 0 0 0 0 4.00 180.00 5.0 4 40 0 98.00"
                ),
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "storage_latency_pressure",
        )
        self.assertEqual(investigation.io_sample["device"], "sda")

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
