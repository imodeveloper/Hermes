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
