"""Console messaging helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Optional

from rich.console import Console


console = Console()


@dataclass
class Message:
    """Structured CLI message."""

    status: str
    title: str
    detail: Optional[str] = None
    next_step: Optional[str] = None
    data: Optional[dict[str, Any]] = None


def emit(message: Message, *, as_json: bool = False) -> None:
    """Render a message for CLI output."""

    if as_json:
        console.print_json(json.dumps(asdict(message)))
        return

    style = {
        "ok": "green",
        "warn": "yellow",
        "error": "red",
        "info": "cyan",
    }.get(message.status, "white")
    console.print(f"[{style}]{message.title}[/{style}]")
    if message.detail:
        console.print(message.detail)
    if message.next_step:
        console.print(f"Next: {message.next_step}")
    if message.data:
        for key, value in message.data.items():
            console.print(f"- {key}: {value}")
