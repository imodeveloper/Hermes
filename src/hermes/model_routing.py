"""Model routing and token budget helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .config.models import ModelsConfig, TaskModelConfig


@dataclass
class RouteDecision:
    task_class: str
    preferred_model: str
    max_prompt_chars: int
    max_context_expansions: int


def route_for_task(models: ModelsConfig, task_class: str) -> RouteDecision:
    """Return the configured route for a task class."""

    config: TaskModelConfig = models.task_classes[task_class]
    return RouteDecision(
        task_class=task_class,
        preferred_model=config.preferred_model,
        max_prompt_chars=config.max_prompt_chars,
        max_context_expansions=config.max_context_expansions,
    )

