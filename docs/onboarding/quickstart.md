# Quickstart

1. Install system tools: `git`, `gh`, `python3`, `sqlite3`, and `launchctl`.
2. Authenticate `gh` with the scopes needed for Projects and repository operations.
3. Create a virtual environment and install Hermes:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e '.[dev]'`
4. Generate a local config set:
   - `hermes init --destination-dir ./.hermes`
5. Run doctor:
   - `hermes doctor --config-dir ./.hermes`
6. Follow the roadmap and architecture docs before changing behavior.

The full setup wizard and doctor flow are planned in later roadmap issues.
