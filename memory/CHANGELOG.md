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
