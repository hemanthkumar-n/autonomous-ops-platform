# Linux Troubleshooting Command Catalog

## Purpose

This is AOP's canonical command-level Linux troubleshooting memory.

It preserves experienced operational practice: begin with scope and evidence,
move from broad host health toward the affected subsystem, correlate signals,
and avoid destroying evidence through premature restarts or changes.

The catalog is intentionally read-only. Commands that modify services,
processes, filesystems, firewall rules, kernel settings, packages, users, or
logs are excluded from the default workflow.

## How to Use This Catalog

For each incident:

1. Record the symptom, start time, affected host, service, and recent changes.
2. Capture baseline host and time context.
3. Check CPU/load, memory, disk/inodes/I/O, services, kernel, and network.
4. Follow the evidence into a focused domain.
5. Preserve raw output before remediation.
6. Distinguish facts, interpretations, and missing evidence.

Placeholder values:

```text
<PID>         process ID
<UNIT>        systemd unit such as nginx.service
<IFACE>       interface such as eth0 or ens5
<HOST>        hostname or IP address
<PORT>        TCP or UDP port
<PATH>        filesystem path
<DEVICE>      block device such as sda or nvme0n1
<MOUNT>       mount point
<USER>        Linux user
<SINCE>       journal start time, for example "2026-06-10 10:00:00"
```

## 1. First Five Minutes

### Identity, OS, kernel, and uptime

```bash
hostnamectl
uname -a
cat /etc/os-release
uptime
who -b
date --iso-8601=seconds
timedatectl
```

Important arguments:

- `uname -a`: kernel release, architecture, and build.
- `who -b`: last system boot.
- `date --iso-8601=seconds`: timestamp evidence in an unambiguous format.
- `timedatectl`: timezone and synchronization state.

Why it matters:

- A wrong clock corrupts incident timelines, certificates, authentication, and
  distributed-system behavior.
- Kernel and distribution versions determine available commands, cgroup mode,
  known defects, and service layout.

### Current users and activity

```bash
w
who
last -n 20
last reboot -n 10
```

- `w`: users, source addresses, idle time, and current activity.
- `last -n 20`: recent sessions.
- `last reboot`: reboot history.

### One-screen resource baseline

```bash
uptime
free -h
df -hT
df -i
systemctl --failed --no-pager
journalctl -p warning -n 50 --no-pager
ip -br address
ip route
ss -lntup
```

This baseline answers whether the host has obvious load, memory, capacity,
inode, service, kernel/log, address, route, or listener problems.

## 2. CPU, Load, Scheduling, and Pressure

### CPU topology

```bash
lscpu
nproc
grep -E 'processor|model name|cpu MHz' /proc/cpuinfo
```

- `nproc`: processing units available to the current process; cgroups or
  affinity can make this differ from the physical host count.
- `lscpu -e`: extended per-CPU topology.

### Load and scheduler activity

```bash
uptime
cat /proc/loadavg
vmstat 1 5
mpstat -P ALL 1 5
pidstat -u -w 1 5
```

Important arguments:

- `vmstat 1 5`: one-second interval, five samples. Ignore the first line when
  judging current activity because it represents averages since boot.
- `mpstat -P ALL 1 5`: each CPU plus aggregate utilization.
- `pidstat -u -w 1 5`: per-process CPU and context-switch activity.

Fields to correlate:

- `r`: runnable tasks. Sustained values above available CPUs indicate CPU
  queueing.
- `b`: tasks blocked in uninterruptible sleep, commonly I/O.
- `us`: user CPU.
- `sy`: kernel/system CPU.
- `wa`: I/O wait.
- `st`: CPU time taken by the hypervisor.
- `cs`: context switches.
- `in`: interrupts.

High load is not proof of CPU saturation. High load with high `wa` or blocked
tasks points toward I/O or a stalled dependency.

### Pressure Stall Information

```bash
cat /proc/pressure/cpu
cat /proc/pressure/io
cat /proc/pressure/memory
```

- `some`: at least one task stalled.
- `full`: all non-idle tasks stalled simultaneously; available for I/O and
  memory pressure.
- `avg10`, `avg60`, `avg300`: percentage of wall time stalled.
- `total`: accumulated stall time in microseconds.

