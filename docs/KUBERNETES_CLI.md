# AOP Kubernetes Shortcuts

Use `aop kb` for fast, read-only SRE troubleshooting. `aop k8s` is an
equivalent alias.

Use `aop investigate k8s-linux` when you want AOP to explain which Linux
evidence a Kubernetes symptom requires before deeper RCA:

```bash
aop investigate k8s-linux --list
aop investigate k8s-linux --incident OOMKilled
aop investigate k8s-linux --incident DiskPressure --format json
```

Use `aop investigate k8s-knowledge` when you want curated Kubernetes issue
knowledge, safe commands, do-not-assume rules, and source links:

```bash
aop investigate k8s-knowledge --list
aop investigate k8s-knowledge --symptom CrashLoopBackOff
aop investigate k8s-knowledge --symptom DiskPressure --format json
```

Use `aop kx` when you need short expert shortcuts:

```bash
aop kx list
aop kx oom
aop kx crash
aop kx image
aop kx disk
aop kx node
aop kx explain DiskPressure --json
```

## First Response

```bash
aop kb health
aop kb po
aop kb ev
```

Scope any command to a namespace with `-n`:

```bash
aop kb health -n payments
aop kb po -n payments
aop kb ev -n payments
```

## Commands

| Command | Short alias | Purpose |
|---|---|---|
| `aop kb health` | | Cluster readiness and unhealthy pods |
| `aop kb nodes` | `aop kb no` | Node readiness, pressure, and capacity |
| `aop kb namespaces` | `aop kb ns` | Namespace inventory |
| `aop kb deployments` | `aop kb deploy` | Unhealthy deployment replicas |
| `aop kb services` | `aop kb svc` | Service types, addresses, and ports |
| `aop kb pods` | `aop kb po` | Unhealthy pods |
| `aop kb events` | `aop kb ev` | Recent warning events |
| `aop kb logs POD` | `aop kb log POD` | Bounded current or previous logs |
| `aop kb describe POD` | `aop kb desc POD` | Pod state, resources, and events |
| `aop kb investigate` | `aop kb inv` | Full AI and memory-aware investigation |

## Common Examples

Show all pods rather than only unhealthy pods:

```bash
aop kb po -n payments --all
```

Read the previous crashed container:

```bash
aop kb log checkout-abc123 \
  -n payments \
  -c checkout \
  --previous
```

Inspect one pod:

```bash
aop kb desc checkout-abc123 -n payments
```

Run full investigation and export a report:

```bash
aop kb inv \
  -n payments \
  --format markdown \
  --output reports/payments-incident.md
```

Most inventory commands support `--json` for scripts:

```bash
aop kb po -n payments --json
aop kb health --json
```

These commands do not modify cluster resources.

Safe issue simulation manifests are listed in
[`incidents/kubernetes-simulation-catalog.md`](incidents/kubernetes-simulation-catalog.md).
