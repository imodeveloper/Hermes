# Pipeline Architecture

Hermes operates on a GitHub Project with these default stages:

- `Backlog`: triage only
- `Ready`: claimable execution queue
- `In progress`: active work
- `In review`: active review
- `Done`: merge/release queue

Each poll cycle is local-first:

1. fetch project items via `gh`
2. compare a snapshot hash to the last seen state
3. short-circuit if nothing changed
4. run only the stage logic that has eligible items