PSI measures contention impact, not merely resource consumption.

### Top CPU consumers and process state

```bash
ps -eo pid,ppid,user,state,ni,pri,psr,etimes,%cpu,%mem,comm,args --sort=-%cpu
top -b -n 1
pidstat -p <PID> -u -w 1 5
taskset -pc <PID>
```

- `state`: `R` runnable, `S` sleeping, `D` uninterruptible, `Z` zombie,
  `T` stopped.
- `psr`: CPU currently or most recently used.
- `etimes`: elapsed lifetime in seconds.
- `ni` and `pri`: nice value and scheduler priority.
- `taskset -pc`: CPU affinity for a process.

### Blocked and uninterruptible tasks

```bash
ps -eo state,pid,ppid,wchan:32,comm,args | awk '$1 ~ /^D/'
cat /proc/<PID>/stack
cat /proc/<PID>/wchan
```

Reading `/proc/<PID>/stack` can require root. A `D`-state task cannot normally
be killed until the kernel operation completes; investigate storage, NFS,
device, or kernel waits instead of repeatedly sending signals.

### CPU frequency, throttling, and virtualization

```bash
systemd-detect-virt
lscpu | grep -E 'Hypervisor|Virtualization'
grep -R . /sys/devices/system/cpu/cpu0/cpufreq/ 2>/dev/null
cat /sys/fs/cgroup/cpu.stat
cat /sys/fs/cgroup/cpu.max
```

For cgroup v2:

- `cpu.max`: quota and period; `max` means no quota.
- `cpu.stat`: usage plus throttling counters such as `nr_throttled` and
  `throttled_usec`.

## 3. Memory, Swap, OOM, and Cgroups

### Memory overview

```bash
free -h
cat /proc/meminfo
vmstat 1 5
sar -r 1 5
sar -W 1 5
```

Important interpretation:

- Use `MemAvailable`, not only `MemFree`.
- Linux uses free memory for page cache.
- Swap allocated is not the same as active swap pressure.
- `vmstat si/so` or `sar -W` reveals active swap-in and swap-out.

### Top memory consumers

```bash
ps -eo pid,ppid,user,state,etimes,rss,vsz,%mem,comm,args --sort=-rss
pidstat -r -p ALL 1 5
pmap -x <PID>
cat /proc/<PID>/status
cat /proc/<PID>/smaps_rollup
```

- `RSS`: resident physical memory.
- `VSZ`: virtual address space, not actual RAM consumption.
- `smaps_rollup`: aggregated private/shared/PSS memory when supported.
- `pmap -x`: process mapping totals.

### OOM evidence

```bash
journalctl -k -g 'oom|out of memory|killed process' --no-pager
dmesg -T | grep -Ei 'oom|out of memory|killed process'
grep -E 'oom|pgmajfault|workingset' /proc/vmstat
```

Do not conclude that an application crashed voluntarily when the kernel or a
cgroup killed it.

### cgroup memory

```bash
cat /proc/<PID>/cgroup
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.stat
```

For cgroup v2:

- `memory.current`: current usage.
- `memory.max`: hard limit; `max` means unlimited.
- `memory.events`: counters such as `high`, `max`, `oom`, and `oom_kill`.

The host can have free memory while a container or service cgroup reaches its
own limit.

### Kernel slab, huge pages, and shared memory

```bash
slabtop -o
grep -E 'Slab|SReclaimable|SUnreclaim|Huge|Shmem' /proc/meminfo
ipcs -m
sysctl vm.overcommit_memory vm.overcommit_ratio
```

`sysctl` without `-w` is read-only. Never change VM settings during evidence
collection.

## 4. Disk Capacity, Inodes, Filesystems, and I/O

Implemented AOP workflow:

```bash
aop linux disk --path <PATH>
aop linux space --path <PATH>
aop linux fs --path <PATH>
```

Bound recent growth searches:

```bash
aop linux disk --path /var/log --top 20 \
  --recent-minutes 30 --large-size-mb 500
```

AOP executes capacity/type, inode, mount, directory usage, recent large-file,
deleted-open file, and kernel-error evidence in that order.

Deterministic incident interpretation:

```bash
aop investigate linux disk --path <PATH>
aop investigate linux disk --path <PATH> --format json
```

Diagnosis priority:

