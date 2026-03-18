# Threat Model

Hermes will eventually operate across multiple repositories with filesystem and GitHub mutation privileges. The main risks are:

- access outside the configured repo allowlist
- accidental issue, PR, or project mutations
- unintended merge or release
- secrets leaking through logs, comments, or context packs
- stale claims causing duplicate or conflicting work
- over-aggressive model escalation wasting tokens or taking unsafe actions

Early mitigation goals:

- explicit repo allowlists in config
- human-gated merge and release
- local state and lock validation
- structured logging with redaction
- documented recovery paths

