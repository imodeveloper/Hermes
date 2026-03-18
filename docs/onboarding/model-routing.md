# Model Routing

Hermes chooses a model route by task class, not by one global default.

The routing rules live in `config/examples/models.yaml` and are intended to keep token usage low:

- use cheaper routes for triage, labeling, progress comments, and stale comments
- use stronger routes for complex execution, risky review, and merge-conflict work
- limit prompt size and context expansions
- stop after the configured escalation cap instead of retrying indefinitely

Current task classes:

- `triage_simple`
- `triage_complex`
- `execute_small`
- `execute_large`
- `review_small`
- `review_risky`
- `merge_conflict`

