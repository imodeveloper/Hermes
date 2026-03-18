# Permissions

Hermes needs:

- local filesystem access to configured repos and worktree roots
- GitHub CLI auth with project and repository scopes
- permission to create comments, labels, pull requests, and status transitions

Hermes should not require:

- direct secret files committed to the repo
- access to repos outside the configured allowlist
- automatic merge/release without a human gate unless explicitly reconfigured

