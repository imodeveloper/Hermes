# Sandbox

Hermes supports sandbox ticket creation to validate the pipeline without using a real task.

## Create a sandbox ticket

```bash
hermes sandbox-create-ticket --repo OWNER/REPO --config-dir ./.hermes
```

## Run a lightweight sandbox bootstrap

```bash
hermes sandbox-run-e2e --repo OWNER/REPO --config-dir ./.hermes
```

This currently creates the sandbox issue and prints the next manual steps for board-driven validation.

