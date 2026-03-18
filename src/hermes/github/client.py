"""GitHub CLI-backed integration for Hermes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, List, Optional, Union

from hermes.config.models import ConfigBundle
from hermes.subprocess_utils import run_command

from .models import IssueContent, ProjectField, ProjectFieldOption, ProjectItem


class GitHubClient:
    """Minimal GitHub CLI wrapper."""

    def __init__(self, bundle: ConfigBundle) -> None:
        self.bundle = bundle
        self.owner = bundle.hermes.project.owner
        self.project_number = bundle.hermes.project.number

    def auth_status(self) -> str:
        return run_command(["gh", "auth", "status"]).stdout

    def repo_default_branch(self, repo: str) -> str:
        payload = self._json(["gh", "repo", "view", repo, "--json", "defaultBranchRef"])
        return payload["defaultBranchRef"]["name"]

    def list_project_items(self) -> list[ProjectItem]:
        payload = self._json(
            [
                "gh",
                "project",
                "item-list",
                str(self.project_number),
                "--owner",
                self.owner,
                "--format",
                "json",
            ]
        )
        items: list[ProjectItem] = []
        for item in payload.get("items", []):
            content = item.get("content")
            issue_content = None
            if content:
                issue_content = IssueContent(
                    number=content["number"],
                    title=content["title"],
                    body=content.get("body", ""),
                    repository=content.get("repository", ""),
                    url=content["url"],
                    type=content["type"],
                )
            items.append(
                ProjectItem(
                    id=item["id"],
                    title=item["title"],
                    status=item.get("status", ""),
                    repository=item.get("repository"),
                    labels=item.get("labels", []),
                    assignees=item.get("assignees", []),
                    content=issue_content,
                )
            )
        return items

    def compute_snapshot_hash(self, items: list[ProjectItem]) -> str:
        payload = [
            {
                "id": item.id,
                "status": item.status,
                "title": item.title,
                "labels": item.labels,
                "repository": item.repository,
                "content_number": item.content.number if item.content else None,
            }
            for item in items
        ]
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def get_project_fields(self) -> list[ProjectField]:
        payload = self._json(
            [
                "gh",
                "project",
                "field-list",
                str(self.project_number),
                "--owner",
                self.owner,
                "--format",
                "json",
            ]
        )
        fields: list[ProjectField] = []
        for field in payload.get("fields", []):
            options = [
                ProjectFieldOption(id=option["id"], name=option["name"])
                for option in field.get("options", [])
            ]
            fields.append(
                ProjectField(
                    id=field["id"],
                    name=field["name"],
                    type=field["type"],
                    options=options,
                )
            )
        return fields

    def view_project(self) -> dict[str, Any]:
        return self._json(
            [
                "gh",
                "project",
                "view",
                str(self.project_number),
                "--owner",
                self.owner,
                "--format",
                "json",
            ]
        )

    def comment_issue(self, repo: str, issue_number: int, body: str) -> None:
        run_command(
            ["gh", "issue", "comment", str(issue_number), "-R", repo, "--body", body],
            check=True,
        )

    def close_issue(self, repo: str, issue_number: int) -> None:
        run_command(["gh", "issue", "close", str(issue_number), "-R", repo], check=True)

    def create_issue(self, repo: str, title: str, body: str, labels: Optional[List[str]] = None) -> str:
        args = ["gh", "issue", "create", "-R", repo, "--title", title, "--body", body]
        for label in labels or []:
            args.extend(["--label", label])
        return run_command(args).stdout

    def ensure_label(self, repo: str, name: str, color: str = "1D76DB", description: str = "Created by Hermes") -> None:
        run_command(
            ["gh", "label", "create", name, "-R", repo, "--color", color, "--description", description],
            check=False,
        )

    def add_labels(self, repo: str, issue_number: int, labels: list[str]) -> None:
        args = ["gh", "issue", "edit", str(issue_number), "-R", repo]
        for label in labels:
            args.extend(["--add-label", label])
        run_command(args)

    def remove_label(self, repo: str, issue_number: int, label: str) -> None:
        run_command(
            ["gh", "issue", "edit", str(issue_number), "-R", repo, "--remove-label", label],
            check=False,
        )

    def create_pr(self, repo: str, base: str, head: str, title: str, body: str) -> str:
        return run_command(
            ["gh", "pr", "create", "-R", repo, "--base", base, "--head", head, "--title", title, "--body", body]
        ).stdout

    def list_prs(self, repo: str, state: str = "open") -> list[dict[str, Any]]:
        return self._json(
            [
                "gh",
                "pr",
                "list",
                "-R",
                repo,
                "--state",
                state,
                "--limit",
                "100",
                "--json",
                "number,title,state,headRefName,baseRefName,url,isDraft,reviews",
            ]
        )

    def review_pr(self, repo: str, pr_number: int, *, approve: bool, body: str) -> None:
        event = "APPROVE" if approve else "REQUEST_CHANGES"
        run_command(
            ["gh", "pr", "review", str(pr_number), "-R", repo, "--body", body, f"--{event.lower().replace('_', '-')}"],
        )

    def merge_pr(self, repo: str, pr_number: int, method: str = "squash") -> None:
        flag = {"squash": "--squash", "merge": "--merge", "rebase": "--rebase"}.get(method, "--squash")
        run_command(["gh", "pr", "merge", str(pr_number), "-R", repo, flag, "--delete-branch"])

    def item_edit_status(self, item_id: str, project_id: str, field_id: str, option_id: str) -> None:
        run_command(
            [
                "gh",
                "project",
                "item-edit",
                "--id",
                item_id,
                "--project-id",
                project_id,
                "--field-id",
                field_id,
                "--single-select-option-id",
                option_id,
            ]
        )

    def _json(self, args: list[str]) -> Union[dict[str, Any], list[dict[str, Any]]]:
        result = run_command(args)
        return json.loads(result.stdout or "{}")
