from pathlib import Path

from hermes.config.loader import load_bundle
from hermes.model_routing import route_for_task


def test_route_for_task_uses_models_yaml() -> None:
    root = Path(__file__).resolve().parents[1]
    bundle = load_bundle(root / "config" / "examples")
    route = route_for_task(bundle.models, "execute_small")
    assert route.preferred_model == "medium"
    assert route.max_prompt_chars == 10000

