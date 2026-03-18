# Hermes Agent Guide

## Purpose

Hermes is a local orchestrator for GitHub Projects. It is intended to coordinate multi-agent work across multiple repositories using explicit config, local state, worktrees, review gates, and low-token execution patterns.

## Working Rules

- Read the roadmap issue and relevant docs before changing code.
- Keep changes scoped to the current roadmap issue.
- Use small, reviewable commits on `codex/<issue-slice>` branches.
- Update `memory/CHANGELOG.md` and `memory/ROADMAP.md` on every issue slice.
- Prefer standard library plus `gh` and `git` subprocess calls unless a roadmap issue explicitly justifies new dependencies.
- Do not auto-close roadmap issues locally; close issues only after code, docs, and validation for that slice are complete.

## Core Files

- Architecture plan: `docs/architecture/v1-plan.md`
- Changelog: `memory/CHANGELOG.md`
- Roadmap tracking: `memory/ROADMAP.md`
- Design decisions: `memory/DECISIONS.md`
- Failure learnings: `memory/FAILURE_PATTERNS.md`

## Safety

- Treat repo path allowlists, merge gates, and model-routing constraints as critical behavior.
- Never weaken merge/release safety or secret redaction without explicit review.
- Keep self-improvement limited to noncritical files until the corresponding roadmap issues are implemented.

## Bootstrap Sequence

The initial roadmap order is:

1. Bootstrap repository structure and contributor docs.
2. Define configuration schema and examples.
3. Build CLI foundation and config loading.
4. Add state store and locking.
5. Add GitHub project discovery.
6. Implement pipeline stages incrementally.
7. Add doctor, sandbox, and security documentation.

