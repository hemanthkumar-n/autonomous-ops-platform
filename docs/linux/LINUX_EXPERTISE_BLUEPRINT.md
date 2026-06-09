# AOP Linux Operational Expertise Blueprint

## Purpose

Linux support in AOP will encode experienced system-administration reasoning,
not merely execute a collection of familiar commands.

The founding source is Hemanth Kumar's `tshelper` work and the operational
experience behind its command selection. The original artifacts are preserved
under [`tshelper-original/`](tshelper-original/).

The founder's authored Linux and Kubernetes correlation criterion is preserved
in
[`../../app/memory/knowledgebase/linkedin_kubernetes_linux_criteria.md`](../../app/memory/knowledgebase/linkedin_kubernetes_linux_criteria.md).

This document is the editable design space. The archived source files remain
unchanged.

## Product Goal

Provide one source of truth for Linux troubleshooting that helps both
experienced SREs and engineers who do not yet know where to begin.

AOP should answer four questions:

1. What evidence should be collected first?
2. What is abnormal?
3. How do the signals correlate?
4. What should the operator inspect next without destroying evidence?

## Core Workflow

```text
Symptom
  -> preserve evidence
  -> identify scope and recent change
  -> collect host facts
  -> evaluate resource pressure
  -> correlate kernel, service, process, network, and storage signals
  -> classify deterministic findings
  -> recommend the next lowest-risk diagnostic step
  -> produce a portable report
  -> store reusable operational memory
```

AI analysis should enhance this workflow only after deterministic evidence and
rules have established the facts.

## Implemented CLI Foundation

```text
aop linux health
aop linux cpu
aop linux memory
aop linux disk
aop linux network
aop linux processes
aop linux services
aop linux logs
aop linux kernel
aop linux boot
aop linux security
aop linux all
```

These commands provide read-only, bounded evidence collection with
human-readable and JSON output. `aop linux investigate`, cross-domain
correlation, incident memory, and AI-assisted RCA remain future work.

## Baseline Evidence

Every Linux investigation should begin with enough context to prevent false
conclusions:

- hostname, operating system, distribution, kernel, architecture, and uptime
- physical host, virtual machine, container, or cloud instance context
- time synchronization and timezone
- current user and privilege level
- load average and runnable or blocked task state
- memory, swap, filesystem, inode, and mount state
- failed services and recent boot or kernel errors
- active interfaces, addresses, routes, DNS configuration, and listening ports
- recent package, configuration, deployment, or reboot changes when available

## Expert Diagnostic Domains

### CPU and Load

AOP must distinguish:

- CPU saturation from high load caused by blocked I/O
- user, system, steal, idle, and I/O-wait time
- sustained pressure from a short-lived spike
- one hot process from per-core imbalance
- process demand from virtualization steal time
- high context switching, interrupts, and run-queue contention
- uninterruptible `D` state processes from ordinary CPU consumers
- throttling, thermal limitations, and cgroup CPU limits

High load alone must never be reported as proof of high CPU utilization.

### Memory and OOM

AOP must distinguish:

- low `free` memory from genuinely low `available` memory
- page cache use from unreclaimable pressure
- swap allocation from active swap-in and swap-out pressure
- host memory exhaustion from cgroup or container limits
- application growth from kernel slab growth
- an OOM kill from an application crash
- memory pressure from huge pages, shared memory, or overcommit behavior

Evidence should correlate `free`, `vmstat`, process RSS, `/proc/meminfo`,
pressure stall information, cgroup limits, and kernel OOM records.

### Disk, Filesystem, and Storage

AOP must inspect:

- capacity and inode exhaustion
- mount availability, options, and read-only transitions
- filesystem errors and kernel storage messages
- deleted files that remain open
- directory growth and large-file ownership
- device latency, utilization, queue depth, and I/O wait
- LVM, device mapper, multipath, RAID, and cloud-volume context
- stale NFS mounts and blocked filesystem operations
- reserved blocks and differences between apparent and allocated size

`df` and `du` disagreement should trigger investigation, not confusion.

### Processes

AOP must inspect:

- process state, parent-child relationships, age, and command line
- CPU, RSS, virtual memory, threads, file descriptors, and open files
- zombie and orphan processes
- uninterruptible tasks
- repeated respawn loops
- process limits and exhaustion
- namespace and cgroup placement
- deleted executables or libraries still in use

The platform should make targeted inspection possible without dumping every
process by default.

