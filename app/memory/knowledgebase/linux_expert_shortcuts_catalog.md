# Linux Expert Shortcuts Catalog

This is AOP's v0.24 Linux shortcut memory.

The goal is fast SRE muscle memory without hiding the reasoning. Each shortcut
must preserve:

- first safe checks
- next AOP commands
- dangerous commands to avoid
- do-not-assume rule
- Kubernetes relation
- cloud relation

## CLI

```bash
aop lx list
aop lx boot
aop lx kernel
aop lx grub
aop lx storage
aop lx lvm
aop lx dns
aop lx nfs
aop lx limits
aop lx selinux
aop lx runtime
aop lx explain storage --json
```

## Shortcuts

| Shortcut | Purpose |
|---|---|
| `boot` | previous boot, unexpected reboot, boot delay, failed boot units |
| `kernel` | panic, OOM, hung task, driver reset, kernel warning |
| `grub`, `grubby` | default kernel, boot args, cgroups, crashkernel, rollback |
| `storage` | filesystem, I/O, read-only remount, device latency |
| `lvm` | PV/VG/LV/filesystem resize mismatch |
| `dns` | resolver, route, service discovery, registry lookup |
| `nfs` | stale mounts, D-state, NFS reachability |
| `limits`, `ulimit` | file descriptors, process limits, systemd limits |
| `selinux` | AVC denials, labels, access despite Unix permissions |
| `runtime`, `container` | containerd, kubelet paths, runtime disk pressure |

## Guardrail

Shortcuts must not execute destructive actions. Commands such as `fsck`,
`xfs_repair`, `grubby --update-kernel`, `systemctl restart`, `setenforce 0`,
`umount -f`, and runtime directory deletion are listed as dangerous so the
operator sees the risk before acting.

## Product Rule

Linux expert shortcuts are not replacements for deterministic investigators.
They are the fast front door into Linux troubleshooting knowledge. When AOP has
a deterministic investigator, the shortcut should point to that command.
