# Hermes v1 Plan

## Goal

Hermes should become a local-first orchestrator for GitHub Projects that can:

- triage backlog work
- claim ready work
- execute in isolated worktrees
- open and review pull requests
- detect stale work
- merge and release with explicit human gates

## Execution Sequence

Roadmap issues `#1` to `#16` define the delivery order:

1. Bootstrap repo structure and contributor docs.
2. Define configuration schema and example configs.
3. Implement CLI foundation and config loading.
4. Implement local state store and locking.
5. Implement GitHub project discovery and metadata sync.
6. Implement triage stage.
7. Implement execution stage.
8. Implement PR creation and review handoff.
9. Implement review stage.
10. Implement merge and release stage.
11. Implement stale-run detection and recovery.
12. Implement model routing and token controls.
13. Implement init wizard and scheduler integration.
14. Implement doctor and dependency validation.
15. Implement sandbox end-to-end validation.
16. Document security model and extension points.

## Design Defaults

- Scheduler: local `launchd`
- Poll interval: 1 minute
- Global execution limit: 2
- Default merge/release gate: PR label `human-approved`
- Executable items: linked GitHub issues only
- Runtime state: local SQLite
- GitHub operations: `gh`
- Git isolation: `git worktree`

## Low-Token Rules

- Poll locally and cheaply.
- Do not invoke an agent when board state is unchanged.
- Cache field metadata, repo summaries, and context packs.
- Send only stage-specific context, not whole-repo dumps.
- Start with the cheapest viable model for each task class.
- Allow a single controlled context expansion before escalation.

## Safety

- Repos must be explicitly allowlisted in config.
- Paths outside configured repos are out of bounds.
- Secrets must be redacted from logs, prompts, comments, and context packs.
- Merge/release stays human-gated by default.
- Core pipeline safety, claim logic, and model routing are not self-modifying.

