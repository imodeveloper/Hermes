"""Subprocess helpers for Hermes."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from .errors import CommandError


@dataclass
class CommandResult:
    """Normalized subprocess result."""

    args: Sequence[str]
    stdout: str
    stderr: str
    returncode: int


def shell_join(args: Sequence[str]) -> str:
    """Return a safe shell representation of args."""

    return " ".join(shlex.quote(arg) for arg in args)


def run_command(
    args: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    check: bool = True,
) -> CommandResult:
    """Run a subprocess and return a normalized result."""

    completed = subprocess.run(
        list(args),
        cwd=str(cwd) if cwd else None,
        env=dict(env) if env else None,
        capture_output=True,
        text=True,
    )
    result = CommandResult(
        args=args,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
        returncode=completed.returncode,
    )
    if check and completed.returncode != 0:
        raise CommandError(
            f"Command failed: {shell_join(args)}",
            command=shell_join(args),
            exit_code=completed.returncode,
            stderr=result.stderr,
        )
    return result


def ensure_tools_exist(tools: Iterable[str]) -> list[str]:
    """Return a list of missing tools."""

    missing: list[str] = []
    for tool in tools:
        try:
            run_command(["/usr/bin/env", "which", tool], check=True)
        except CommandError:
            missing.append(tool)
    return missing
