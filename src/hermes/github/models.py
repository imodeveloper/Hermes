"""GitHub-side models used by Hermes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProjectFieldOption:
    id: str
    name: str


@dataclass
class ProjectField:
    id: str
    name: str
    type: str
    options: list[ProjectFieldOption] = field(default_factory=list)


@dataclass
class IssueContent:
    number: int
    title: str
    body: str
    repository: str
    url: str
    type: str


@dataclass
class ProjectItem:
    id: str
    title: str
    status: str
    repository: Optional[str]
    labels: list[str]
    assignees: list[str]
    content: Optional[IssueContent] = None

    @property
    def is_linked_issue(self) -> bool:
        return self.content is not None and self.content.type == "Issue"
