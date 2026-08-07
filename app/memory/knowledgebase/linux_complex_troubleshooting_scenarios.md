# Linux Complex Troubleshooting Scenarios

Updated: 2026-08-08

This file is AOP memory for complex Linux troubleshooting. It captures the
operator reasoning that should eventually power `aop linux plan <domain>` and
future deterministic Linux investigations.

This is not a command dump. Each scenario should preserve:

```text
symptom
  -> likely causes
  -> first safe checks
  -> interpretation
  -> common traps
  -> Kubernetes/AWS correlation when relevant
```

## Scenario: High Load, Low CPU

Symptoms:

- load average is high
- CPU idle may still be available
- application latency or shell response is slow

Likely causes:

- blocked I/O
- many tasks in `D` state
- NFS or storage latency
- memory reclaim pressure
- cgroup throttling or pressure

First safe checks:

```bash
uptime
vmstat 1 5
ps -eo state,pid,ppid,comm,wchan:32,args | awk '$1 ~ /D|R/'
iostat -xz 1 5
cat /proc/pressure/io
journalctl -k -p warning --no-pager
```

Interpretation:

- Load average is not CPU percentage.
- `D` state tasks contribute to load because they are stuck in kernel wait.
- Correlate run queue, blocked tasks, I/O wait, PSI, and kernel storage logs.

Common trap:

- Do not call this a CPU issue only because load is high.

## Scenario: Memory Pressure and OOM

Symptoms:

- application killed or restarted
- pod shows `OOMKilled`
- host has low available memory
- swap activity is high

Likely causes:

- process memory growth
- cgroup memory limit
- kernel OOM killer
- swap storm
- unreclaimable slab growth
- tmpfs usage

First safe checks:

```bash
free -h
vmstat 1 5
cat /proc/meminfo
ps aux --sort=-%mem | head
journalctl -k -g 'Out of memory|Killed process|oom' --no-pager
cat /proc/pressure/memory
```

Interpretation:

- Low `free` memory alone is not proof of memory pressure.
- `available`, swap-in/swap-out, PSI, OOM logs, and cgroup limits must be
  correlated.
- In Kubernetes, distinguish host memory pressure from pod cgroup OOM.

Common trap:

- Do not restart the biggest process before preserving OOM evidence and
  checking whether it was killed by the kernel or application logic.

## Scenario: Disk `df` and `du` Mismatch

Symptoms:

- `df` shows high usage
- `du` cannot find matching visible files
- deleting files does not release space

Likely causes:

- deleted files still open by running processes
- files hidden under a mounted filesystem
- snapshots
- reserved blocks
- sparse files
- mount namespace differences

First safe checks:

```bash
df -hT
du -x -h --max-depth=1 /var | sort -h
lsof +L1 /var
findmnt -r
```

Interpretation:

- `df` reports filesystem allocation.
- `du` reports visible directory tree usage.
- Deleted-open files release space only when the owning process closes the
  file.

Common trap:

- Do not keep deleting files when `lsof +L1` shows a process still holds the
  deleted file open.

## Scenario: Inode Exhaustion

Symptoms:

- file creation fails
- application logs show `No space left on device`
- `df -h` may show free bytes

Likely causes:

- too many small files
- runaway cache
- session/temp directories
- mail queues
- container runtime artifacts

First safe checks:

```bash
df -i
find /var -xdev -type f | wc -l
find /var -xdev -type d -printf '%p\n' | head
du -x -h --max-depth=1 /var | sort -h
```

Interpretation:

- Inodes are file metadata slots. A filesystem can have free bytes but no
  remaining inodes.

Common trap:

- Searching only for large files will not explain inode exhaustion.

## Scenario: Read-Only Filesystem Remount

Symptoms:

- writes fail
- mount options show `ro`
- services cannot write logs or state

Likely causes:

- filesystem errors
- storage I/O errors
- SAN/NAS/cloud-volume issue
- kernel protected the filesystem after corruption risk

First safe checks:

```bash
findmnt -no SOURCE,FSTYPE,OPTIONS,TARGET /var
journalctl -k -g 'read-only|I/O error|EXT4-fs|XFS|BTRFS|nvme|scsi' --no-pager
lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL
```

Interpretation:

- Treat read-only remount as a storage/filesystem health incident first, not a
  cleanup task.

Common trap:

- Do not remount read-write before understanding why the kernel changed the
  state.

