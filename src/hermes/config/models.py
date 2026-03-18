"""Configuration models for Hermes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class ProjectConfig(BaseModel):
    owner: str
    number: int


class SchedulerConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = 60
    timezone: str = "UTC"


class RuntimeConfig(BaseModel):
    state_db_path: Path
    log_path: Path
    worktree_root: Path
    global_execution_limit: int = 2


class GitHubConfig(BaseModel):
    use_gh_cli: bool = True
    refresh_project_metadata_every_seconds: int = 300
    no_op_fast_path: bool = True


class FeatureFlags(BaseModel):
    allow_triage_comments: bool = True
    allow_priority_updates: bool = True
    allow_pr_creation: bool = True
    allow_release: bool = False


class HermesConfig(BaseModel):
    workspace_root: Path
    project: ProjectConfig
    scheduler: SchedulerConfig
    runtime: RuntimeConfig
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)


class ReleaseConfig(BaseModel):
    enabled: bool = False
    human_gate_label: str = "human-approved"
    merge_strategy: str = "squash"
    post_merge_commands: list[str] = Field(default_factory=list)


class RepoConfig(BaseModel):
    key: str
    path: Path
    default_branch: str
    worktree_root: Path
    branch_template: str = "codex/{issue_number}-{slug}"
    execution_concurrency: int = 1
    executable: bool = True
    validation_commands: list[str] = Field(default_factory=list)
    release: ReleaseConfig = Field(default_factory=ReleaseConfig)


class ReposConfig(BaseModel):
    repos: list[RepoConfig]

    def repo_by_key(self, key: str) -> Optional[RepoConfig]:
        return next((repo for repo in self.repos if repo.key == key), None)

    def repo_for_path(self, path: Path) -> Optional[RepoConfig]:
        for repo in self.repos:
            if repo.path == path:
                return repo
        return None


class StageConfig(BaseModel):
    project_status: str
    action: str
    auto_transition: bool = False


class ConcurrencyConfig(BaseModel):
    global_execution_limit: int = 2
    global_review_limit: int = 2


class HeartbeatConfig(BaseModel):
    comment_every_seconds: int = 300
    stale_warning_after_seconds: int = 600
    reclaim_after_seconds: int = 900


class ClaimsConfig(BaseModel):
    require_local_lock: bool = True
    require_repo_allowlist: bool = True
    reuse_existing_pr: bool = True
    reuse_existing_worktree: bool = True


class RecoveryConfig(BaseModel):
    add_stale_label: bool = True
    return_unfinished_items_to_ready: bool = True
    return_review_rejections_to_ready: bool = True
    stop_on_conflict_without_rule: bool = True


class PipelineConfig(BaseModel):
    stages: dict[str, StageConfig]
    concurrency: ConcurrencyConfig = Field(default_factory=ConcurrencyConfig)
    heartbeats: HeartbeatConfig = Field(default_factory=HeartbeatConfig)
    claims: ClaimsConfig = Field(default_factory=ClaimsConfig)
    recovery: RecoveryConfig = Field(default_factory=RecoveryConfig)


class LabelsConfig(BaseModel):
    labels: dict[str, str]
    mutually_exclusive_groups: list[list[str]] = Field(default_factory=list)


class EscalationConfig(BaseModel):
    on_ambiguity: Optional[str] = None
    on_failure: Optional[str] = None
    on_large_diff: Optional[str] = None
    on_risk: Optional[str] = None


class TaskModelConfig(BaseModel):
    preferred_model: str
    max_prompt_chars: int
    max_context_expansions: int = 1
    escalation: EscalationConfig = Field(default_factory=EscalationConfig)


class ModelsDefaults(BaseModel):
    progress_comment_model: str = "small"
    stale_comment_model: str = "small"
    release_check_model: str = "medium"
    stop_after_total_escalations: int = 1


class ModelsConfig(BaseModel):
    task_classes: dict[str, TaskModelConfig]
    defaults: ModelsDefaults = Field(default_factory=ModelsDefaults)


class ConfigBundle(BaseModel):
    hermes: HermesConfig
    repos: ReposConfig
    pipeline: PipelineConfig
    labels: LabelsConfig
    models: ModelsConfig
    root: Path

    @model_validator(mode="after")
    def validate_paths(self) -> "ConfigBundle":
        repo_keys = set()
        for repo in self.repos.repos:
            if repo.key in repo_keys:
                raise ValueError(f"Duplicate repo key: {repo.key}")
            repo_keys.add(repo.key)
        return self

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "workspace_root": str(self.hermes.workspace_root),
            "project_owner": self.hermes.project.owner,
            "project_number": self.hermes.project.number,
            "repos": [repo.key for repo in self.repos.repos],
            "scheduler_interval_seconds": self.hermes.scheduler.interval_seconds,
        }