```text
read-only filesystem
  -> kernel filesystem or storage I/O error
  -> inode exhaustion
  -> filesystem byte exhaustion
  -> deleted-open files
  -> rapid large-file growth
  -> insufficient evidence
```

Storage integrity outranks space usage because deleting data is not a safe
response to a filesystem that has become read-only or is reporting I/O
errors. Inode exhaustion remains separate from byte exhaustion because large
file cleanup may not solve excessive small-file creation. Missing or
permission-limited evidence reduces confidence and must be reported.

### Capacity and filesystem type

```bash
df -hT
df -i
findmnt -r
findmnt -no SOURCE,FSTYPE,OPTIONS,TARGET <MOUNT>
lsblk -o NAME,TYPE,SIZE,FSTYPE,FSVER,MOUNTPOINTS,ROTA,MODEL,SERIAL
```

- `df -hT`: capacity plus filesystem type.
- `df -i`: inode usage; a filesystem can fail with free bytes but no inodes.
- `findmnt`: source, mount point, type, and mount options.
- `ROTA`: rotational-device indicator, useful but not always reliable through
  virtualized storage.

### Directory and file growth

```bash
du -x -h --max-depth=1 <PATH> | sort -h
du -x -a <PATH> | sort -n | tail -n 20
find <PATH> -xdev -type f -printf '%s %p\n' | sort -n | tail -n 20
```

Safety arguments:

- `-x` or `-xdev`: stay on one filesystem.
- `--max-depth=1`: bound recursion.
- Select a focused path such as `/var`, `/opt`, or an application directory;
  avoid an unrestricted scan of `/` during an incident.

### Deleted files still consuming space

```bash
lsof +L1
lsof +L1 <MOUNT>
```

This explains many `df` versus `du` mismatches. The space is released only
when the owning process closes the deleted file; preserve evidence before
deciding whether a service restart is appropriate.

### I/O latency and saturation

```bash
iostat -xz 1 5
pidstat -d 1 5
sar -d 1 5
cat /proc/diskstats
```

Important `iostat -xz` fields vary by version, but commonly include:

- `r/s`, `w/s`: operations per second.
- `rMB/s`, `wMB/s`: throughput.
- `await`: average request latency.
- `aqu-sz`: average queue depth.
- `%util`: device busy time; interpretation differs for parallel devices and
  storage arrays.

No single threshold fits every storage system. Compare latency with the
device type and the application's normal baseline.

### Filesystem and device errors

```bash
journalctl -k -g 'I/O error|EXT4-fs|XFS|BTRFS|nvme|scsi|reset|read-only' --no-pager
dmesg -T | grep -Ei 'I/O error|EXT4-fs|XFS|BTRFS|nvme|scsi|reset|read-only'
findmnt -no OPTIONS <MOUNT>
```

A read-only remount can indicate filesystem or storage failure, not merely a
permissions problem.

### LVM, RAID, multipath, and device mapper

```bash
pvs
vgs
lvs -a -o +devices
dmsetup ls --tree
cat /proc/mdstat
mdadm --detail /dev/<MD_DEVICE>
multipath -ll
```

Some commands require root for complete output. These commands inspect the
storage stack; they do not repair it.

### NFS and remote filesystems

```bash
findmnt -t nfs,nfs4
nfsstat -m
nfsstat -c
mountstats
ss -tanp | grep ':2049'
rpcinfo -p <HOST>
```

Stale or slow NFS can create `D`-state tasks and high load with low CPU usage.
Avoid `du` across remote mounts during first response.

## 5. Processes, Threads, Files, and Limits

### Process inventory

```bash
ps -eo pid,ppid,user,group,state,etimes,lstart,%cpu,%mem,rss,vsz,nlwp,comm,args
pstree -ap
pgrep -a <PROCESS_NAME>
```

- `nlwp`: thread count.
- `lstart`: process start time.
- `pgrep -a`: matching PIDs with full command lines.

### One process in depth

```bash
ps -p <PID> -o pid,ppid,user,group,state,etimes,lstart,%cpu,%mem,rss,vsz,nlwp,args
cat /proc/<PID>/status
cat /proc/<PID>/limits
cat /proc/<PID>/cgroup
readlink -f /proc/<PID>/exe
readlink -f /proc/<PID>/cwd
tr '\0' ' ' < /proc/<PID>/cmdline
```

