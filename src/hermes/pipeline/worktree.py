"""Worktree lifecycle helpers."""

from __future__ import annotations

import re
from pathlib import Path

from hermes.subprocess_utils import run_command


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "task"


def render_branch_name(template: str, issue_number: int, title: str) -> str:
    return template.format(issue_number=issue_number, slug=slugify(title))


def ensure_worktree(repo_path: Path, worktree_root: Path, branch_name: str, title: str) -> Path:
    worktree_root.mkdir(parents=True, exist_ok=True)
    worktree_path = worktree_root / f"{branch_name}-{slugify(title)}"
    if not worktree_path.exists():
        run_command(["git", "-C", str(repo_path), "fetch", "origin"])
        run_command(
            [
                "git",
                "-C",
                str(repo_path),
                "worktree",
                "add",
                "-b",
                branch_name,
                str(worktree_path),
                "origin/main",
            ]
        )
    return worktree_path