## Scenario: File Descriptor Exhaustion

Symptoms:

- application cannot open files or sockets
- logs show `too many open files`
- new connections fail

Likely causes:

- process file descriptor leak
- low systemd or shell limits
- high socket churn
- missing connection pooling

First safe checks:

```bash
cat /proc/sys/fs/file-nr
cat /proc/<pid>/limits
ls -l /proc/<pid>/fd | wc -l
lsof -p <pid>
systemctl show <service> -p LimitNOFILE
```

Interpretation:

- Separate system-wide file table pressure from per-process limits.

Common trap:

- Raising limits without finding the leak may only delay the next incident.

## Scenario: Port Conflict or Missing Listener

Symptoms:

- service is running but clients cannot connect
- expected port is not listening
- bind error appears in logs

Likely causes:

- another process owns the port
- service bound to localhost instead of all interfaces
- IPv4/IPv6 binding mismatch
- firewall or route issue
- application failed after startup

First safe checks:

```bash
ss -plnt
ss -tanp | grep <port>
lsof -i -P | grep <port>
systemctl status <service>
journalctl -u <service> -n 100 --no-pager
```

Interpretation:

- Listener presence, bind address, owning PID, and service logs must be
  correlated before blaming the network.

Common trap:

- Do not assume a firewall issue before confirming the process is listening on
  the expected address and port.

## Scenario: systemd Restart Loop

Symptoms:

- service repeatedly restarts
- unit shows failed or activating state
- logs repeat the same startup error

Likely causes:

- missing environment file
- permissions issue
- dependency unavailable
- port conflict
- filesystem or disk issue
- memory or cgroup limit
- bad deployment/config

First safe checks:

```bash
systemctl status <service>
systemctl show <service> -p NRestarts -p Restart -p RestartUSec
journalctl -u <service> -n 200 --no-pager
systemctl cat <service>
systemctl list-dependencies <service>
```

Interpretation:

- The service failure may be a symptom of disk, memory, DNS, dependency, or
  permission failure.

Common trap:

- Restarting a restart loop usually repeats the failure and can destroy
  useful timing evidence.

## Scenario: Kernel Panic or Previous Boot Crash

Symptoms:

- host rebooted unexpectedly
- uptime is shorter than expected
- application recovered but cause unknown

Likely causes:

- kernel panic
- hardware or storage fault
- OOM/reboot policy
- watchdog reset
- hypervisor or cloud host event

First safe checks:

```bash
uptime
last -x | head
journalctl --list-boots
journalctl -k -b -1 -p warning --no-pager
coredumpctl list
```

Interpretation:

- Previous-boot evidence is critical because current boot logs may look clean.

Common trap:

- Do not investigate only the current boot after an unexpected restart.

## Scenario: LVM, Partition, and Filesystem Expansion Mismatch

Symptoms:

- storage was expanded but filesystem still shows old size
- application still reports low disk
- cloud or SAN volume size changed

Likely causes:

- block device expanded but partition not resized
- physical volume not resized
- logical volume not extended
- filesystem not grown
- wrong mount or wrong device

First safe checks:

```bash
lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS
df -hT
pvs
vgs
lvs -a -o +devices
findmnt -r
```

Interpretation:

- Expansion has layers: volume, partition, PV, VG, LV, filesystem, mount.
  Confirm which layer did not change.

Common trap:

- Do not assume cloud/SAN expansion automatically changed the filesystem.

## Scenario: Container Runtime Disk Pressure

Symptoms:

- Kubernetes node reports `DiskPressure`
- image pulls fail
- pods are evicted
- `/var` or runtime directory grows quickly

Likely causes:

- container image layers
- container logs
- orphaned pod data
- failed garbage collection
- runtime snapshots
- ephemeral storage limits missing

First safe checks:

```bash
df -hT /var/lib/kubelet /var/lib/containerd
df -i /var/lib/kubelet /var/lib/containerd
du -x -h --max-depth=1 /var/lib/containerd | sort -h
du -x -h --max-depth=1 /var/lib/kubelet | sort -h
journalctl -u kubelet -n 200 --no-pager
```

Interpretation:

- Kubernetes reports the orchestration symptom. Linux filesystem and runtime
  evidence explain the node-level cause.

Common trap:

- Do not delete container runtime directories manually without understanding
  kubelet/runtime ownership and recovery impact.