### Services and systemd

AOP must inspect:

- unit state, result, exit code, and restart count
- dependencies and ordering
- recent service logs
- effective unit configuration and drop-ins
- failed conditions, missing environment files, permissions, and limits
- socket activation and timer relationships
- restart loops and rate limiting
- whether the service failure is a symptom of disk, memory, DNS, network, or
  dependency failure

Restarting a failed service should not be the first troubleshooting action.

### Network and DNS

Troubleshooting order should be explicit:

```text
link
  -> interface state and errors
  -> address
  -> local route
  -> default gateway
  -> raw IP reachability
  -> DNS configuration and resolution
  -> remote port reachability
  -> TLS or protocol behavior
  -> application listener and firewall
```

AOP must account for:

- packet errors, drops, MTU, duplex, speed, bonding, VLANs, and bridges
- policy routing and multiple routing tables
- ARP or neighbor failures
- local and upstream firewall behavior
- listening sockets versus service readiness
- connection states, backlog, ephemeral ports, and conntrack exhaustion
- DNS search domains, resolver order, caching, split DNS, and reverse lookup
- IPv4 and IPv6 differences

Successful ping must not be treated as proof that an application is healthy.

### Logs, Kernel, and Boot

AOP must correlate:

- current boot and previous boot journals
- kernel errors, OOM activity, hung tasks, storage resets, and link changes
- service-specific logs and rate-limited messages
- authentication and privilege events
- boot duration and failed boot units
- log rotation, disk pressure, and missing logs
- system time changes that can distort incident timelines

Raw log volume should be bounded and filtered around the incident window.

### Security and Access

Read-only diagnostics should cover:

- authentication failures and account lockouts
- sudo and privilege failures
- file ownership, mode, ACL, and extended attributes
- SELinux or AppArmor denials
- firewall state
- expiring certificates
- user, group, and SSH configuration context

Sensitive values, secrets, private keys, tokens, and unrestricted environment
variables must be redacted from reports.

## Operational Safety

- Default to read-only collection.
- Do not restart, kill, delete, unmount, modify firewall rules, or clear logs.
- Label commands that require elevated privileges.
- Bound expensive scans by path, depth, count, duration, and filesystem type.
- Avoid crossing pseudo-filesystems or remote mounts unintentionally.
- Record command availability and permission failures as evidence.
- Preserve raw evidence separately from interpretations.
- Support human-readable and JSON output.

## Implementation Phases

### Phase 1: Preserve and Model

- [x] preserve all `tshelper` source material
- [x] establish command execution safety and timeout contracts
- [x] add normalized Linux command-result records
- [ ] define comprehensive typed Linux host and diagnostic evidence
- document distribution and utility compatibility

### Phase 2: Linux Health

- [x] implement `aop linux health`
- [x] collect baseline host, load, memory, filesystem, and service indicators
- [x] return deterministic status and prioritized findings
- [x] add offline mocked tests
- [ ] add Linux fixture coverage for inode, kernel, network, and service states

### Phase 3: Focused Diagnostics

- [x] implement CPU, memory, disk, network, process, service, and log commands
- [x] add bounded human-readable and JSON reports
- [x] add kernel, boot, and security evidence commands
- [ ] encode advanced expert correlation and next-step rules

### Phase 4: Deep Linux Intelligence

- add kernel, boot, security, storage-stack, namespace, and cgroup diagnostics
- support incident time windows and recent-change correlation
- add redaction and portable support bundles

### Phase 5: Memory and AI

- store normalized Linux incidents
- retrieve exact and semantically similar cases
- generate evidence-grounded RCA and remediation guidance
- retain deterministic findings when semantic memory or AI is unavailable

## Knowledge Capture

New Linux knowledge from the author should be recorded as one of:

- a deterministic diagnostic rule
- a collector requirement
- a command safety constraint
- a symptom-to-next-step decision
- a historical incident example
- a runbook
- a test fixture

This converts individual experience into durable, testable operational
intelligence.

## Kubernetes Correlation Rule

Linux evidence should not be collected as an isolated parallel report. When a
Kubernetes incident can originate from the node, AOP should correlate the pod,
workload, event, metric, kernel, cgroup, filesystem, process, service, runtime,
and network evidence inside one investigation.

Until remote node collection exists, AI must name the missing Linux evidence
and recommend the appropriate `aop linux` command rather than asserting a
host-level cause.
