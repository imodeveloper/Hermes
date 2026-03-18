# Failure Patterns

## 2026-03-18

### Duplicate roadmap issue creation

- Cause: retried `gh issue create` commands while a previous batch was still draining output.
- Effect: duplicate roadmap issues were created.
- Recovery: kept the original `#1` to `#16` sequence and closed duplicates with an explanatory comment.
- Guardrail: prefer idempotent issue-creation tooling or check for existing open issues before retrying.

