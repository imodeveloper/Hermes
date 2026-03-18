# Hermes Changelog

## 2026-03-18

### Issue
- `#1` Bootstrap Hermes repository structure and contributor docs

### Request
- Create the roadmap issues first.
- Add the master plan, contributor docs, memory files, and initial Python scaffold.
- Keep progress tracked in repo memory files and use small commits.

### Done
- Added GitHub roadmap labels and created the canonical roadmap issue set `#1` to `#16`.
- Closed duplicate roadmap issues created during bootstrap retries and kept the original sequence.
- Bootstrapped the Hermes repo structure with:
  - top-level docs
  - architecture and onboarding docs
  - contributor guide
  - memory files
  - initial Python package scaffold
  - packaging metadata

### Validation
- Verified GitHub issue creation and labels through `gh issue list`.
- Verified the local repo scaffold exists under the expected directories.
- `python3 -m compileall src tests` passed.
- Importing `hermes.cli.main` is not yet runnable in this shell because declared Python dependencies such as `typer` are not installed locally.

### Next
- Finish the remaining bootstrap files for Issue `#1`.
- Commit the initial scaffold in small slices.
- Move to Issue `#2` after Issue `#1` is complete and documented.

## 2026-03-18 (Config Examples)

### Issue
- `#2` Define Hermes configuration schema and example configs

### Request
- Add example config files for scheduler, repos, labels, pipeline stages, and model routing.
- Make the public config surface explicit and documented for later implementation issues.

### Done
- Added committed example configs:
  - `config/examples/hermes.yaml`
  - `config/examples/repos.yaml`
  - `config/examples/pipeline.yaml`
  - `config/examples/labels.yaml`
  - `config/examples/models.yaml`
- Replaced the config examples placeholder README with a real inventory of the public config surface.
- Added `docs/onboarding/configuration.md` to document every top-level config file and its main keys.

### Validation
- Verified the example files are present in the repo and grouped under `config/examples/`.
- Performed manual schema review to ensure the files cover scheduler, repos, labels, stages, stale policy, and model routing.
- Parser-backed validation is deferred to Issue `#3`, which introduces config loading and schema enforcement.

### Next
- Commit the configuration examples in a small slice.
- Implement Issue `#3` on top of these committed config contracts.

## 2026-03-18 (CLI Foundation and MVP Runtime)

### Issue
- `#3` Implement Hermes CLI foundation and config loading
- `#4` Implement local state store and lock management
- `#5` Implement GitHub project discovery and metadata sync
- `#6` Implement triage stage for Backlog items
- `#7` Implement execution stage for Ready items with worktree orchestration
- `#8` Implement pull request creation and In review transition
- `#9` Implement review stage with approve/reject outcomes
- `#10` Implement merge and release stage with human gate
- `#11` Implement stale-run detection, heartbeats, and recovery
- `#12` Implement model routing and token budget controls
- `#13` Implement init wizard and launchd scheduler integration
- `#14` Implement doctor, preflight, and dependency validation
- `#15` Implement sandbox end-to-end validation flow
- `#16` Document security model, extension points, and contributor workflow

### Request
- Continue implementation until Hermes is functional and testable.
- Keep the roadmap, changelog, and docs aligned with the code.
- Make onboarding easy and keep token use low through local-first behavior and model routing.

### Done
- Replaced the placeholder package with a functional Hermes MVP:
  - CLI command surface
  - YAML config loading and local override support
  - SQLite runtime state and scheduler locks
  - GitHub CLI integration for project items, issues, labels, PRs, and status changes
  - pipeline operations for triage, execution claims, review processing, release-ready detection, and stale recovery
  - worktree naming and creation helpers
  - model routing helpers
  - doctor/preflight checks
  - sandbox ticket creation
  - launchd plist generation
- Added docs for:
  - configuration
  - quickstart
  - launchd
  - model routing
  - pipeline architecture
  - state model
  - context packs
  - model selection
  - recovery
  - sandbox
  - permissions
  - contributor extension points
- Adjusted Python compatibility to `>=3.9` because the available local interpreter is Python 3.9.

### Validation
- Installed Hermes into a local virtual environment with `pip install -e '.[dev]'`.
- CLI smoke checks:
  - `hermes version`
  - `hermes show-config`
  - `hermes init --destination-dir /tmp/hermes-demo-2 --workspace-root /Users/ivan.borinschi/Work --state-root /tmp/hermes-state-2 --project-owner imodeveloper --project-number 1`
  - `hermes show-config --config-dir /tmp/hermes-demo-2`
  - `hermes doctor --config-dir /tmp/hermes-demo-2`
  - `hermes scheduler-install --config-dir /tmp/hermes-demo-2 --destination /tmp/com.imodeveloper.hermes.plist`
  - `hermes sandbox-create-ticket --repo imodeveloper/Hermes --config-dir /tmp/hermes-demo-2`
  - `hermes sandbox-run-e2e --repo imodeveloper/Hermes --config-dir /tmp/hermes-demo-2`
  - `hermes poll-all --config-dir /tmp/hermes-demo-2 --dry-run`
- Test suite:
  - `pytest -q`

### Next
- Push the CLI foundation branch and close the implemented roadmap issues.
- Run additional live GitHub/project validation against a real Hermes config if needed.

## 2026-03-18 (Launchd Environment Fix)

### Issue
- Post-roadmap runtime fix

### Request
- Start Hermes on this machine through `launchd`.

### Done
- Generated a repo-local Hermes config under `.hermes`.
- Loaded Hermes as a `launchd` agent from `~/Library/LaunchAgents/com.imodeveloper.hermes.plist`.
- Fixed the plist generator to include:
  - `WorkingDirectory`
  - `PATH`
  - `HOME`
  - `USER`
- Verified that Hermes can now run under the reduced launchd environment where `gh` still needs access to the user home and login state.

### Validation
- `hermes doctor --config-dir /Users/ivan.borinschi/Work/Hermes/.hermes`
- `env -i HOME=/Users/ivan.borinschi USER=ivan.borinschi PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin XPC_SERVICE_NAME=com.imodeveloper.hermes /Users/ivan.borinschi/Work/Hermes/.venv/bin/hermes poll-all --config-dir /Users/ivan.borinschi/Work/Hermes/.hermes`
- `launchctl print gui/$(id -u)/com.imodeveloper.hermes`

### Next
- Monitor the live scheduler behavior and use the sandbox tickets for manual pipeline validation.

## 2026-03-18 (HermesBar Menu App)

### Issue
- Post-roadmap usability addition

### Request
- Add a macOS menu bar app that shows Hermes status and exposes start, stop, restart, and run-now actions.
- Start it after building.

### Done
- Added a Swift package-based macOS menu bar companion:
  - `Package.swift`
  - `Sources/HermesBar/main.swift`
- HermesBar currently shows:
  - scheduler state
  - last exit code
  - run count
  - PID when active
  - active claims from the Hermes SQLite state DB
- HermesBar actions:
  - `Run Now`
  - `Start Scheduler`
  - `Stop Scheduler`
  - `Restart Scheduler`
  - `Open Config`
  - `Open State Folder`
  - `Open LaunchAgent`
  - `Quit HermesBar`
- Built the app with `swift build -c release`.
- Started HermesBar in a live interactive session so it remains running on this machine.

### Validation
- `swift build -c release`
- interactive launch of `./.build/release/HermesBar`
- verified process presence with `ps aux | rg '[H]ermesBar'`

### Next
- If needed, package HermesBar as a proper `.app` bundle for detached GUI launching without a terminal-backed session.
