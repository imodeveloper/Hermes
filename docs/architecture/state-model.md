# State Model

Hermes stores runtime state in SQLite.

Current tables:

- `scheduler_locks`
- `item_claims`
- `project_snapshots`

Purpose:

- prevent duplicate poll cycles
- track active claims and heartbeats
- remember PR/worktree associations
- enable no-op fast path for unchanged project state

