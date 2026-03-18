"""Sandbox flow helpers."""

from __future__ import annotations

from hermes.config.models import ConfigBundle
from hermes.github.client import GitHubClient


def sandbox_issue_title() -> str:
    return "[SANDBOX] Hermes end-to-end validation ticket"


def sandbox_issue_body() -> str:
    return "\n".join(
        [
            "This is a Hermes-managed sandbox ticket.",
            "",
            "Purpose:",
            "- validate triage",
            "- validate execution claim flow",
            "- validate review flow",
            "- validate stale recovery and release gate behavior",
        ]
    )


def create_sandbox_issue(bundle: ConfigBundle, github: GitHubClient, repo: str) -> str:
    labels = [bundle.labels.labels["sandbox"]]
    github.ensure_label(repo, bundle.labels.labels["sandbox"], color="5319E7", description="Hermes sandbox issue")
    return github.create_issue(repo, sandbox_issue_title(), sandbox_issue_body(), labels)