Do not capture `/proc/<PID>/environ` by default; it can expose passwords,
tokens, and credentials.

### Open files and file descriptors

```bash
lsof -p <PID>
ls -l /proc/<PID>/fd
find /proc/<PID>/fd -maxdepth 1 -type l | wc -l
cat /proc/<PID>/limits | grep -i 'open files'
cat /proc/sys/fs/file-nr
```

Correlate process limits, current descriptor count, and system-wide file table
usage.

### Threads and stacks

```bash
ps -T -p <PID>
top -H -p <PID>
pidstat -t -p <PID> 1 5
```

`strace` and debuggers can affect production processes. If authorized:

```bash
strace -f -tt -T -p <PID> -o /tmp/strace.<PID>.log
```

- `-f`: follow child processes/threads.
- `-tt`: timestamps with microseconds.
- `-T`: syscall duration.
- `-p`: attach to the process.
- `-o`: write bounded evidence to a file.

Use briefly and with approval; tracing can add overhead and expose sensitive
data.

### Zombies and process states

```bash
ps -eo state,pid,ppid,comm,args | awk '$1 ~ /^Z/'
ps -eo state,pid,ppid,wchan:32,comm,args | awk '$1 ~ /^D/'
```

Zombie processes are already dead; the parent must reap them. Killing the
zombie itself is not a meaningful remedy.

## 6. Services and systemd

### Failed and active units

```bash
systemctl --failed --no-pager
systemctl list-units --type=service --state=running --no-pager
systemctl list-units --type=service --state=failed --no-pager
systemctl is-system-running
```

### One service in depth

```bash
systemctl status <UNIT> --no-pager --full
systemctl show <UNIT>
systemctl cat <UNIT>
systemctl list-dependencies <UNIT>
systemctl list-dependencies --reverse <UNIT>
journalctl -u <UNIT> --since '<SINCE>' --no-pager
```

- `status --full`: avoids ellipsized lines.
- `show`: machine-readable properties including `Result`, `ExecMainStatus`,
  restart counters, limits, and cgroup.
- `cat`: unit file plus drop-ins.
- `list-dependencies --reverse`: units that depend on this unit.

### Service execution and restart history

```bash
systemctl show <UNIT> -p ActiveState -p SubState -p Result \
  -p ExecMainCode -p ExecMainStatus -p NRestarts -p MainPID
journalctl -u <UNIT> -b --no-pager
```

Inspect status, logs, dependencies, resource pressure, permissions, and
configuration before restarting. A restart can erase the most useful state.

### Timers and sockets

```bash
systemctl list-timers --all --no-pager
systemctl list-sockets --all --no-pager
systemctl status <TIMER_OR_SOCKET> --no-pager --full
```

## 7. Logs, Journal, Kernel, and Incident Time Windows

### Journal queries

```bash
journalctl -b --no-pager
journalctl -b -1 --no-pager
journalctl -p warning --since '<SINCE>' --no-pager
journalctl -k --since '<SINCE>' --no-pager
journalctl -u <UNIT> --since '<SINCE>' --until '<END>' --no-pager
journalctl --list-boots
journalctl --disk-usage
```

Important arguments:

- `-b`: current boot.
- `-b -1`: previous boot.
- `-k`: kernel messages.
- `-p warning`: warning through emergency priorities.
- `--since` and `--until`: incident time window.
- `-o short-iso-precise`: precise, sortable timestamps.
- `-n <COUNT>`: bound output.

Preferred incident query:

```bash
journalctl -o short-iso-precise --since '<SINCE>' --until '<END>' \
  -p warning --no-pager
```

### Traditional log files

```bash
tail -n 100 /var/log/messages
tail -n 100 /var/log/syslog
tail -n 100 /var/log/auth.log
tail -n 100 /var/log/secure
zgrep -i '<PATTERN>' /var/log/<LOG>*
```

Paths differ by distribution. Use journald when authoritative, and avoid
assuming every file exists.

### Kernel messages

```bash
dmesg -T
dmesg --level=emerg,alert,crit,err,warn
journalctl -k -p warning --no-pager
```

