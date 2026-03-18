"""Doctor and preflight checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hermes.config.models import ConfigBundle
from hermes.github.client import GitHubClient
from hermes.subprocess_utils import ensure_tools_exist, run_command


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def basic_environment_checks(bundle: ConfigBundle) -> list[CheckResult]:
    results: list[CheckResult] = []
    required_tools = ["git", "gh", "python3", "sqlite3", "launchctl"]
    missing = ensure_tools_exist(required_tools)
    results.append(
        CheckResult(
            name="required-tools",
            ok=not missing,
            detail="all required tools available" if not missing else f"missing: {', '.join(missing)}",
        )
    )

    results.append(
        CheckResult(
            name="workspace-root",
            ok=bundle.hermes.workspace_root.exists(),
            detail=str(bundle.hermes.workspace_root),
        )
    )
    for repo in bundle.repos.repos:
        results.append(
            CheckResult(
                name=f"repo:{repo.key}",
                ok=repo.path.exists(),
                detail=str(repo.path),
            )
        )
    results.append(
        CheckResult(
            name="state-db-parent",
            ok=bundle.hermes.runtime.state_db_path.parent.exists() or bundle.hermes.runtime.state_db_path.parent.parent.exists(),
            detail=str(bundle.hermes.runtime.state_db_path),
        )
    )
    return results


def github_checks(bundle: ConfigBundle, github: GitHubClient) -> list[CheckResult]:
    results: list[CheckResult] = []
    auth = github.auth_status()
    results.append(CheckResult(name="gh-auth", ok="Logged in to" in auth, detail=auth.splitlines()[0] if auth else "unknown"))
    project = github.view_project()
    results.append(
        CheckResult(
            name="project-view",
            ok=bool(project.get("id")),
            detail=project.get("url", "missing project url"),
        )
    )
    field_names = {field.name for field in github.get_project_fields()}
    results.append(
        CheckResult(
            name="project-status-field",
            ok="Status" in field_names,
            detail=f"fields: {', '.join(sorted(field_names))}",
        )
    )
    return results


def command_checks(bundle: ConfigBundle) -> list[CheckResult]:
    results: list[CheckResult] = []
    for repo in bundle.repos.repos:
        if not repo.validation_commands:
            continue
        results.append(
            CheckResult(
                name=f"validation-command:{repo.key}",
                ok=True,
                detail=repo.validation_commands[0],
            )
        )
    return results

