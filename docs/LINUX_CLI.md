# AOP Linux CLI

The `aop linux` command group provides read-only Linux troubleshooting based
on the preserved `tshelper` workflow and experienced Linux administration
practices.

For the current end-to-end troubleshooting order, read
[`linux/LINUX_INVESTIGATION_LADDER.md`](linux/LINUX_INVESTIGATION_LADDER.md).

Use `aop lx` when you need short Linux expert shortcuts:

```bash
aop lx list
aop lx boot
aop lx kernel
aop lx grub
aop lx storage
aop lx lvm
aop lx dns
aop lx nfs
aop lx limits
aop lx selinux
aop lx runtime
aop lx explain storage --json
```

## Quick Start

```bash
aop linux health
aop linux explain "df -hT"
aop linux explain "netstat -plane | grep :3045"
aop linux plan disk --path /var
aop linux plan scenario --list
aop linux plan scenario high-load
aop linux cpu
aop investigate linux cpu
aop investigate linux boot
aop linux memory
aop investigate linux memory
aop investigate linux memory --pid 4242
aop linux nic
aop linux nic --iface ens5
aop investigate linux network --iface ens5
aop linux disk --path /var
aop linux space --path /var
aop linux fs --path /var
aop linux network
aop linux services
aop investigate linux service --service nginx
aop linux logs
```

## Commands

| Command | Purpose |
|---|---|
| `aop linux health` | Prioritized host, load, memory, filesystem, and service health |
| `aop linux explain` | Explain a Linux troubleshooting command and its arguments |
| `aop linux plan` | Build a read-only troubleshooting plan before collecting evidence |
| `aop linux cpu` | CPU topology, load, run queue, and top consumers |
| `aop linux memory` | Available memory, swap activity, kernel counters, and consumers |
| `aop linux nic` | NIC/interface link state, counters, driver, firmware, speed, and duplex |
| `aop linux disk` | Capacity, inodes, mounts, directory usage, and deleted-open files |
| `aop linux space` | Shortcut for `aop linux disk` |
| `aop linux fs` | Shortcut for `aop linux disk` |
| `aop linux network` | Interfaces, errors, routes, neighbors, sockets, and resolvers |
| `aop linux processes` | Process state, age, hierarchy, and resource usage |
| `aop linux services` | Failed and running systemd services |
| `aop linux logs` | Bounded warning, kernel, and authentication journals |
| `aop linux kernel` | Kernel identity, warnings, and errors |
| `aop linux boot` | Current boot state, performance, and previous-boot warnings |
| `aop linux security` | Identity, failed logins, SELinux, and AppArmor state |
| `aop linux internals` | Scheduler load, process states, PSI, and VM counters |
| `aop linux cgroups` | PID membership, cgroup version, limits, events, and pressure |
| `aop linux all` | Baseline health followed by the primary diagnostic domains |

## Explain Commands

```bash
aop linux explain "df -hT"
aop linux explain "ps aux"
aop linux explain "lsof -p 4242"
aop linux explain "netstat -plane | grep :3045"
aop linux explain "strace -tt -T -f -y -yy -s 1024 -p 4242"
aop linux explain "tcpdump host 10.0.0.10"
aop linux explain "df -hT" --json
```

`aop linux explain` uses AOP's Linux argument reasoning catalog. It explains:

- command purpose
- argument meaning
- troubleshooting value
- risk level
- whether elevated read access may be required
- incident types where the command is useful
- related next commands
- AOP guidance for safe use

The command is not executed. It is a teaching and planning interface for the
operator and for future specialist agents.

Example interpretation:

```text
df -hT
  -h -> human-readable units
  -T -> filesystem type
  useful for DiskFull, KubernetesDiskPressure, and FilesystemCapacity
```

## Plan Commands

```bash
aop linux plan disk --path /var
aop linux plan disk --path /var --json
aop linux plan disk --path /company/app/logs
aop linux plan scenario --list
aop linux plan scenario high-load
aop linux plan scenario oom --json
```

`aop linux plan disk` prints the ordered disk troubleshooting path before any
collector runs. It explains:

