# Development

## Current State

Hermes is in bootstrap. Start from roadmap issue `#1` and proceed in order unless a higher-priority corrective fix is required.

## Workflow

- Create or reuse a `codex/<issue-slice>` branch.
- Keep commits small and scoped.
- Update `memory/CHANGELOG.md` and `memory/ROADMAP.md` for every issue slice.
- Add docs alongside code when behavior or config surface changes.
- Validate each slice enough to support the issue acceptance criteria.

## Dependency Policy

- Prefer Python stdlib first.
- Prefer `gh` and `git` subprocess integration before introducing external SDKs.
- Introduce dependencies only in the issue that requires them.
- Document every added dependency in the README and relevant docs.

