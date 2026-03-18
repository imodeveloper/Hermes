"""Heartbeat helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from typing import Optional


def format_heartbeat(*, stage: str, action: str, blocker: Optional[str] = None) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    body = f"[hermes-heartbeat] stage={stage} action={action} at={timestamp}"
    if blocker:
        body += f" blocker={blocker}"
    return body
