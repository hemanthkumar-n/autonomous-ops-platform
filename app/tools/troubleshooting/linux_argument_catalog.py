from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


ArgumentRisk = Literal["safe", "careful", "elevated", "destructive"]


@dataclass(frozen=True)
class CommandArgument:
    """
    Explain an individual command argument or flag.
    """

    flag: str
    meaning: str
    troubleshooting_value: str
    risk: ArgumentRisk = "safe"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CommandVariant:
    """
    Argument-aware command variant.

    This catalog helps AOP reason about why a variant should be selected,
    not just which command string to run.
    """

    key: str
    base_command: str
    variant: str
    category: str
    description: str
    arguments: tuple[CommandArgument, ...]
    incident_types: tuple[str, ...]
    related_commands: tuple[str, ...] = ()
    risk: ArgumentRisk = "safe"
    requires_root: bool = False
    agent_hint: str = ""
    source_notes: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        result = asdict(self)
        result["arguments"] = [argument.to_dict() for argument in self.arguments]
        return result


LINUX_ARGUMENT_AWARE_COMMANDS: tuple[CommandVariant, ...] = (
    CommandVariant(
        key="linux.files.ls_la",
        base_command="ls",
        variant="ls -la <path>",
        category="files",
        description="List files using long format and include hidden entries.",
        arguments=(
            CommandArgument("-l", "Long listing format", "Shows permissions, ownership, size, and modification time."),
            CommandArgument("-a", "Include hidden files", "Useful for dotfiles, hidden configs, and app/runtime state."),
        ),
        incident_types=("PermissionIssue", "ConfigDrift", "MissingFile", "UnexpectedFileChange"),
        related_commands=("stat <path>", "find <path> -maxdepth 1 -ls", "namei -l <path>"),
        agent_hint="Use when verifying file ownership, permissions, hidden config files, or unexpected application state.",
        source_notes=("Red Hat Developer Linux commands cheat sheet: ls examples include ls, ls -l, and ls -la.",),
    ),
    CommandVariant(
        key="linux.files.ls_ltr",
        base_command="ls",
        variant="ls -ltr <path>",
        category="files",
        description="List files by modification time with oldest first and newest at the bottom.",
        arguments=(
            CommandArgument("-l", "Long listing format", "Shows timestamp, ownership, permissions, and size."),
            CommandArgument("-t", "Sort by modification time", "Finds recently changed files during incidents."),
            CommandArgument("-r", "Reverse sort order", "Keeps newest entries near the bottom for easier terminal reading."),
        ),
        incident_types=("ConfigDrift", "DeploymentRegression", "LogRotationIssue", "UnexpectedFileChange"),
        related_commands=("stat <path>", "find <path> -type f -mtime -1 -ls", "journalctl --since '1 hour ago'"),
        agent_hint="Use after an incident starts to identify files changed around the failure window.",
    ),
    CommandVariant(
        key="linux.search.grep_context",
        base_command="grep",
        variant="grep -B 2 -A 2 <pattern> <file>",
        category="search",
        description="Search file contents and include surrounding context lines.",
        arguments=(
            CommandArgument("-B 2", "Show two lines before each match", "Provides pre-error context."),
            CommandArgument("-A 2", "Show two lines after each match", "Provides post-error context."),
        ),
        incident_types=("LogInvestigation", "ConfigSearch", "ErrorPatternSearch"),
        related_commands=("grep -r <pattern> <directory>", "zgrep <pattern> <file.gz>", "fgrep -R <literal> <directory>"),
        agent_hint="Use for bounded log/config searches where surrounding context matters.",
        source_notes=("GitLab Linux cheat sheet documents grep -B/-A context search and recursive grep patterns.",),
    ),
    CommandVariant(
        key="linux.search.grep_recursive",
        base_command="grep",
        variant="grep -r <pattern> <directory>",
        category="search",
        description="Recursively search files below a directory.",
        arguments=(
            CommandArgument("-r", "Recursive search", "Finds matching content across nested application or config directories.", "careful"),
        ),
        incident_types=("ConfigSearch", "SecretReferenceSearch", "DependencySearch"),
        related_commands=("find <directory> -type f -name '<pattern>'", "rg <pattern> <directory>"),
        risk="careful",
        agent_hint="Bound the directory path; avoid recursive searches from / on large production systems.",
    ),
    CommandVariant(
        key="linux.disk.df_hT",
        base_command="df",
        variant="df -hT",
        category="disk",
        description="Show filesystem capacity using human-readable units and filesystem type.",
        arguments=(
            CommandArgument("-h", "Human-readable units", "Makes disk capacity easier to interpret."),
            CommandArgument("-T", "Show filesystem type", "Separates ext4/xfs/tmpfs/nfs/container overlay issues."),
        ),
        incident_types=("DiskFull", "KubernetesDiskPressure", "FilesystemCapacity"),
        related_commands=("df -i", "du -xhd1 /", "findmnt -r", "lsof +L1"),
        agent_hint="First-line disk capacity check before recommending cleanup.",
        source_notes=("GitLab Linux cheat sheet includes df -h for human-readable disk usage.",),
    ),
    CommandVariant(
        key="linux.disk.du_xhd1_root",
        base_command="du",
        variant="du -xhd1 /",
        category="disk",
        description="Show one-level directory usage on the root filesystem only.",
        arguments=(
            CommandArgument("-x", "Stay on one filesystem", "Avoids crossing into mounted volumes, pseudo-filesystems, or network mounts."),
            CommandArgument("-h", "Human-readable units", "Makes large directories easier to compare."),
            CommandArgument("-d1", "Depth one", "Keeps scan bounded and fast enough for incident use."),
        ),
        incident_types=("DiskFull", "KubernetesDiskPressure", "LargeFileGrowth"),
        related_commands=("df -hT", "df -i", "find / -xdev -type f -size +500M", "lsof +L1"),
        risk="careful",
        agent_hint="Use only after df confirms capacity pressure; keep path bounded.",
        source_notes=("GitLab Linux cheat sheet includes du -hd 1 and du -h --max-depth=1.",),
    ),
    CommandVariant(
        key="linux.disk.find_large_files",
        base_command="find",
        variant="find / -xdev -type f -size +100M -print0 | xargs -0 du -hs | sort -h",
        category="disk",
        description="Find large files on one filesystem and sort them by size.",
        arguments=(
            CommandArgument("-xdev", "Stay on the same filesystem", "Avoids scanning attached or virtual filesystems."),
            CommandArgument("-type f", "Only regular files", "Avoids directories and special files."),
            CommandArgument("-size +100M", "Files larger than 100 MiB", "Targets likely disk consumers."),
            CommandArgument("-print0", "NUL-delimited output", "Safely handles spaces and unusual filenames."),
            CommandArgument("sort -h", "Human numeric sort", "Ranks results by readable size."),
        ),
        incident_types=("DiskFull", "LargeFileGrowth"),
        related_commands=("du -xhd1 /", "lsof +L1", "journalctl --disk-usage"),
        risk="careful",
        agent_hint="Use with bounded filesystems; avoid automatic deletion recommendations.",
        source_notes=("GitLab Linux cheat sheet includes find / -type f -size +100M ... sort -h pattern.",),
    ),
    CommandVariant(
        key="linux.memory.free_m",
        base_command="free",
        variant="free -m",
        category="memory",
        description="Show memory and swap usage in MiB.",
        arguments=(
            CommandArgument("-m", "Show values in MiB", "Makes memory usage simple for quick incident triage."),
        ),
        incident_types=("MemoryPressure", "OOMKilled", "SwapPressure"),
        related_commands=("cat /proc/meminfo", "vmstat 1 5", "ps aux --sort=-%mem"),
        agent_hint="Use before deeper memory pressure or OOM analysis.",
        source_notes=("GitLab Linux cheat sheet includes free -m for finding free memory.",),
    ),
    CommandVariant(
        key="linux.process.ps_aux_memory",
        base_command="ps",
        variant="ps aux --sort=-%mem | head",
        category="process",
        description="Show top memory-consuming processes.",
        arguments=(
            CommandArgument("aux", "BSD-style all process listing", "Shows processes across users with CPU/memory and command."),
            CommandArgument("--sort=-%mem", "Sort by memory descending", "Highlights likely memory consumers."),
        ),
        incident_types=("MemoryPressure", "OOMKilled", "ProcessLeak"),
        related_commands=("top -o %MEM", "pmap -x <pid>", "cat /proc/<pid>/status"),
        agent_hint="Use to identify top process consumers before recommending restart/escalation.",
    ),
    CommandVariant(
        key="linux.process.strace_timing",
        base_command="strace",
        variant="strace -tt -T -f -y -yy -s 1024 -p <pid>",
        category="process",
        description="Trace a process with timestamps, syscall durations, child processes, and file/socket context.",
        arguments=(
            CommandArgument("-tt", "Microsecond timestamps", "Correlates syscalls with incident timeline."),
            CommandArgument("-T", "Show syscall duration", "Finds slow system calls."),
            CommandArgument("-f", "Follow child processes", "Captures forked worker behavior."),
            CommandArgument("-y", "Show file descriptor paths", "Maps file descriptors to paths."),
            CommandArgument("-yy", "Show more fd/socket details", "Improves network and device context."),
            CommandArgument("-s 1024", "Increase string capture length", "Preserves useful payload/path snippets."),
            CommandArgument("-p <pid>", "Attach to PID", "Targets one process instead of tracing the whole system."),
        ),
        incident_types=("LatencyInvestigation", "HungProcess", "FilesystemLatency", "SocketTimeout"),
        related_commands=("pidstat -p <pid> 1 5", "lsof -p <pid>", "perf top -p <pid>"),
        risk="elevated",
        requires_root=True,
        agent_hint="High-value but high-risk. Warn about overhead and keep duration bounded.",
        source_notes=("GitLab Linux cheat sheet warns strace can have major system performance impact.",),
    ),
    CommandVariant(
        key="linux.network.ss_plnt",
        base_command="ss",
        variant="ss -plnt",
        category="network",
        description="Show listening TCP sockets and owning processes.",
        arguments=(
            CommandArgument("-p", "Show process using socket", "Maps a port to a service/process when permissions allow."),
            CommandArgument("-l", "Listening sockets", "Filters to server-side listeners."),
            CommandArgument("-n", "Numeric addresses/ports", "Avoids DNS/service-name lookup delays."),
            CommandArgument("-t", "TCP only", "Focuses on TCP service listeners."),
        ),
        incident_types=("PortConflict", "ServiceUnavailable", "LocalListenerMissing"),
        related_commands=("netstat -plnt", "lsof -i -P | grep <port>", "systemctl status <service>"),
        agent_hint="Use when an application should be listening but clients cannot connect.",
        source_notes=("GitLab Linux cheat sheet lists netstat -plnt, ss -plnt, and lsof -i -P for port checks.",),
    ),
    CommandVariant(
        key="linux.network.dig_specific_resolver",
        base_command="dig",
        variant="dig @8.8.8.8 example.com",
        category="network",
        description="Resolve a domain using a specific DNS resolver.",
        arguments=(
            CommandArgument("@<server>", "Query a specific resolver", "Separates local resolver issues from authoritative/public DNS behavior."),
        ),
        incident_types=("DNSFailure", "ServiceDiscoveryFailure", "ExternalConnectivity"),
        related_commands=("dig +short example.com", "nslookup example.com 1.1.1.1", "cat /etc/resolv.conf"),
        agent_hint="Compare local resolver and public resolver answers before blaming application DNS.",
        source_notes=("GitLab Linux cheat sheet includes dig +short and dig @8.8.8.8 examples.",),
    ),
    CommandVariant(
        key="linux.network.curl_head_location",
        base_command="curl",
        variant="curl --head --location https://example.com",
        category="network",
        description="Fetch response headers while following redirects.",
        arguments=(
            CommandArgument("--head", "Fetch headers only", "Checks status, redirects, cache/proxy headers without downloading body."),
            CommandArgument("--location", "Follow redirects", "Shows final response path for HTTP routing issues."),
        ),
        incident_types=("HTTPFailure", "ProxyIssue", "IngressRouting", "TLSOrRedirectIssue"),
        related_commands=("curl -vk https://example.com", "openssl s_client -connect host:443 -servername host"),
        agent_hint="Use before packet capture to verify HTTP status and redirect behavior.",
        source_notes=("GitLab Linux cheat sheet includes curl --head --location for headers and redirects.",),
    ),
    CommandVariant(
        key="linux.network.tcpdump_host",
        base_command="tcpdump",
        variant="sudo tcpdump host <host>",
        category="network",
        description="Capture packets to or from a host.",
        arguments=(
            CommandArgument("host <host>", "Host filter", "Bounds packet capture to one target host."),
        ),
        incident_types=("NetworkTimeout", "PacketLoss", "DNSFailure", "TLSHandshakeFailure"),
        related_commands=("mtr <host>", "ss -tanp", "ip route get <host>"),
        risk="elevated",
        requires_root=True,
        agent_hint="Use only with strict filters and short capture windows.",
        source_notes=("GitLab Linux cheat sheet includes sudo tcpdump host www.example.com.",),
    ),
    CommandVariant(
        key="linux.logs.tail_n",
        base_command="tail",
        variant="tail -n 100 /path/to/log/file",
        category="logs",
        description="Read the last N lines of a log file.",
        arguments=(
            CommandArgument("-n 100", "Number of lines", "Keeps log evidence bounded for analysis."),
        ),
        incident_types=("LogInvestigation", "ServiceFailure", "StartupFailure"),
        related_commands=("journalctl -u <service> -n 100 --no-pager", "grep -B 2 -A 2 <pattern> <file>"),
        agent_hint="Prefer bounded log reads over dumping entire files.",
        source_notes=("GitLab Linux cheat sheet includes tail -n /path/to/log/file.",),
    ),
)


def list_argument_aware_commands(category: str | None = None) -> list[dict]:
    """
    Return Linux command variants with flag-level troubleshooting explanations.
    """

    return [
        command.to_dict()
        for command in LINUX_ARGUMENT_AWARE_COMMANDS
        if category is None or command.category == category
    ]


def get_argument_aware_command(key: str) -> dict | None:
    """
    Return one command variant by key.
    """

    for command in LINUX_ARGUMENT_AWARE_COMMANDS:
        if command.key == key:
            return command.to_dict()
    return None
