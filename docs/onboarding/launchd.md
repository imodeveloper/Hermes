# Launchd

Hermes uses `launchd` for local scheduled polling.

## Generate a plist

```bash
hermes scheduler-install --config-dir ./.hermes
```

By default this writes:

- `~/Library/LaunchAgents/com.imodeveloper.hermes.plist`

## Load it

```bash
launchctl load ~/Library/LaunchAgents/com.imodeveloper.hermes.plist
```

## Unload it

```bash
launchctl unload ~/Library/LaunchAgents/com.imodeveloper.hermes.plist
```

The generated plist runs `hermes poll-all` on the interval declared in `hermes.yaml`.

