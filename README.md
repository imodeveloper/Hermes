# Hermes

Hermes is an open-source local orchestrator for GitHub Projects. It triages backlog items, claims ready work, runs tasks in isolated worktrees, opens PRs, coordinates review, detects stale agents, and moves approved work through merge and release across multiple repos.

## Status

Hermes is in active bootstrap. The roadmap is tracked in GitHub issues `#1` to `#16`, and the current architecture plan lives in [`docs/architecture/v1-plan.md`](docs/architecture/v1-plan.md).

## Principles

- Local-first orchestration to keep polling cheap and reduce token use.
- Explicit configuration over hidden behavior.
- Human-gated merge and release by default.
- Reusable skills and compact context packs for model efficiency.
- Clear docs, memory files, and changelog entries so future agents can continue work safely.

## Planned Modules

- `src/hermes/cli`: CLI entrypoints and command surface.
- `src/hermes/config`: config loading and schema validation.
- `src/hermes/github`: GitHub and project metadata access via `gh`.
- `src/hermes/pipeline`: stage logic for triage, execution, review, release, and stale recovery.
- `src/hermes/state`: local SQLite-backed runtime state and locking.
- `src/hermes/context`: slim context-pack generation and cache policy.
- `src/hermes/skills`: stage-scoped skill definitions and prompt helpers.
- `src/hermes/doctor`: environment validation, preflight, and dependency checks.
- `src/hermes/sandbox`: end-to-end dry-run and sandbox ticket flows.
- `Sources/HermesBar`: native macOS menu bar companion for scheduler status and controls.

## Quick Start

1. Clone the repo locally.
2. Ensure `git`, `gh`, `python3`, `sqlite3`, and `launchctl` are available.
3. Read [`AGENTS.md`](AGENTS.md) for repo rules and contributor workflow.
4. Read [`docs/architecture/v1-plan.md`](docs/architecture/v1-plan.md) for the v1 design.
5. Follow the roadmap in [`memory/ROADMAP.md`](memory/ROADMAP.md).

## Repo Navigation

- Architecture: [`docs/architecture/v1-plan.md`](docs/architecture/v1-plan.md)
- Onboarding: [`docs/onboarding/quickstart.md`](docs/onboarding/quickstart.md)
- Contributor guide: [`docs/contributing/development.md`](docs/contributing/development.md)
- Memory and progress: [`memory/`](memory)
