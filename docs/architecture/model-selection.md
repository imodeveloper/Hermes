# Model Selection

Model selection is config-driven.

Hermes should:

- start with the cheapest viable route for the current task class
- escalate only when the configured rule requires it
- cap context expansions
- stop and request human intervention instead of burning tokens repeatedly

The routing rules are defined in `models.yaml`.

