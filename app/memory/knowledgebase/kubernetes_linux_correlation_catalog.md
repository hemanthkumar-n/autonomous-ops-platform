# Kubernetes To Linux Correlation Catalog

This is AOP's v0.20 Kubernetes issue training memory.

It does not train a model by changing weights. It trains the AOP agents by
preserving explicit SRE rules in source control: when Kubernetes shows a
symptom, AOP should know which Linux evidence is required before AI reasoning
or remediation advice.

## Core Rule

```text
Kubernetes symptom
  -> preserve Kubernetes evidence
  -> identify plausible Linux node causes
  -> request the safest Linux evidence
  -> state missing evidence
  -> avoid invented host facts
```

## Covered Symptoms

| Kubernetes symptom | Linux evidence focus |
|---|---|
| `OOMKilled` | memory, cgroups, PSI, VM counters, kernel OOM logs |
| `CrashLoopBackOff` | previous logs, exit reason, process state, memory, dependency network |
| `ImagePullBackOff` | DNS, route, NIC, registry reachability, runtime disk |
| `ErrImagePull` | first pull error, registry/auth/network path |
| `CreateContainerConfigError` | config references, secrets/configmaps, projected volume clues |
| `CreateContainerError` | kubelet/runtime logs, runtime storage, cgroup setup |
| `FailedScheduling` | node capacity, pressure, taints, affinity, autoscaler limits |
| `DiskPressure` | filesystem bytes, inodes, kubelet/runtime paths, deleted-open files |
| `MemoryPressure` | node memory, swap, PSI, OOM, eviction evidence |
| `NodeNotReady` | kubelet, runtime, network, disk, memory, CPU, cloud instance health |

## Implementation

The executable catalog lives in:

```text
app/agents/sre/k8s_linux_correlation_agent.py
```

The CLI entry point is:

```bash
aop investigate k8s-linux --list
aop investigate k8s-linux --incident OOMKilled
aop investigate k8s-linux --incident DiskPressure --format json
```

This is a planning and training layer. It does not SSH to nodes, run `kubectl`,
or collect Linux evidence automatically.
