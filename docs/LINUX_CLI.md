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
| `aop linux network` | Interfaces, errors, routes, neighbors, sockets, and resolvers |
| `aop linux processes` | Process state, age, hierarchy, and resource usage |
| `aop linux services` | Failed and running systemd services |
| `aop linux logs` | Bounded warning, kernel, and authentication journals |
| `aop linux kernel` | Kernel identity, warnings, and errors |
| `aop linux boot` | Current boot state, performance, and previous-boot warnings |
| `aop linux security` | Identity, failed logins, SELinux, and AppArmor state |
| `aop linux all` | Baseline health followed by the primary diagnostic domains |

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

Directory scans remain on the selected filesystem through `du -x`.

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