- filesystem byte and type confirmation
- inode exhaustion checks
- mount identity and read-only state
- bounded directory growth investigation
- recent large-file discovery
- deleted-open file checks
- kernel filesystem and storage-error review
- I/O latency separation
- Kubernetes node correlation
- AWS/EBS correlation

The plan command does not require the path to exist on the local machine. This
allows an SRE to prepare an investigation for a remote host, a Kubernetes node,
or a company-specific application path before logging into the target system.

`aop linux plan scenario` exposes senior Linux scenario plans from AOP's
complex troubleshooting catalog. It does not execute the listed checks. It
prints symptoms, likely causes, first safe checks, interpretation, common
traps, and Kubernetes/AWS/cgroup correlation where relevant.

Current scenario keys:

- `high-load`
- `memory-pressure`
- `df-du-mismatch`
- `inode-exhaustion`
- `read-only-filesystem`
- `file-descriptor-exhaustion`
- `port-conflict`
- `systemd-restart-loop`
- `kernel-panic`
- `lvm-expansion-mismatch`
- `container-runtime-disk-pressure`

Useful aliases are accepted for common operator language, for example:

```bash
aop linux plan scenario oom
aop linux plan scenario fdisk
aop linux plan scenario diskpressure
```

## Linux Internals

```bash
aop linux internals
aop linux internals --json
aop linux internals --interval 5
aop linux internals --interval 5 --json
```

This command reads:

- `/proc/loadavg`
- `/proc/uptime`
- `/proc/<PID>/stat` for process-state counts
- `/proc/pressure/cpu`
- `/proc/pressure/memory`
- `/proc/pressure/io`
- selected `/proc/vmstat` counters

Important interpretation:

- Load includes runnable and uninterruptible tasks; it is not CPU percentage.
- `D` state usually means a task is blocked inside the kernel.
- PSI measures time lost to resource contention.
- VM counters are cumulative and need timed samples for rates.

Timed mode takes two snapshots and reports:

- counter delta and per-second rate
- measured CPU, memory, and I/O stall percentages
- OOM kills that occurred during the interval
- active swap and direct-reclaim activity

The interval is bounded between 0.1 and 60 seconds.

## Cgroups

```bash
aop linux cgroups --pid 1
aop linux cgroups --pid 4242 --json
aop linux cgroups --pid 4242 --interval 5
```

A process is used as the starting point because resource controls apply to its
cgroup membership. On cgroup v2, AOP reads:

- `cpu.max`, `cpu.weight`, and `cpu.stat`
- `memory.current`, `memory.high`, `memory.max`, swap, and events
- `io.max`, `io.weight`, and `io.stat`
- `pids.current`, `pids.max`, and events
- CPU, memory, and I/O pressure

Cgroup v1 and hybrid systems are detected without applying incorrect v2
interpretation. Full controller-specific v1 normalization remains future work.

Timed cgroup v2 mode reports:

- CPU usage and throttling deltas
- memory-high and OOM event deltas
- PID-limit event deltas
- measured per-cgroup PSI stall percentages
- before/after `memory.current`

If the process exits or moves to another cgroup between snapshots, AOP refuses
to compare the counters and asks the operator to repeat the sample.

## Automation

Every command supports JSON output:

```bash
aop linux health --json
aop linux network --json
aop linux all --json > linux-report.json
```

Use strict health checks in scripts:

```bash
aop linux health --strict
```

The command exits non-zero when deterministic warning or critical findings
exist.

## Disk Incident Investigation

Raw evidence collection and incident diagnosis are separate commands:

```bash
aop linux disk --path /var
aop investigate linux disk --path /var
```

`aop linux disk` shows the ordered command evidence. The investigation command
parses that evidence and classifies:

- filesystem byte exhaustion
- inode exhaustion
- deleted-open files
- rapid large-file growth
- read-only filesystem state
- read-only block-device state
- LVM low-free-space and thin-pool pressure
- multipath path loss
- NFS mount risk and server-not-responding evidence
- block-device I/O latency or utilization pressure
- kernel filesystem or storage I/O errors
- insufficient evidence

