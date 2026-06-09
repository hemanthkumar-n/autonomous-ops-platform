from __future__ import annotations


KUBERNETES_LINUX_CORRELATION_POLICY = """
Cross-domain Linux and Kubernetes policy:
- Treat Kubernetes as an orchestration layer running on Linux infrastructure.
- Do not assume a pod-level symptom has a pod-only cause.
- For OOM, CPU pressure, disk or inode pressure, networking, DNS, storage,
  runtime, scheduling, or node-readiness symptoms, correlate Kubernetes
  evidence with relevant Linux node evidence when it is available.
- Relevant Linux evidence may include kernel and OOM logs, cgroup limits,
  pressure stall information, memory and swap activity, filesystem and inode
  state, disk latency, process state, sockets, routes, DNS, firewall,
  conntrack, systemd, kubelet, and container-runtime health.
- Distinguish confirmed evidence from hypotheses.
- When required Linux node evidence is missing, state the evidence gap and
  recommend the exact read-only AOP Linux diagnostic command to collect next.
- Never invent host-level facts from Kubernetes symptoms alone.
""".strip()
