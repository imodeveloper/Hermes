"""Load Hermes configuration bundles."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from hermes.errors import ConfigError

from .models import ConfigBundle, HermesConfig, LabelsConfig, ModelsConfig, PipelineConfig, ReposConfig


CONFIG_FILE_MAP = {
    "hermes": "hermes.yaml",
    "repos": "repos.yaml",
    "pipeline": "pipeline.yaml",
    "labels": "labels.yaml",
    "models": "models.yaml",
}


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    loaded = yaml.safe_load(path.read_text()) or {}
    if not isinstance(loaded, dict):
        raise ConfigError(f"Config file must contain a YAML mapping: {path}")
    return loaded


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_bundle(config_dir: Path) -> ConfigBundle:
    """Load all Hermes config files from a directory."""

    config_dir = config_dir.resolve()
    if not config_dir.exists():
        raise ConfigError(f"Config directory does not exist: {config_dir}")

    local_override_path = config_dir / ".hermes.local.yaml"
    local_override = _read_yaml(local_override_path) if local_override_path.exists() else {}

    hermes_payload = _read_yaml(config_dir / CONFIG_FILE_MAP["hermes"])
    repos_payload = _read_yaml(config_dir / CONFIG_FILE_MAP["repos"])
    pipeline_payload = _read_yaml(config_dir / CONFIG_FILE_MAP["pipeline"])
    labels_payload = _read_yaml(config_dir / CONFIG_FILE_MAP["labels"])
    models_payload = _read_yaml(config_dir / CONFIG_FILE_MAP["models"])

    if local_override:
        hermes_payload = _deep_merge(hermes_payload, local_override.get("hermes", local_override))
        repos_payload = _deep_merge(repos_payload, local_override.get("repos", {}))
        pipeline_payload = _deep_merge(pipeline_payload, local_override.get("pipeline", {}))
        labels_payload = _deep_merge(labels_payload, local_override.get("labels", {}))
        models_payload = _deep_merge(models_payload, local_override.get("models", {}))

    hermes_cfg = HermesConfig.model_validate(hermes_payload)
    repos_cfg = ReposConfig.model_validate(repos_payload)
    pipeline_cfg = PipelineConfig.model_validate(pipeline_payload)
    labels_cfg = LabelsConfig.model_validate(labels_payload)
    models_cfg = ModelsConfig.model_validate(models_payload)

    return ConfigBundle(
        hermes=hermes_cfg,
        repos=repos_cfg,
        pipeline=pipeline_cfg,
        labels=labels_cfg,
        models=models_cfg,
        root=config_dir,
    )


def init_config_from_examples(*, project_root: Path, destination_dir: Path) -> list[Path]:
    """Copy example configuration files into a destination directory."""

    source_dir = project_root / "config" / "examples"
    if not source_dir.exists():
        raise ConfigError(f"Example config directory is missing: {source_dir}")

    destination_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for file_name in CONFIG_FILE_MAP.values():
        source = source_dir / file_name
        target = destination_dir / file_name
        if not target.exists():
            target.write_text(source.read_text())
            written.append(target)
    return written


def personalize_init_files(
    *,
    destination_dir: Path,
    workspace_root: Path,
    state_root: Path,
    project_owner: str,
    project_number: int,
) -> None:
    """Rewrite copied example files with locally useful defaults."""

    hermes_path = destination_dir / "hermes.yaml"
    repos_path = destination_dir / "repos.yaml"

    hermes_payload = _read_yaml(hermes_path)
    hermes_payload["workspace_root"] = str(workspace_root)
    hermes_payload["project"]["owner"] = project_owner
    hermes_payload["project"]["number"] = project_number
    hermes_payload["runtime"]["state_db_path"] = str(state_root / "state.sqlite3")
    hermes_payload["runtime"]["log_path"] = str(state_root / "hermes.log")
    hermes_payload["runtime"]["worktree_root"] = str(workspace_root / "Worktrees")
    hermes_path.write_text(yaml.safe_dump(hermes_payload, sort_keys=False))

    repos_payload = _read_yaml(repos_path)
    for repo in repos_payload.get("repos", []):
        repo_path = workspace_root / repo["key"]
        repo["path"] = str(repo_path)
        repo["worktree_root"] = str((workspace_root / "Worktrees" / repo["key"]).resolve())
    repos_path.write_text(yaml.safe_dump(repos_payload, sort_keys=False))