`dmesg -T` human timestamps can be inaccurate after clock changes. Journal
timestamps are better for cross-system incident correlation.

## 8. Network Troubleshooting Sequence

Use this order:

```text
link -> errors -> address -> neighbor -> route -> gateway -> DNS
     -> remote port -> TLS/protocol -> local listener -> firewall
```

### Interfaces, addresses, and link counters

```bash
ip -br link
ip -br address
ip -s link show dev <IFACE>
ethtool <IFACE>
ethtool -S <IFACE>
```

- `ip -br`: concise output.
- `ip -s link`: RX/TX errors, drops, overruns, and carrier issues.
- `ethtool`: speed, duplex, link state.
- `ethtool -S`: driver-specific counters.

### Routes and policy routing

```bash
ip route
ip route show table all
ip rule show
ip route get <DESTINATION_IP>
```

`ip route get` shows the actual selected source address, interface, gateway,
and route for a destination.

### Neighbor and ARP state

```bash
ip neighbor show
ip neighbor show nud failed
arping -I <IFACE> <GATEWAY_IP>
```

`arping` actively sends packets. Use a bounded count where supported:

```bash
arping -c 3 -I <IFACE> <GATEWAY_IP>
```

### Basic reachability

```bash
ping -c 3 -W 2 <IP>
ping -c 3 -W 2 <HOST>
tracepath <HOST>
traceroute -n <HOST>
mtr -n -r -c 10 <HOST>
```

- IP succeeds, hostname fails: investigate DNS.
- Ping failure does not prove the service is down; ICMP may be filtered.
- `mtr -r -c 10`: report mode with a bounded cycle count.

### DNS

```bash
cat /etc/resolv.conf
resolvectl status
getent ahosts <HOST>
dig <HOST>
dig +short <HOST>
dig +trace <HOST>
dig @<DNS_SERVER> <HOST>
dig -x <IP>
nslookup <HOST>
```

Use `getent` to test the host's configured name-service path, including
`nsswitch.conf`, local files, and configured resolvers. `dig` directly tests
DNS and can bypass parts of the system resolver path.

### Listening and connected sockets

```bash
ss -lntup
ss -tanp
ss -s
ss -tan state established
ss -tan state time-wait
ss -lntp 'sport = :<PORT>'
lsof -nP -iTCP:<PORT> -sTCP:LISTEN
```

- `-l`: listening.
- `-n`: no name resolution.
- `-t`, `-u`: TCP and UDP.
- `-p`: owning process; may require root.
- `ss -s`: summary including socket pressure.

### Port and application reachability

```bash
nc -vz -w 3 <HOST> <PORT>
curl -v --connect-timeout 3 --max-time 10 http://<HOST>:<PORT>/
curl -vk --connect-timeout 3 --max-time 10 https://<HOST>:<PORT>/
openssl s_client -connect <HOST>:<PORT> -servername <DNS_NAME> -brief
```

- `nc -vz`: TCP connection test without sending application data.
- `curl --connect-timeout`: bound connection establishment.
- `curl --max-time`: bound the entire request.
- `-k` disables certificate validation; use only to separate connectivity from
  trust failure, and report that validation was bypassed.
- `openssl -servername`: sends SNI for virtual hosts.

### Packet capture

```bash
tcpdump -ni <IFACE> -c 100 host <HOST>
tcpdump -ni <IFACE> -c 100 port <PORT>
tcpdump -ni any -c 100 'host <HOST> and port <PORT>'
```

- `-n`: no DNS lookups.
- `-i`: interface.
- `-c`: strict packet bound.

Packet capture requires authorization and can expose sensitive payload or
metadata. Prefer narrow filters and bounded counts.

### Firewall and connection tracking

```bash
nft list ruleset
iptables -S
iptables -L -n -v
ufw status verbose
firewall-cmd --state
firewall-cmd --list-all
sysctl net.netfilter.nf_conntrack_count
sysctl net.netfilter.nf_conntrack_max
conntrack -S
```

These are inspection commands. Do not flush or modify rules during diagnosis.

### Network namespace and Kubernetes node context

```bash
ip netns list
nsenter -t <PID> -n ip address
nsenter -t <PID> -n ip route
nsenter -t <PID> -n ss -lntup
```

