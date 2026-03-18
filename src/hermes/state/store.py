"""SQLite state store for Hermes runtime state."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from hermes.errors import LockError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ClaimRecord:
    item_id: str
    repo_key: str
    stage: str
    status: str
    branch_name: Optional[str]
    worktree_path: Optional[str]
    pr_number: Optional[int]
    last_heartbeat_at: Optional[str]


class StateStore:
    """Hermes runtime state store."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS scheduler_locks (
                    name TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    acquired_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS item_claims (
                    item_id TEXT PRIMARY KEY,
                    repo_key TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    branch_name TEXT,
                    worktree_path TEXT,
                    pr_number INTEGER,
                    last_heartbeat_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS project_snapshots (
                    project_key TEXT PRIMARY KEY,
                    snapshot_hash TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def acquire_lock(self, name: str, owner: str) -> None:
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT owner FROM scheduler_locks WHERE name = ?",
                (name,),
            ).fetchone()
            if existing:
                raise LockError(f"Lock already held for {name} by {existing['owner']}")
            conn.execute(
                "INSERT INTO scheduler_locks (name, owner, acquired_at) VALUES (?, ?, ?)",
                (name, owner, utc_now()),
            )

    def release_lock(self, name: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM scheduler_locks WHERE name = ?", (name,))

    def upsert_claim(
        self,
        *,
        item_id: str,
        repo_key: str,
        stage: str,
        status: str,
        branch_name: Optional[str] = None,
        worktree_path: Optional[str] = None,
        pr_number: Optional[int] = None,
    ) -> None:
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO item_claims (
                    item_id, repo_key, stage, status, branch_name, worktree_path,
                    pr_number, last_heartbeat_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    repo_key = excluded.repo_key,
                    stage = excluded.stage,
                    status = excluded.status,
                    branch_name = excluded.branch_name,
                    worktree_path = excluded.worktree_path,
                    pr_number = excluded.pr_number,
                    updated_at = excluded.updated_at
                """,
                (
                    item_id,
                    repo_key,
                    stage,
                    status,
                    branch_name,
                    worktree_path,
                    pr_number,
                    now,
                    now,
                    now,
                ),
            )

    def delete_claim(self, item_id: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM item_claims WHERE item_id = ?", (item_id,))

    def record_heartbeat(self, item_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE item_claims SET last_heartbeat_at = ?, updated_at = ? WHERE item_id = ?",
                (utc_now(), utc_now(), item_id),
            )

    def list_claims(self) -> list[ClaimRecord]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT item_id, repo_key, stage, status, branch_name, worktree_path,
                       pr_number, last_heartbeat_at
                FROM item_claims
                ORDER BY item_id
                """
            ).fetchall()
        return [ClaimRecord(**dict(row)) for row in rows]

    def count_active_for_repo(self, repo_key: str, *, stages: tuple[str, ...] = ("execute", "review")) -> int:
        placeholders = ",".join("?" for _ in stages)
        with self.connect() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) AS count FROM item_claims WHERE repo_key = ? AND stage IN ({placeholders})",
                (repo_key, *stages),
            ).fetchone()
            return int(row["count"])

    def get_claim(self, item_id: str) -> Optional[ClaimRecord]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT item_id, repo_key, stage, status, branch_name, worktree_path,
                       pr_number, last_heartbeat_at
                FROM item_claims
                WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()
        return ClaimRecord(**dict(row)) if row else None

    def get_snapshot_hash(self, project_key: str) -> Optional[str]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT snapshot_hash FROM project_snapshots WHERE project_key = ?",
                (project_key,),
            ).fetchone()
        return str(row["snapshot_hash"]) if row else None

    def update_snapshot_hash(self, project_key: str, snapshot_hash: str) -> None:
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO project_snapshots (project_key, snapshot_hash, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(project_key) DO UPDATE SET
                    snapshot_hash = excluded.snapshot_hash,
                    updated_at = excluded.updated_at
                """,
                (project_key, snapshot_hash, now),
            )
