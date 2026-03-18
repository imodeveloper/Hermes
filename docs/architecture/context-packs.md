# Context Packs

Hermes is designed to send compact context to agents.

A context pack should contain:

- issue title and body
- repo and worktree path
- stage-specific instructions
- small selected `AGENTS.md` excerpts
- small selected memory snippets
- relevant file shortlist
- PR and branch metadata

Hermes should avoid sending:

- full repo dumps
- unchanged prior context
- secrets or credential files
- unnecessary long diffs

