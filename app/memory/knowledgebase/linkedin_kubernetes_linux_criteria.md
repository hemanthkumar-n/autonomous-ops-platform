# Authored Knowledge: Kubernetes and Linux Troubleshooting

## Source

- Author: Hemanth Kumar
- Source type: LinkedIn post
- Post URL:
  <https://www.linkedin.com/posts/hemanthkumarn_kubernetes-sre-linux-share-7470154226396995585-ILcv/>
- Supplied to AOP memory: June 10, 2026
- Topics: AI troubleshooting, Kubernetes, Linux, SRE

LinkedIn prevented automated retrieval of the complete post body. This record
therefore preserves the source URL and only the troubleshooting criterion
explicitly confirmed by the author. It does not claim to reproduce or quote
the post.

## Author-Confirmed Criterion

Kubernetes troubleshooting and Linux troubleshooting must not be treated as
unrelated operational domains.

Kubernetes provides orchestration state, but workloads run through Linux
kernel, cgroup, filesystem, process, network, service, kubelet, and
container-runtime behavior. A Kubernetes symptom can therefore originate from
the workload, the node, or the interaction between them.

## AI Troubleshooting Requirements

When AOP analyzes a Kubernetes incident, AI reasoning must:

1. Begin with Kubernetes evidence such as pod state, termination history,
   events, logs, resource settings, node placement, and metrics.
2. Decide whether the symptom can plausibly originate from the Linux node.
3. Correlate available host evidence before reaching a cross-domain
   conclusion.
4. Clearly separate confirmed findings, likely explanations, and unverified
   hypotheses.
5. Identify missing Linux evidence instead of inventing node-level facts.
6. Recommend the next read-only diagnostic command when evidence is missing.
7. Preserve operational evidence before recommending restarts or changes.

## Correlation Matrix

| Kubernetes symptom | Linux evidence to correlate |
|---|---|
| `OOMKilled`, memory pressure | kernel OOM records, cgroup limits, available memory, swap activity, PSI, process RSS |
| CPU throttling, high latency | load, run queue, per-core use, steal time, I/O wait, cgroup quotas, blocked tasks |
| `DiskPressure`, eviction | filesystem capacity, inodes, mounts, deleted-open files, device latency, kernel storage errors |
| DNS or service connectivity | interfaces, routes, neighbors, resolver state, sockets, firewall, conntrack, kube-proxy/CNI context |
| Node `NotReady` | kubelet, container runtime, systemd, kernel, time synchronization, disk, memory, and network health |
| Volume mount or I/O failure | mounts, filesystem state, NFS/storage reachability, device mapper, multipath, kernel messages |
| Crash loops | termination reason, application logs, service dependencies, permissions, filesystems, OOM, and runtime state |
| Image pull failure | node DNS, route, proxy, certificates, registry reachability, disk capacity, and runtime logs |

## AOP Command Guidance

Examples of evidence-gap recommendations:

```bash
aop linux health
aop linux memory
aop linux cpu
aop linux disk --path /var
aop linux network
aop linux services
aop linux logs
aop linux kernel
```

These commands currently run on the Linux host being investigated. Remote
host collection and automatic node correlation remain future capabilities.

## Durable Product Rule

The final AOP experience should unify Linux, Kubernetes, observability, cloud,
runbooks, and incident memory behind one investigation. Domain commands remain
collectors underneath that single troubleshooting workflow.
