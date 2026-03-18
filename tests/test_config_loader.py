from pathlib import Path

from hermes.config.loader import load_bundle


def test_load_bundle_from_examples() -> None:
    root = Path(__file__).resolve().parents[1]
    bundle = load_bundle(root / "config" / "examples")
    assert bundle.hermes.project.owner == "imodeveloper"
    assert bundle.pipeline.stages["ready"].project_status == "Ready"
    assert bundle.labels.labels["claimed"] == "hermes:claimed"
    assert "triage_simple" in bundle.models.task_classes