Entering another process namespace can require root. Use it to compare host
and container network views, not to modify them.

## 9. Boot, Time, Kernel, Hardware, and Devices

### Boot health

```bash
systemctl is-system-running
systemd-analyze time
systemd-analyze blame
systemd-analyze critical-chain
journalctl -b -p warning --no-pager
journalctl -b -1 -p warning --no-pager
```

`systemd-analyze blame` shows activation time, not necessarily the root cause
of boot delay. Use `critical-chain` for ordering dependencies.

### Kernel and loaded modules

```bash
uname -a
lsmod
modinfo <MODULE>
sysctl -a
```

`sysctl -a` can be large and may expose environment details. Prefer focused
keys such as:

```bash
sysctl fs.file-nr
sysctl vm.swappiness
sysctl net.ipv4.ip_local_port_range
```

### Hardware and device inventory

```bash
lspci -nnk
lsusb
lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL
lshw -short
dmidecode -t system
```

`dmidecode` normally requires root. In cloud or virtual environments, combine
hardware output with instance metadata and hypervisor evidence.

### Device health

```bash
smartctl -a /dev/<DEVICE>
nvme smart-log /dev/<NVME_DEVICE>
sensors
```

These require the relevant packages and often elevated read access. Cloud
volumes and virtual disks may not expose physical-device health.

## 10. Security, Identity, Permissions, and Access

### Identity and account state

```bash
id
id <USER>
getent passwd <USER>
getent group <GROUP>
groups <USER>
passwd -S <USER>
chage -l <USER>
```

`passwd -S` and `chage -l` inspect account and password-aging state; access can
vary by distribution and privilege.

### File permissions and path traversal

```bash
ls -ld <PATH>
stat <PATH>
namei -l <PATH>
getfacl -p <PATH>
lsattr <PATH>
```

- `namei -l`: permissions on every component of a path.
- `getfacl`: ACLs that can override the simple mode-bit interpretation.
- `lsattr`: extended attributes such as immutable.

### Authentication evidence

```bash
last -n 20
lastb -n 20
journalctl -u ssh -u sshd --since '<SINCE>' --no-pager
journalctl _COMM=sudo --since '<SINCE>' --no-pager
```

`lastb` often requires root and depends on failed-login accounting.

### SELinux and AppArmor

```bash
getenforce
sestatus
ausearch -m AVC,USER_AVC -ts recent
aa-status
journalctl -k -g 'apparmor|avc: denied' --no-pager
```

Do not disable SELinux or AppArmor as a troubleshooting shortcut. Identify the
specific denial and required policy or labeling correction.

### Certificates

```bash
openssl x509 -in <CERTIFICATE> -noout -subject -issuer -dates -fingerprint
openssl s_client -connect <HOST>:<PORT> -servername <DNS_NAME> -showcerts
```

Never print private keys.

## 11. Packages, Configuration, and Recent Changes

### Package ownership and version

Debian/Ubuntu:

```bash
dpkg -S <PATH>
dpkg -l <PACKAGE>
apt-cache policy <PACKAGE>
zgrep -h '<PACKAGE>' /var/log/apt/history.log*
```

RHEL/Rocky/Alma/Amazon Linux:

```bash
rpm -qf <PATH>
rpm -qi <PACKAGE>
dnf info <PACKAGE>
dnf history list
dnf history info <ID>
```

### Verify packaged files

```bash
debsums <PACKAGE>
rpm -V <PACKAGE>
```

Verification output requires careful interpretation because legitimate
configuration changes may appear as differences.

### Recently changed files

```bash
find <PATH> -xdev -type f -mmin -60 -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n'
find <PATH> -xdev -type f -mtime -1 -ls
```

Bound searches to relevant configuration or application paths. Do not scan
all of `/` by default.

### Configuration comparison

```bash
stat <CONFIG_FILE>
sha256sum <CONFIG_FILE>
diff -u <KNOWN_GOOD_FILE> <CONFIG_FILE>
```

Do not copy secrets or unredacted configuration into incident reports.

## 12. Containers, Namespaces, and Kubernetes Nodes

### Container and namespace identity

```bash
systemd-detect-virt
cat /proc/1/cgroup
lsns
nsenter -t <PID> -m -u -i -n -p -- ps -ef
```

