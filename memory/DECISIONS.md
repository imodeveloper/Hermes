# Design Decisions

## 2026-03-18

- Hermes is a standalone public repo, not embedded inside an application repo.
- The roadmap source of truth is GitHub issues `#1` to `#16`.
- The local scheduler target is `launchd`.
- Runtime state will be stored in SQLite.
- Hermes should optimize for low token use through local-first polling, cached metadata, and model routing by task class.

