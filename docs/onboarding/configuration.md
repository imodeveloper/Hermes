# Configuration

Hermes exposes its behavior through example YAML files under `config/examples/`.

## Files

### `hermes.yaml`

Global runtime configuration:

- `workspace_root`: base folder for managed repos
- `project.owner`: GitHub owner for the tracked Project
- `project.number`: GitHub Project number
- `scheduler.interval_seconds`: local poll interval
- `runtime.state_db_path`: SQLite state location
- `runtime.log_path`: log file location
- `runtime.worktree_root`: default worktree parent directory
- `runtime.global_execution_limit`: maximum active execution tasks
- `github.use_gh_cli`: use `gh` instead of a direct API client
- `github.refresh_project_metadata_every_seconds`: metadata refresh cadence
- `github.no_op_fast_path`: skip agent work when nothing changed

### `repos.yaml`

Managed repositories and release behavior:

- `key`: stable repo identifier in Hermes
- `path`: local repo path
- `default_branch`: tracked base branch
- `worktree_root`: repo-specific worktree location
- `branch_template`: branch naming pattern
- `execution_concurrency`: per-repo execution limit
- `validation_commands`: commands Hermes can run for validation
- `release`: merge and post-merge behavior

### `pipeline.yaml`

Pipeline behavior and safety rules:

- `stages`: mapping between Hermes stage names and project statuses
- `concurrency`: global limits
- `heartbeats`: heartbeat and stale thresholds
- `claims`: claim policy and reuse rules
- `recovery`: stale and rejection handling

### `labels.yaml`

Public label surface Hermes uses on issues and pull requests:

- stage-state labels
- review outcome labels
- stale and sandbox labels
- mutually exclusive label groups

### `models.yaml`

Task-to-model routing and token controls:

- `task_classes`: class-specific model choice and prompt budgets
- `preferred_model`: symbolic route chosen by future model-routing logic
- `max_prompt_chars`: prompt size ceiling
- `max_context_expansions`: allowed context expansions before escalation
- `escalation`: next route on ambiguity, risk, or failure
- `defaults`: model choices for low-cost comment and release checks

## Local Overrides

Machine-specific values should live outside committed examples:

- `.hermes.local.yaml`
- `.hermes.secrets.env`

These files should never be committed.

