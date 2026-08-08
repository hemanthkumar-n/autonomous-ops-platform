# Kubernetes Issue Knowledge Catalog

This is AOP's v0.21 curated Kubernetes issue memory.

The goal is not to dump every online issue into the project. Public issue
trackers contain duplicates, stale version-specific behavior, partial reports,
and unresolved speculation. AOP should ingest trusted and reviewed knowledge
first, then use selected external issues only after filtering.

## Trusted Source Baseline

- Kubernetes Debug Running Pods:
  <https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/>
- Kubernetes Node Status:
  <https://kubernetes.io/docs/reference/node/node-status/>
- Kubernetes Node-pressure Eviction:
  <https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/>
- Kubernetes Monitoring, Logging, and Debugging:
  <https://kubernetes.io/docs/tasks/debug/>

## Agent Rule

```text
Kubernetes symptom
  -> preserve Kubernetes evidence
  -> identify common causes
  -> request Linux evidence when node/runtime behavior may be involved
  -> recommend safe kubectl and AOP commands
  -> state do-not-assume rules
  -> cite source memory
```

## Covered Symptoms

| Symptom | Primary evidence |
|---|---|
| `CrashLoopBackOff` | previous logs, restart count, exit reason, events |
| `ImagePullBackOff` | image reference, pull events, registry auth, node network |
| `ErrImagePull` | first pull error, image reference, auth/network path |
| `OOMKilled` | limits, restart count, OOM evidence, cgroup memory, node pressure |
| `CreateContainerConfigError` | ConfigMap, Secret, env, volume, projected references |
| `CreateContainerError` | runtime events, kubelet logs, mounts, runtime storage |
| `FailedScheduling` | scheduler reason, resources, taints, affinity, quota |
| `DiskPressure` | node condition, filesystem bytes, inodes, runtime paths |
| `MemoryPressure` | node condition, evictions, memory metrics, PSI/OOM |
| `PIDPressure` | process count, pids cgroup, runtime process creation failures |
| `NodeNotReady` | node conditions, kubelet/runtime, network, host pressure |
| `NetworkUnavailable` | node condition, CNI, NIC, route, DNS, cloud network |

## CLI

```bash
aop investigate k8s-knowledge --list
aop investigate k8s-knowledge --symptom CrashLoopBackOff
aop investigate k8s-knowledge --symptom DiskPressure --format json
```

## Online Issue Ingestion Policy

Future online issue ingestion should preserve source quality:

- prefer official docs and vendor runbooks before random issue threads
- record source URL and Kubernetes version where relevant
- mark unresolved reports as hypotheses, not facts
- avoid storing credentials, tokens, customer data, or private log content
- deduplicate similar reports before adding them to memory
- connect each symptom to safe commands and evidence gaps

This keeps AOP's operational memory useful instead of noisy.
