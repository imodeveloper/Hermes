from pathlib import Path

from hermes.config.loader import load_bundle
from hermes.doctor.checks import basic_environment_checks


def test_basic_environment_checks_reports_workspace(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    bundle = load_bundle(root / "config" / "examples")
    bundle.hermes.workspace_root = tmp_path
    results = basic_environment_checks(bundle)
    assert any(result.name == "workspace-root" for result in results)
