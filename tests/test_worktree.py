from hermes.pipeline.worktree import render_branch_name, slugify


def test_slugify_and_branch_rendering() -> None:
    assert slugify("Fix home screen performance issues") == "fix-home-screen-performance-issues"
    branch = render_branch_name("codex/{issue_number}-{slug}", 42, "Fix home screen performance issues")
    assert branch == "codex/42-fix-home-screen-performance-issues"

