"""CLI entrypoint for Hermes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from hermes.config.loader import init_config_from_examples, load_bundle, personalize_init_files
from hermes.doctor.checks import basic_environment_checks, command_checks, github_checks
from hermes.errors import ConfigError, HermesError, LockError
from hermes.github.client import GitHubClient
from hermes.launchd_support import plist_contents
from hermes.logging.console import Message, console, emit
from hermes.pipeline.engine import (
    PipelineContext,
    execute_ready,
    project_key,
    reap_stale,
    release_done,
    review_in_review,
    transition_to_review,
    triage_backlog,
)
from hermes.sandbox.flow import create_sandbox_issue
from hermes.state.store import StateStore


app = typer.Typer(help="Hermes local orchestrator CLI.")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_config_dir() -> Path:
    return _project_root() / "config" / "examples"


def _bundle_from_dir(config_dir: Path, *, initialize_state: bool = True) -> PipelineContext:
    bundle = load_bundle(config_dir)
    state = StateStore(bundle.hermes.runtime.state_db_path)
    if initialize_state:
        state.initialize()
    github = GitHubClient(bundle)
    return PipelineContext(bundle=bundle, github=github, state=state)


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, ConfigError):
        emit(Message(status="error", title="Configuration error", detail=str(exc), next_step="Review your config files."))
    elif isinstance(exc, LockError):
        emit(Message(status="warn", title="Scheduler lock unavailable", detail=str(exc), next_step="Retry after the active run finishes."))
    elif isinstance(exc, HermesError):
        emit(Message(status="error", title="Hermes failed", detail=str(exc)))
    else:
        emit(Message(status="error", title="Unexpected failure", detail=str(exc)))
    raise typer.Exit(code=1)


def main() -> None:
    app()


@app.command()
def version() -> None:
    """Show the current Hermes version."""

    typer.echo("Hermes 0.1.0")


@app.command("show-config")
def show_config(config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True)) -> None:
    """Print the loaded config summary."""

    try:
        ctx = _bundle_from_dir(config_dir, initialize_state=False)
    except Exception as exc:  # pragma: no cover - thin error adapter
        _handle_error(exc)
    emit(Message(status="ok", title="Loaded config", data=ctx.bundle.as_public_dict()))


@app.command()
def init(
    destination_dir: Path = typer.Option(Path("./.hermes"), file_okay=False, dir_okay=True),
    workspace_root: Path = typer.Option(Path.home() / "Work", file_okay=False, dir_okay=True),
    state_root: Path = typer.Option(Path.home() / ".local" / "share" / "hermes", file_okay=False, dir_okay=True),
    project_owner: str = typer.Option("imodeveloper"),
    project_number: int = typer.Option(1),
    force: bool = typer.Option(False, help="Overwrite local helper files if needed."),
) -> None:
    """Copy example configs into a local destination directory."""

    try:
        written = init_config_from_examples(project_root=_project_root(), destination_dir=destination_dir)
        personalize_init_files(
            destination_dir=destination_dir,
            workspace_root=workspace_root,
            state_root=state_root,
            project_owner=project_owner,
            project_number=project_number,
        )
        local_override = destination_dir / ".hermes.local.yaml"
        if force or not local_override.exists():
            local_override.write_text("# Optional machine-specific overrides for Hermes.\n")
        emit(
            Message(
                status="ok",
                title="Initialized Hermes config",
                detail=f"Wrote {len(written)} example files to {destination_dir}",
                next_step=f"Review {destination_dir} and run `hermes doctor --config-dir {destination_dir}`",
            )
        )
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command()
def doctor(config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True)) -> None:
    """Run doctor checks."""

    try:
        ctx = _bundle_from_dir(config_dir)
        results = basic_environment_checks(ctx.bundle) + github_checks(ctx.bundle, ctx.github) + command_checks(ctx.bundle)
        table = Table(title="Hermes Doctor")
        table.add_column("Check")
        table.add_column("OK")
        table.add_column("Detail")
        failed = False
        for result in results:
            table.add_row(result.name, "yes" if result.ok else "no", result.detail)
            failed = failed or not result.ok
        console.print(table)
        if failed:
            raise typer.Exit(code=1)
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command()
def preflight(config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True)) -> None:
    """Run non-mutating checks required before scheduler work."""

    doctor(config_dir=config_dir)


@app.command("state-inspect")
def state_inspect(config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True)) -> None:
    """Print current runtime state."""

    try:
        ctx = _bundle_from_dir(config_dir)
        payload = [
            {
                "item_id": claim.item_id,
                "repo_key": claim.repo_key,
                "stage": claim.stage,
                "status": claim.status,
                "branch_name": claim.branch_name,
                "worktree_path": claim.worktree_path,
                "pr_number": claim.pr_number,
                "last_heartbeat_at": claim.last_heartbeat_at,
            }
            for claim in ctx.state.list_claims()
        ]
        console.print_json(json.dumps(payload))
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("poll-triage")
def poll_triage(
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
    dry_run: bool = typer.Option(False),
) -> None:
    """Process backlog items."""

    try:
        ctx = _bundle_from_dir(config_dir)
        for line in triage_backlog(ctx, dry_run=dry_run):
            console.print(line)
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("poll-execute")
def poll_execute(
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
    dry_run: bool = typer.Option(False),
) -> None:
    """Claim ready items for execution."""

    try:
        ctx = _bundle_from_dir(config_dir)
        for line in execute_ready(ctx, dry_run=dry_run):
            console.print(line)
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("poll-review")
def poll_review(
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
    approve: bool = typer.Option(False, help="Approve reviewed items instead of rejecting them."),
    dry_run: bool = typer.Option(False),
) -> None:
    """Process in-review items."""

    try:
        ctx = _bundle_from_dir(config_dir)
        for line in review_in_review(ctx, approve=approve, dry_run=dry_run):
            console.print(line)
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("poll-release")
def poll_release(
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
    dry_run: bool = typer.Option(False),
) -> None:
    """List or process release-ready items."""

    try:
        ctx = _bundle_from_dir(config_dir)
        for line in release_done(ctx, dry_run=dry_run):
            console.print(line)
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("reap-stale")
def stale_reaper(
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
    dry_run: bool = typer.Option(False),
) -> None:
    """Detect and recover stale claims."""

    try:
        ctx = _bundle_from_dir(config_dir)
        for line in reap_stale(ctx, dry_run=dry_run):
            console.print(line)
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("poll-all")
def poll_all(
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
    dry_run: bool = typer.Option(False),
) -> None:
    """Run the full scheduler cycle."""

    try:
        ctx = _bundle_from_dir(config_dir)
        owner = f"{os.uname().nodename}:{os.getpid()}"
        ctx.state.acquire_lock("scheduler", owner)
        try:
            for line in triage_backlog(ctx, dry_run=dry_run):
                console.print(line)
            for line in execute_ready(ctx, dry_run=dry_run):
                console.print(line)
            for line in review_in_review(ctx, approve=False, dry_run=dry_run):
                console.print(line)
            for line in release_done(ctx, dry_run=dry_run):
                console.print(line)
            for line in reap_stale(ctx, dry_run=dry_run):
                console.print(line)
        finally:
            ctx.state.release_lock("scheduler")
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("transition-to-review")
def cmd_transition_to_review(
    item_id: str = typer.Argument(...),
    repo_key: str = typer.Option(...),
    pr_title: str = typer.Option(...),
    pr_body: str = typer.Option(...),
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
    dry_run: bool = typer.Option(False),
) -> None:
    """Move a claimed item into review by opening/updating a PR."""

    try:
        ctx = _bundle_from_dir(config_dir)
        console.print(
            transition_to_review(ctx, repo_key=repo_key, item_id=item_id, pr_title=pr_title, pr_body=pr_body, dry_run=dry_run)
        )
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("sandbox-create-ticket")
def sandbox_create_ticket(
    repo: str = typer.Option(..., help="Repository in OWNER/REPO format."),
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
) -> None:
    """Create a sandbox ticket."""

    try:
        ctx = _bundle_from_dir(config_dir)
        issue_url = create_sandbox_issue(ctx.bundle, ctx.github, repo)
        ctx.github.add_issue_to_project(issue_url)
        console.print(issue_url)
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("sandbox-run-e2e")
def sandbox_run_e2e(
    repo: str = typer.Option(..., help="Repository in OWNER/REPO format."),
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
) -> None:
    """Run a lightweight sandbox bootstrap."""

    try:
        ctx = _bundle_from_dir(config_dir)
        issue_url = create_sandbox_issue(ctx.bundle, ctx.github, repo)
        ctx.github.add_issue_to_project(issue_url)
        emit(
            Message(
                status="ok",
                title="Sandbox ticket created",
                detail=f"{issue_url}\nAdded to configured project.",
                next_step="Move the sandbox item through Backlog -> Ready to exercise the pipeline commands.",
            )
        )
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)


@app.command("scheduler-install")
def scheduler_install(
    config_dir: Path = typer.Option(_default_config_dir(), exists=True, file_okay=False, dir_okay=True),
    destination: Path = typer.Option(Path.home() / "Library/LaunchAgents/com.imodeveloper.hermes.plist"),
) -> None:
    """Generate a launchd plist for Hermes."""

    try:
        ctx = _bundle_from_dir(config_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            plist_contents(
                project_root=_project_root(),
                interval_seconds=ctx.bundle.hermes.scheduler.interval_seconds,
                config_dir=config_dir,
            )
        )
        emit(
            Message(
                status="ok",
                title="launchd plist written",
                detail=str(destination),
                next_step=f"Run `launchctl load {destination}` to enable the scheduler.",
            )
        )
    except Exception as exc:  # pragma: no cover
        _handle_error(exc)
