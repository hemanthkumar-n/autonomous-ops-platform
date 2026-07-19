# Linux Disk Troubleshooting: `df -h` Is Only the Beginning

**Author:** Hemanth Kumar
**Project:** Autonomous Ops Platform (AOP)
**Topic:** Linux, Kubernetes, AWS, SRE, and AI-assisted troubleshooting

## LinkedIn Post

When someone tells me:

> "The Linux server disk is full."

I do not immediately delete files.

I first ask: **What exactly is full, where is it full, and why did it grow?**

`df -h` is useful, but it is only the beginning of a disk investigation.

### 1. Check filesystem capacity and type

```bash
df -hT
```

This shows:

- filesystem size
- used and available space
- usage percentage
- filesystem type
- mount point

The filesystem type matters. Troubleshooting `ext4`, XFS, NFS, overlay
filesystems, and container storage may require different reasoning.

### 2. Check inode usage

```bash
df -i
```

A filesystem may have free disk space but still fail to create files because
all inodes are consumed.

This commonly happens when an application creates a very large number of
small files.

The error may still appear as:

```text
No space left on device
```

That does not always mean the filesystem has run out of bytes.

### 3. Confirm the mount and storage layout

```bash
findmnt
findmnt -no SOURCE,FSTYPE,OPTIONS,TARGET /var
lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,ROTA,MODEL
```

Before scanning directories, I confirm:

- which device backs the affected path
- whether it is a local or remote filesystem
- whether the correct filesystem is mounted
- whether the mount became read-only
- whether LVM, RAID, device mapper, or cloud storage is involved

A missing mount can make applications write into the underlying root
filesystem without anyone noticing.

### 4. Find the directory consuming space

Start with a focused and filesystem-bounded scan:

```bash
du -x -h --max-depth=1 /var | sort -h
```

Then continue only inside the directory that is growing:

```bash
du -x -h --max-depth=1 /var/log | sort -h
du -x -a /var/log | sort -n | tail -n 20
```

Why use `-x`?

It prevents `du` from crossing into other mounted filesystems during the
investigation.

Why avoid immediately running an unrestricted `du` against `/`?

On a busy production server, a large recursive scan can create unnecessary
I/O and make an incident worse.

### 5. Find large files safely

```bash
find /var -xdev -type f -printf '%s %p\n' | sort -n | tail -n 20
```

This helps identify:

- oversized logs
- core dumps
- temporary files
- application artifacts
- package caches
- database or backup growth

But file size alone does not explain why it grew. I still correlate the file
with its owner, process, service, deployment, and recent changes.

### 6. Investigate `df` and `du` disagreement

If `df` says the filesystem is full but `du` cannot account for the usage, I
check for deleted files that are still open:

```bash
lsof +L1
lsof +L1 /var
```

A process can continue writing to a file after the file has been deleted.
The filename disappears, but the disk blocks remain allocated until the
process closes the file.

This is why blindly deleting a large active log may not release space.

Before restarting or stopping the owning process, preserve the evidence and
understand the service impact.

Other reasons for a `df` and `du` mismatch can include:

- files hidden under a mount point
- filesystem reserved blocks
- snapshots
- sparse files
- bind mounts
- container overlay storage
- different views created by mount namespaces

### 7. Separate capacity problems from I/O problems

A disk does not need to be full to cause an outage.

Check latency, queueing, and saturation:

```bash
iostat -xz 1 5
pidstat -d 1 5
```

Important evidence includes:

- read and write operations
- throughput
- request latency
- queue depth
- device busy time
- processes generating I/O

There is no universal `%util` or `await` threshold for every storage system.
The device type, virtualization layer, workload, and normal baseline matter.

### 8. Check kernel and filesystem errors

```bash
journalctl -k -g 'I/O error|EXT4-fs|XFS|BTRFS|nvme|scsi|reset|read-only' \
  --no-pager
```

Also check whether the filesystem changed to read-only mode:

```bash
findmnt -no SOURCE,FSTYPE,OPTIONS,TARGET /var
```

Deleting files will not solve a failing device, filesystem corruption,
storage timeout, or read-only remount.

### 9. Inspect the storage layers

Depending on the server, the investigation may continue through:

```bash
pvs
vgs
lvs -a -o +devices
cat /proc/mdstat
multipath -ll
```