Examples:

```bash
aop investigate linux disk --path /var
aop investigate linux disk \
  --path /var/log \
  --top 20 \
  --recent-minutes 30 \
  --large-size-mb 500
aop investigate linux disk --path /var --format json
aop investigate linux disk --path /var --no-persist
```

The result includes a primary diagnosis, severity, confidence, supporting
evidence, alternative findings, recommended next checks, why those checks
matter, and evidence gaps.

The v0.26 storage depth intentionally keeps one command:

```bash
aop investigate linux disk --path /data
```

Behind that command AOP now collects safe read-only evidence from `df`,
`findmnt`, `lsblk`, LVM inventory, multipath state, `/proc/self/mountstats`,
`iostat`, `du`, `find`, `lsof`, and kernel storage logs. This is the old Linux
admin reality: a write failure might be capacity, inodes, deleted files,
read-only remount, SAN path loss, thin-pool exhaustion, NFS trouble, or storage
latency.

The investigation does not run `fsck`, `mkfs`, `mount`, `umount`, `lvextend`,
`lvremove`, `multipathd`, cleanup commands, or any destructive storage action.

## Memory And OOM Investigation

Raw memory collection and incident diagnosis are separate commands:

```bash
aop linux memory
aop investigate linux memory
aop investigate linux memory --pid 4242
aop investigate linux memory --pid 4242 --format json
```

`aop linux memory` shows raw memory evidence. The investigation command parses
that evidence and classifies:

- recent kernel OOM kills
- cgroup memory OOM events for the selected PID
- active swap pressure from `vmstat`
- low `MemAvailable`
- cgroup `memory.high` pressure
- insufficient evidence

When `--pid` is provided, AOP includes cgroup memory evidence for that process.
This is important for Kubernetes and containerized workloads because a process
can hit a cgroup memory limit while the host still has available memory.

The memory investigation remains read-only. It does not kill processes, clear
cache, restart services, change cgroup limits, tune sysctl values, or modify
swap.

By default it persists a Linux-native JSON memory record and attempts semantic
indexing. Structured memory remains available if embeddings or the vector
store are unavailable.

Example finding explanation:

```text
Finding: kernel_oom_kill
Next: Identify the victim process, owning service or pod, allocation context, and whether the OOM was host-wide or cgroup-limited.
Why: Kernel OOM evidence proves a process or cgroup could not satisfy memory allocation.
```

This workflow is deterministic. It does not call an LLM and does not kill,
restart, clear cache, change limits, tune sysctl values, or modify swap.

## Boot, Kernel, And grubby Investigation

```bash
aop investigate linux boot
aop investigate linux boot --recent-minutes 30
aop investigate linux boot --format json
```

This command classifies:

- previous boot panic/oops evidence
- current kernel panic/oops evidence
- kernel OOM near boot/reboot context
- hung task or blocked kernel waits
- kernel storage/filesystem errors
- unavailable kdump crash capture
- running/default kernel mismatch
- risky boot arguments such as cgroup or crashkernel controls
- insufficient evidence

It collects `uname`, `/proc/cmdline`, boot history, previous boot journal,
current kernel journal, kdump status, and read-only `grubby` information. It
does not change default kernel, boot arguments, GRUB config, or reboot state.

## CPU, Load, And D-State Investigation

Raw CPU collection and incident diagnosis are separate commands:

```bash
aop linux cpu
aop linux internals
aop investigate linux cpu
aop investigate linux cpu --top 20
aop investigate linux cpu --format json
```

`aop investigate linux cpu` classifies:

- uninterruptible `D` state blocked tasks
- I/O pressure behind high load
- CPU saturation
- steal-time pressure
- high load with low CPU
- insufficient evidence

This command preserves the Linux distinction between load average and CPU
percentage. High load is not automatically CPU saturation.

The CPU investigation remains read-only. It does not kill or renice processes,
restart services, change cgroup limits, tune kernel parameters, or resize
cloud capacity.

## NIC And Interface Cards

```bash
aop linux nic
aop linux nic --iface eth0
aop linux nic --iface ens5 --json
```

