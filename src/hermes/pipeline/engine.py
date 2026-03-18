"""Pipeline operations for Hermes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from hermes.config.models import ConfigBundle, RepoConfig
from hermes.github.client import GitHubClient
from hermes.github.models import ProjectField, ProjectItem
from hermes.model_routing import route_for_task
from hermes.subprocess_utils import run_shell
from hermes.state.store import ClaimRecord, StateStore

from .heartbeats import format_heartbeat
from .worktree import ensure_worktree, render_branch_name


@dataclass
class PipelineContext:
    bundle: ConfigBundle
    github: GitHubClient
    state: StateStore


def project_key(bundle: ConfigBundle) -> str:
    return f"{bundle.hermes.project.owner}/{bundle.hermes.project.number}"


def should_skip_poll(ctx: PipelineContext, items: list[ProjectItem]) -> bool:
    if not ctx.bundle.hermes.github.no_op_fast_path:
        return False
    new_hash = ctx.github.compute_snapshot_hash(items)
    old_hash = ctx.state.get_snapshot_hash(project_key(ctx.bundle))
    ctx.state.update_snapshot_hash(project_key(ctx.bundle), new_hash)
    return old_hash == new_hash


def route_repo_for_item(bundle: ConfigBundle, item: ProjectItem) -> Optional[RepoConfig]:
    repo_name = None
    if item.content and item.content.repository:
        repo_name = item.content.repository.split("/")[-1]
    elif item.repository:
        repo_name = item.repository.rsplit("/", 1)[-1]
    if not repo_name:
        return None
    for repo in bundle.repos.repos:
        if repo.key == repo_name or repo.path.name == repo_name:
            return repo
    return None


def status_field_and_option(fields: list[ProjectField], status_name: str) -> tuple[str, str]:
    for field in fields:
        if field.name == "Status":
            for option in field.options:
                if option.name == status_name:
                    return field.id, option.id
    raise ValueError(f"Status option not found: {status_name}")


def triage_backlog(ctx: PipelineContext, *, dry_run: bool = False) -> list[str]:
    items = ctx.github.list_project_items()
    results: list[str] = []
    if should_skip_poll(ctx, items):
        return ["No project changes detected; triage skipped."]
    for item in items:
        if item.status != ctx.bundle.pipeline.stages["backlog"].project_status or not item.is_linked_issue:
            continue
        repo = route_repo_for_item(ctx.bundle, item)
        if not repo or not item.content:
            continue
        labels = ctx.bundle.labels.labels
        if labels["triaged"] in item.labels:
            continue
        comment = "\n".join(
            [
                "Hermes triage summary:",
                f"- issue: {item.content.title}",
                f"- repo: {repo.key}",
                f"- suggested task class: {route_for_task(ctx.bundle.models, 'triage_simple').preferred_model}",
                "- next step: move this item to Ready when implementation should begin",
            ]
        )
        if not dry_run:
            ctx.github.ensure_label(item.content.repository, labels["triaged"])
            ctx.github.comment_issue(item.content.repository, item.content.number, comment)
            ctx.github.add_labels(item.content.repository, item.content.number, [labels["triaged"]])
        results.append(f"Triaged issue #{item.content.number} in {repo.key}")
    return results or ["No backlog items required triage."]


def execute_ready(ctx: PipelineContext, *, dry_run: bool = False) -> list[str]:
    items = ctx.github.list_project_items()
    results: list[str] = []
    fields = ctx.github.get_project_fields()
    project_meta = ctx.github.view_project()
    status_field_id, in_progress_option_id = status_field_and_option(
        fields, ctx.bundle.pipeline.stages["in_progress"].project_status
    )
    global_limit = ctx.bundle.pipeline.concurrency.global_execution_limit
    active_global = len([claim for claim in ctx.state.list_claims() if claim.stage == "execute"])

    for item in items:
        if item.status != ctx.bundle.pipeline.stages["ready"].project_status or not item.is_linked_issue:
            continue
        if active_global >= global_limit:
            break
        repo = route_repo_for_item(ctx.bundle, item)
        if not repo or not item.content:
            continue
        if ctx.state.count_active_for_repo(repo.key, stages=("execute",)) >= repo.execution_concurrency:
            continue
        branch_name = render_branch_name(repo.branch_template, item.content.number, item.content.title)
        worktree = ensure_worktree(repo.path, repo.worktree_root, branch_name, item.content.title) if not dry_run else repo.worktree_root / branch_name
        if not dry_run:
            ctx.state.upsert_claim(
                item_id=item.id,
                repo_key=repo.key,
                stage="execute",
                status="claimed",
                branch_name=branch_name,
                worktree_path=str(worktree),
            )
            labels = ctx.bundle.labels.labels
            ctx.github.ensure_label(item.content.repository, labels["claimed"])
            ctx.github.ensure_label(item.content.repository, labels["executing"])
            ctx.github.add_labels(item.content.repository, item.content.number, [labels["claimed"], labels["executing"]])
            ctx.github.comment_issue(
                item.content.repository,
                item.content.number,
                format_heartbeat(stage="execute", action=f"claimed worktree={worktree}"),
            )
            ctx.github.item_edit_status(item.id, project_meta["id"], status_field_id, in_progress_option_id)
        results.append(f"Claimed #{item.content.number} for execution in {repo.key}")
        active_global += 1
    return results or ["No ready items were claimed."]


def transition_to_review(
    ctx: PipelineContext,
    *,
    repo_key: str,
    item_id: str,
    pr_title: str,
    pr_body: str,
    dry_run: bool = False,
) -> str:
    claim = ctx.state.get_claim(item_id)
    if not claim:
        return f"No claim found for item {item_id}"
    repo = ctx.bundle.repos.repo_by_key(repo_key)
    if not repo:
        return f"Unknown repo {repo_key}"
    items = {item.id: item for item in ctx.github.list_project_items()}
    item = items[item_id]
    if not item.content:
        return f"Item {item_id} has no linked issue"
    fields = ctx.github.get_project_fields()
    project_meta = ctx.github.view_project()
    status_field_id, review_option_id = status_field_and_option(
        fields, ctx.bundle.pipeline.stages["in_review"].project_status
    )
    pr_result: dict[str, object] | None = None
    if not dry_run:
        pr_result = ctx.github.create_pr(item.content.repository, repo.default_branch, claim.branch_name or "", pr_title, pr_body)
        labels = ctx.bundle.labels.labels
        ctx.github.remove_label(item.content.repository, item.content.number, labels["executing"])
        ctx.github.add_labels(item.content.repository, item.content.number, [labels["awaiting_review"]])
        ctx.github.item_edit_status(item.id, project_meta["id"], status_field_id, review_option_id)
        ctx.state.upsert_claim(
            item_id=item_id,
            repo_key=repo.key,
            stage="review",
            status="awaiting_review",
            branch_name=claim.branch_name,
            worktree_path=claim.worktree_path,
            pr_number=int(pr_result["number"]) if pr_result and pr_result.get("number") is not None else claim.pr_number,
        )
        pr_url = str(pr_result["url"]) if pr_result else ""
        ctx.github.comment_issue(item.content.repository, item.content.number, f"Hermes moved work to review.\n\nPR: {pr_url}")
        return pr_url or f"Prepared review transition for {item_id}"
    return f"Prepared review transition for {item_id}"


def review_in_review(ctx: PipelineContext, *, approve: bool, dry_run: bool = False) -> list[str]:
    items = ctx.github.list_project_items()
    results: list[str] = []
    fields = ctx.github.get_project_fields()
    project_meta = ctx.github.view_project()
    target_status = "done" if approve else "ready"
    status_field_id, option_id = status_field_and_option(
        fields, ctx.bundle.pipeline.stages[target_status].project_status
    )
    labels = ctx.bundle.labels.labels
    for item in items:
        if item.status != ctx.bundle.pipeline.stages["in_review"].project_status or not item.is_linked_issue or not item.content:
            continue
        repo = route_repo_for_item(ctx.bundle, item)
        if not repo:
            continue
        claim = ctx.state.get_claim(item.id)
        if not dry_run:
            ctx.github.ensure_label(item.content.repository, labels["review_claimed"])
            ctx.github.add_labels(item.content.repository, item.content.number, [labels["review_claimed"]])
            ctx.github.comment_issue(
                item.content.repository,
                item.content.number,
                format_heartbeat(stage="review", action="review-started"),
            )
            pr = None
            if claim and claim.pr_number:
                pr = {"number": claim.pr_number}
            elif claim and claim.branch_name:
                pr = ctx.github.find_pr_by_head(item.content.repository, claim.branch_name)
            if pr and pr.get("number") is not None:
                ctx.github.review_pr(
                    item.content.repository,
                    int(pr["number"]),
                    approve=approve,
                    body="Hermes automated review outcome.",
                )
            if approve:
                ctx.github.add_labels(item.content.repository, item.content.number, [labels["approved"]])
            else:
                ctx.github.add_labels(item.content.repository, item.content.number, [labels["changes_requested"]])
            ctx.github.item_edit_status(item.id, project_meta["id"], status_field_id, option_id)
            ctx.state.upsert_claim(
                item_id=item.id,
                repo_key=repo.key,
                stage="review",
                status="approved" if approve else "changes_requested",
            )
        results.append(f"Reviewed #{item.content.number} -> {target_status}")
    return results or ["No review items were processed."]


def release_done(ctx: PipelineContext, *, dry_run: bool = False) -> list[str]:
    items = ctx.github.list_project_items()
    results: list[str] = []
    labels = ctx.bundle.labels.labels
    for item in items:
        if item.status != ctx.bundle.pipeline.stages["done"].project_status or not item.is_linked_issue or not item.content:
            continue
        repo = route_repo_for_item(ctx.bundle, item)
        if not repo or not repo.release.enabled:
            continue
        if labels["human_approved"] not in item.labels:
            continue
        claim = ctx.state.get_claim(item.id)
        pr = None
        if claim and claim.pr_number:
            pr = {"number": claim.pr_number}
        elif claim and claim.branch_name:
            pr = ctx.github.find_pr_by_head(item.content.repository, claim.branch_name)
        if not dry_run:
            if pr and pr.get("number") is not None:
                ctx.github.merge_pr(item.content.repository, int(pr["number"]), repo.release.merge_strategy)
            for command in repo.release.post_merge_commands:
                run_shell(command, cwd=repo.path, check=True)
            ctx.github.comment_issue(item.content.repository, item.content.number, "Hermes merged and ran release hooks.")
        results.append(f"Release-ready #{item.content.number} in {repo.key}")
    return results or ["No done items are release-ready."]


def reap_stale(ctx: PipelineContext, *, dry_run: bool = False) -> list[str]:
    results: list[str] = []
    now = datetime.now(timezone.utc)
    warning_seconds = ctx.bundle.pipeline.heartbeats.stale_warning_after_seconds
    reclaim_seconds = ctx.bundle.pipeline.heartbeats.reclaim_after_seconds
    labels = ctx.bundle.labels.labels
    items = {item.id: item for item in ctx.github.list_project_items()}
    for claim in ctx.state.list_claims():
        if not claim.last_heartbeat_at:
            continue
        last = datetime.fromisoformat(claim.last_heartbeat_at)
        item = items.get(claim.item_id)
        if item is None or not item.content:
            continue
        repo = route_repo_for_item(ctx.bundle, item)
        if not repo:
            continue
        age = now - last
        if age > timedelta(seconds=reclaim_seconds):
            if not dry_run:
                ctx.github.ensure_label(item.content.repository, labels["stale"])
                ctx.github.add_labels(item.content.repository, item.content.number, [labels["stale"]])
                ctx.github.comment_issue(item.content.repository, item.content.number, "Hermes marked this task stale and returned it for recovery.")
                ctx.state.delete_claim(claim.item_id)
            results.append(f"Reclaimed stale item {claim.item_id}")
        elif age > timedelta(seconds=warning_seconds):
            if not dry_run:
                ctx.github.ensure_label(item.content.repository, labels["stale"])
                ctx.github.add_labels(item.content.repository, item.content.number, [labels["stale"]])
                ctx.github.comment_issue(item.content.repository, item.content.number, "Hermes warning: no recent heartbeat detected.")
            results.append(f"Warned stale item {claim.item_id}")
    return results or ["No stale claims detected."]