For LVM thin pools and snapshots, free space inside the mounted filesystem is
not the only capacity that matters.

### 10. Correlate Linux with Kubernetes

For a Kubernetes node, I also inspect:

```bash
du -x -h --max-depth=1 /var/lib/containerd | sort -h
du -x -h --max-depth=1 /var/lib/kubelet | sort -h
df -hT /var/lib/containerd /var/lib/kubelet
df -i /var/lib/containerd /var/lib/kubelet
```

Then correlate the Linux evidence with:

- Kubernetes `DiskPressure`
- pod eviction events
- container logs
- image and snapshot growth
- ephemeral storage requests and limits
- kubelet garbage collection
- orphaned pod data
- container runtime health

Kubernetes reports the orchestration symptom. Linux and the storage stack
often contain the underlying cause.

### 11. Correlate Linux with AWS

For an EC2 instance using EBS, I also ask:

- Is the correct EBS volume attached?
- Was the volume expanded but the partition or filesystem was not?
- Is the volume reaching its IOPS or throughput limit?
- Is burst balance exhausted?
- Are CloudWatch metrics showing abnormal queue length or latency?
- Is the instance itself limiting EBS bandwidth?

Increasing an EBS volume does not automatically mean every filesystem layer
has also been expanded.

### 12. Preserve evidence before remediation

I do not begin with:

```bash
rm -rf
truncate
systemctl restart
```

Those may remove evidence, interrupt a service, or hide the actual cause.

The correct troubleshooting flow is:

```text
Symptom
  -> confirm scope
  -> identify filesystem and storage layer
  -> check bytes and inodes
  -> locate growth
  -> explain mismatches
  -> inspect I/O and kernel errors
  -> correlate process, service, Kubernetes, and cloud evidence
  -> establish the cause
  -> choose the lowest-risk remediation
  -> verify recovery
  -> preserve the learning
```

This is the principle I am building into **Autonomous Ops Platform (AOP)**.

AOP should not merely run `df -h`, print several commands, and ask an AI model
to guess.

It should:

1. Understand the symptom.
2. Collect the minimum useful read-only evidence.
3. Interpret each result in context.
4. Decide which diagnostic branch is justified next.
5. Separate facts, hypotheses, and missing evidence.
6. Correlate Linux, Kubernetes, and AWS signals.
7. Avoid destructive action until the cause is supported.
8. Learn from the confirmed incident outcome.

The goal is not command automation alone.

The goal is to preserve experienced troubleshooting judgment and make it
available as one source of truth for SRE teams.

## Suggested Hashtags

```text
#Linux #LinuxAdmin #SRE #DevOps #Kubernetes #AWS #CloudComputing
#Troubleshooting #Observability #IncidentManagement #PlatformEngineering
#AIOps #AutonomousOps
```

## Short LinkedIn Version

When a Linux server reports that the disk is full, `df -h` is only the
beginning.

An experienced investigation separates:

- capacity exhaustion from inode exhaustion
- the expected mount from a missing or read-only mount
- visible file growth from deleted files still held open
- filesystem capacity from storage latency and device errors
- Linux host evidence from Kubernetes `DiskPressure`
- filesystem expansion from AWS EBS volume expansion

My usual evidence path starts with:

```bash
df -hT
df -i
findmnt
lsblk
du -x -h --max-depth=1 /var | sort -h
lsof +L1
iostat -xz 1 5
journalctl -k --no-pager
```

The important part is not running every command. It is understanding the
result, selecting the next diagnostic branch, and preserving evidence before
deleting files or restarting services.

This is what I am building into Autonomous Ops Platform (AOP): one
troubleshooting workflow that connects Linux, Kubernetes, AWS, operational
memory, and AI-assisted reasoning.

The objective is not to replace Linux experience. It is to preserve that
experience and make it available to the next engineer during an incident.

```text
#Linux #SRE #DevOps #Kubernetes #AWS #Troubleshooting
#PlatformEngineering #AIOps #AutonomousOps
```

## Publishing Note

LinkedIn does not render Markdown headings or fenced code blocks in the same
way as GitHub. Before publishing:

1. Use the heading lines as plain text.
2. Keep commands on separate lines for readability.
3. Remove the Markdown backticks.
4. Use the long version as an article or newsletter.
5. Use the short version as a standard LinkedIn post.