NIC evidence is separate from higher-level network troubleshooting because
link and driver problems can make DNS, Kubernetes, application, and load
balancer symptoms look misleading.

`aop linux nic` collects:

- interface inventory from `ip -br link`
- addresses from `ip -br address`
- packet counters from `ip -s link`
- per-interface operational state
- carrier state
- speed
- duplex
- `ethtool <IFACE>` link settings
- `ethtool -i <IFACE>` driver and firmware
- `ethtool -S <IFACE>` driver counters

This command is read-only. It does not change routes, bring interfaces up or
down, modify MTU, reset drivers, change offload settings, capture packets, or
alter firewall state.

## Network And NIC Investigation

Raw network collection and incident diagnosis are separate commands:

```bash
aop linux network
aop linux nic --iface ens5
aop investigate linux network
aop investigate linux network --iface ens5
aop investigate linux network --iface ens5 --format json
```

`aop investigate linux network` classifies:

- interface down
- no carrier
- interface errors, drops, overruns, or carrier pressure
- missing or unknown speed/duplex evidence
- missing default route
- missing DNS resolver
- insufficient evidence

This command is read-only. It does not change routes, bring interfaces up or
down, modify MTU, reset drivers, change DNS, capture packets, or alter
firewall state.

## systemd Service Investigation

Raw service collection and incident diagnosis are separate commands:

```bash
aop linux services
aop investigate linux service --service nginx
aop investigate linux service --service nginx.service --format json
```

`aop investigate linux service` classifies:

- start-limit-hit
- failed unit state
- non-zero exit status
- restart policy loop
- recent warning/error journal evidence
- insufficient evidence

This command is read-only. It does not restart, reload, enable, disable,
reset-failed, mask, unmask, edit, or kill service processes.

## Bounded Collection

Limit process records:

```bash
aop linux cpu --top 20
aop linux memory --top 20
aop linux processes --top 20
```

Choose the disk scan root:

```bash
aop linux disk --path /var
aop linux disk --path /opt
```

### Disk Space Investigation

```bash
aop linux disk --path /var
aop linux space --path /var
aop linux fs --path /var
```

The command follows this order:

```text
filesystem bytes and type
  -> inode usage
  -> source, filesystem, mount options, and mount point
  -> largest immediate directories
  -> recently changed large files
  -> deleted files still held open
  -> recent kernel filesystem and storage errors
```

Tune the bounded searches:

```bash
aop linux disk \
  --path /var/log \
  --top 20 \
  --recent-minutes 30 \
  --large-size-mb 500
```

Options:

- `--path`: select the path and its backing filesystem.
- `--top`: limit sorted directory and recent-file records.
- `--recent-minutes`: set the recent-change and kernel-log window.
- `--large-size-mb`: set the recent-file size threshold.
- `--json`: emit structured output.

Directory and file searches remain on the selected filesystem through `du -x`
and `find -xdev`.

Interpretation:

```text
df bytes full       -> follow directory and large-file evidence
df inodes full      -> investigate excessive small-file creation
df larger than du   -> inspect deleted-open files, snapshots, or hidden data
read-only/I/O error -> investigate filesystem or storage health
```

`lsof +L1` and some process details may require elevated read access. AOP
reports permission limits but does not invoke `sudo`.

## Safety

- commands use explicit argument lists without shell evaluation
- each command has a timeout and output limit
- missing utilities are recorded as unavailable evidence
- permission failures are reported rather than hidden
- expensive disk scans are bounded by timeout, output, path, and filesystem
- no restart, kill, delete, unmount, firewall mutation, or log clearing occurs

Some evidence, including deleted-open files and failed login history, may
require elevated read access. AOP labels those checks but does not invoke
`sudo`.

## Platform Support

The command group is intended for Linux hosts. Running `aop linux health` on
another operating system returns `unsupported` rather than reporting a false
healthy result.

## Design Sources

- [`linux/LINUX_EXPERTISE_BLUEPRINT.md`](linux/LINUX_EXPERTISE_BLUEPRINT.md)
- [`linux/tshelper-original/`](linux/tshelper-original/)
