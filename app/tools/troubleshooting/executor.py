from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import asdict, dataclass

from app.tools.troubleshooting.catalog import TroubleshootingCommand


DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_OUTPUT_LIMIT = 80_000


@dataclass
class TroubleshootingCommandResult:
    key: str
    command: str
    status: str
    output: str = ""
    error: str = ""
    exit_code: int | None = None
    skipped: bool = False
    reason: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class SafeTroubleshootingExecutor:
    """
    Execute one catalog command through a bounded, shell-free read path.

    AOP's catalog is mostly planner knowledge. Execution stays opt-in and
    refuses commands that need placeholders, root access, or wider scans unless
    the caller explicitly allows that class of read-only evidence.
    """

    def __init__(
        self,
        *,
        allow_elevated_reads: bool = False,
        allow_careful_reads: bool = False,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        output_limit: int = DEFAULT_OUTPUT_LIMIT,
    ) -> None:
        self.allow_elevated_reads = allow_elevated_reads
        self.allow_careful_reads = allow_careful_reads
        self.timeout_seconds = timeout_seconds
        self.output_limit = output_limit

    def _skip_reason(self, command: TroubleshootingCommand) -> str | None:
        if "<" in command.command or ">" in command.command:
            return "command contains placeholders and needs incident context"
        if command.requires_root and os.geteuid() != 0 and not self.allow_elevated_reads:
            return "requires root or explicit elevated-read allowance"
        if command.risk == "careful" and not self.allow_careful_reads:
            return "careful command requires explicit allowance"

        argv = shlex.split(command.command)
        if not argv:
            return "empty command"
        if shutil.which(argv[0]) is None:
            return f"executable not found: {argv[0]}"
        return None

    def execute(self, command: TroubleshootingCommand) -> TroubleshootingCommandResult:
        reason = self._skip_reason(command)
        if reason is not None:
            return TroubleshootingCommandResult(
                key=command.key,
                command=command.command,
                status="skipped",
                skipped=True,
                reason=reason,
            )

        argv = shlex.split(command.command)
        executable = shutil.which(argv[0])
        assert executable is not None

        try:
            completed = subprocess.run(
                [executable, *argv[1:]],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
                env={
                    **os.environ,
                    "LC_ALL": "C",
                    "LANG": "C",
                },
            )
        except subprocess.TimeoutExpired as exc:
            return TroubleshootingCommandResult(
                key=command.key,
                command=command.command,
                status="timeout",
                output=(exc.stdout or "")[: self.output_limit],
                error=f"command exceeded {self.timeout_seconds} seconds",
                skipped=True,
                reason="timeout",
            )
        except OSError as exc:
            return TroubleshootingCommandResult(
                key=command.key,
                command=command.command,
                status="error",
                error=str(exc),
            )

        return TroubleshootingCommandResult(
            key=command.key,
            command=command.command,
            status="ok" if completed.returncode == 0 else "error",
            output=completed.stdout[: self.output_limit].rstrip(),
            error=completed.stderr[: self.output_limit].rstrip(),
            exit_code=completed.returncode,
        )
