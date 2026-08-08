# Linux Investigation Ladder

This page is the v0.19 human map for Linux troubleshooting inside AOP.

The goal is not to collect every command on the first screen. The goal is to
follow the same order an experienced Linux administrator uses under pressure:
confirm the symptom, collect bounded evidence, avoid destructive shortcuts,
then decide the next safest check.

## Why This Exists

AOP treats Linux as a first-class SRE domain, not as a helper script behind
Kubernetes. Kubernetes, containers, AWS, and application failures often surface
as Linux symptoms first:

- high load without high CPU
- cgroup memory pressure while host memory looks fine
- inode exhaustion while byte capacity looks available
- NIC carrier, driver, or duplex problems behind application timeout symptoms
- systemd restart loops hidden behind simple service-unavailable alerts
- deleted-open files causing `df` and `du` mismatch

The ladder keeps the troubleshooting path visible for future teammates and AI
handoffs.

## The Ladder

```text
1. Confirm the host is safe to inspect
   -> aop linux health

2. Explain unfamiliar or high-impact commands before running them
   -> aop linux explain "df -hT"
   -> aop linux explain "netstat -plane | grep :3045"
   -> aop linux explain "lsof -p 4242"

3. Plan the investigation when the path is not obvious
   -> aop linux plan disk --path /var
   -> aop linux plan scenario high-load
   -> aop linux plan scenario oom

4. Collect raw evidence from the likely domain
   -> aop linux disk --path /var
   -> aop linux memory
   -> aop linux cpu
   -> aop linux nic --iface ens5
   -> aop linux network
   -> aop linux services
   -> aop linux internals --interval 5
   -> aop linux cgroups --pid 4242 --interval 5

5. Run deterministic investigation where AOP has a domain investigator
   -> aop investigate linux disk --path /var
   -> aop investigate linux memory --pid 4242
   -> aop investigate linux cpu
   -> aop investigate linux network --iface ens5
   -> aop investigate linux service --service nginx

6. Preserve the incident memory
   -> structured JSON memory under data/incidents/
   -> semantic memory when vector indexing is available
   -> exact-memory fallback when semantic memory is unavailable

7. Correlate outward only after Linux evidence is clear
   -> Kubernetes node and pod symptoms
   -> Prometheus metrics
   -> future AWS CloudWatch and CloudTrail evidence
   -> future Slack or Teams approval workflow
```

## Domain Order

### Disk And Filesystems

Start with the filesystem that backs the path:

```bash
aop linux plan disk --path /var
aop linux disk --path /var
aop investigate linux disk --path /var
```

The useful order is:

```text
df bytes
  -> df inodes
  -> filesystem type and mount options
  -> bounded du on the same filesystem
  -> recent large files
  -> deleted-open files
  -> kernel filesystem and storage errors
```

This prevents a common mistake: assuming byte usage is the only disk problem.
Inodes, read-only remounts, deleted-open files, and storage I/O errors can all
look like "disk full" from the application side.

### Memory And OOM

Use memory investigation when the symptom is OOMKilled, host memory pressure,
swap activity, allocation failure, or container restart with memory clues:

```bash
aop linux memory
aop investigate linux memory
aop investigate linux memory --pid 4242
```

The PID-scoped path matters for Kubernetes and containers because a cgroup can
hit its own memory limit while the host still has available memory.

### CPU, Load, And D-State

Use CPU investigation when the symptom is slow host, high load, run queue
growth, blocked tasks, I/O wait, or steal time:

```bash
aop linux cpu
aop linux internals --interval 5
aop investigate linux cpu
```

AOP preserves the Linux truth that load average is not CPU percentage. Load
can rise because tasks are runnable, blocked in `D` state, stalled on I/O, or
waiting on virtualized CPU.

### NIC And Network

Split physical/interface evidence from higher-level network symptoms:

```bash
aop linux nic --iface ens5
aop linux network
aop investigate linux network --iface ens5
```

NIC evidence answers link, carrier, error/drop, speed, duplex, driver, and
firmware questions. Network evidence answers route, resolver, neighbor, and
socket questions. Keeping them separate makes the diagnosis cleaner.

### systemd Services

Use service investigation when an application is down, flapping, or repeatedly
restarting:

```bash
aop linux services
aop investigate linux service --service nginx
```

AOP checks service state, start-limit-hit, exit status, restart policy, unit
definition, and recent warning/error journal evidence. It does not restart or
reset the service.

### Internals And Cgroups

Use internals and cgroups when surface metrics are not enough:

```bash
aop linux internals --interval 5
aop linux cgroups --pid 4242 --interval 5
```

Internals show scheduler, process-state, PSI, and VM-counter behavior.
Cgroups show whether a process is constrained by CPU, memory, I/O, or PID
limits. This is the bridge between classic Linux administration and modern
Kubernetes/container troubleshooting.

## Safety Rules

- AOP Linux commands are read-only.
- AOP does not invoke `sudo`.
- AOP does not restart, kill, delete, unmount, clear logs, or modify firewall
  state.
- Missing commands and permission limits are reported as evidence gaps.
- AI reasoning must be grounded in collected evidence, not invented facts.

## Future Expansion

After v0.19, the next Linux growth should focus on correlation:

- connect Kubernetes pod/node symptoms to Linux host evidence
- normalize AWS CloudWatch and CloudTrail evidence into the same contracts
- prepare dashboard panels from evidence, findings, and timelines
- add AI RCA only after deterministic evidence is collected