`nsenter` requires care and usually root. The command shown executes `ps`
inside the target namespaces without changing state.

### Container runtime

```bash
systemctl status containerd --no-pager --full
journalctl -u containerd --since '<SINCE>' --no-pager
crictl info
crictl ps -a
crictl inspect <CONTAINER_ID>
crictl stats
```

For Docker-based environments:

```bash
docker info
docker ps -a
docker inspect <CONTAINER_ID>
docker stats --no-stream
```

### Kubernetes node services

```bash
systemctl status kubelet --no-pager --full
journalctl -u kubelet --since '<SINCE>' --no-pager
crictl ps -a
df -hT /var/lib/kubelet /var/lib/containerd
df -i /var/lib/kubelet /var/lib/containerd
```

Correlate node evidence with:

```bash
kubectl describe node <NODE>
kubectl get events --all-namespaces --field-selector involvedObject.kind=Node
kubectl top node <NODE>
```

Kubernetes commands run from an authorized control context, while Linux
commands run on the affected node.

## 13. Remote Host and Cloud Context

### SSH diagnostic execution

```bash
ssh -o ConnectTimeout=5 -o BatchMode=yes <HOST> 'hostname; uptime'
ssh -vvv -o ConnectTimeout=5 <HOST>
```

- `BatchMode=yes`: avoids hanging on interactive password prompts.
- `-vvv`: client-side SSH negotiation evidence; output can contain hostnames,
  usernames, and environment details and must be handled carefully.

Future AOP remote collection must use approved credentials, least privilege,
timeouts, command allowlists, redaction, and an audit trail.

### Cloud instance identity

Cloud metadata access is provider-specific and security-sensitive. AOP should
use cloud SDKs or approved metadata clients, never unrestricted metadata
fetching or credential endpoint access.

## 14. Safe Evidence Bundles

Useful bounded output:

```bash
aop linux health --json
aop linux all --json > linux-report.json
journalctl -o short-iso-precise --since '<SINCE>' --until '<END>' \
  -p warning --no-pager > incident-journal.txt
```

Before sharing:

- remove tokens, secrets, private addresses when required by policy
- avoid `/proc/<PID>/environ`
- review command lines for embedded credentials
- review logs for headers, cookies, connection strings, and customer data
- record collection time, host, command, privilege, and truncation

## 15. Commands Requiring Explicit Approval

The following are not default diagnostic actions:

```text
systemctl restart/stop/start
kill, killall, pkill
rm, truncate, log deletion
mount, umount, filesystem repair
iptables/nft/firewall modifications
sysctl -w
package install/update/remove
user, group, permission, ACL, or SELinux changes
swapoff/swapon
reboot/shutdown
container or pod deletion
```

They can alter evidence, create outages, or expand impact. AOP must separate
observation from action and require policy plus human approval for
consequential changes.

## 16. AOP Implementation Priority

### Tier 1: Always-on baseline

- host identity and time
- uptime and load
- available memory and swap activity
- filesystem capacity and inodes
- failed services
- warning/error journal
- interfaces, routes, DNS, and listeners

### Tier 2: Deterministic correlation

- load versus CPU, I/O wait, blocked tasks, and PSI
- available memory versus swap, OOM, process RSS, and cgroups
- `df` versus `du`, inodes, deleted-open files, and storage latency
- service result versus logs, dependencies, limits, and resource pressure
- route versus DNS, port, TLS, listener, firewall, and conntrack evidence

Implemented timed evidence commands:

```bash
aop linux internals --interval 5
aop linux cgroups --pid <PID> --interval 5
```

Timed mode converts cumulative VM, PSI, and cgroup counters into interval
deltas and rates. It also verifies that the process remains in the same cgroup
before comparing counters.

### Tier 3: Deep investigation

- process maps, threads, syscalls, namespaces, and limits
- LVM, multipath, RAID, NFS, and device health
- SELinux/AppArmor and authentication
- container runtime, kubelet, and Kubernetes node correlation
- recent package and configuration changes

### Tier 4: AI and operational memory

- retrieve relevant runbooks and past incidents
- explain deterministic findings
- identify evidence gaps
- recommend the next read-only command
- generate grounded RCA and safe remediation guidance

AI must not replace command evidence or claim that an unavailable check passed.
