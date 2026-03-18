from pathlib import Path

from hermes.state.store import StateStore


def test_state_store_lock_and_claim(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.sqlite3")
    store.initialize()
    store.acquire_lock("scheduler", "test-owner")
    store.release_lock("scheduler")

    store.upsert_claim(
        item_id="item-1",
        repo_key="repo",
        stage="execute",
        status="claimed",
        branch_name="codex/1-task",
        worktree_path="/tmp/worktree",
    )
    claim = store.get_claim("item-1")
    assert claim is not None
    assert claim.repo_key == "repo"
    store.record_heartbeat("item-1")
    assert store.get_claim("item-1") is not None

