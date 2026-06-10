# AOP Linux CLI

The `aop linux` command group provides read-only Linux troubleshooting based
on the preserved `tshelper` workflow and experienced Linux administration
practices.

## Quick Start

```bash
aop linux health
aop linux cpu
aop linux memory
aop linux disk --path /var
aop linux space --path /var
aop linux fs --path /var
aop linux network
aop linux services
aop linux logs
```

## Commands

| Command | Purpose |
|---|---|
| `aop linux health` | Prioritized host, load, memory, filesystem, and service health |
| `aop linux cpu` | CPU topology, load, run queue, and top consumers |
| `aop linux memory` | Available memory, swap activity, kernel counters, and consumers |
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
