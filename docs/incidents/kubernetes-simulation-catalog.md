# Kubernetes Simulation Catalog

These manifests create safe, intentional Kubernetes symptoms for AOP demos and
agent training. Apply them in a non-production namespace such as `ai-lab`.

```bash
kubectl create namespace ai-lab
```

## ImagePullBackOff

```bash
kubectl apply -f kubernetes/incidents/imagepull/broken-nginx.yaml
aop investigate k8s-linux --incident ImagePullBackOff
```

## OOMKilled

```bash
kubectl apply -f kubernetes/incidents/oomkilled/oom-test.yaml
aop investigate k8s-linux --incident OOMKilled
```

## CrashLoopBackOff

```bash
kubectl apply -f kubernetes/incidents/crashloop/crashloop-app.yaml
aop investigate k8s-linux --incident CrashLoopBackOff
```

## CreateContainerConfigError

```bash
kubectl apply -f kubernetes/incidents/configerror/missing-configmap.yaml
aop investigate k8s-linux --incident CreateContainerConfigError
```

## FailedScheduling

```bash
kubectl apply -f kubernetes/incidents/failedscheduling/oversized-pod.yaml
aop investigate k8s-linux --incident FailedScheduling
```

## Node Conditions

The v0.20 catalog also covers:

- `DiskPressure`
- `MemoryPressure`
- `NodeNotReady`

Those are intentionally documented as correlation plans rather than destructive
simulation manifests. Forcing node disk, memory, or readiness failures can
harm a shared cluster and should be done only in an isolated lab with a clear
cleanup plan.
