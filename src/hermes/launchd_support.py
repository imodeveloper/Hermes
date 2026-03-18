"""launchd integration helpers."""

from __future__ import annotations

from pathlib import Path


def plist_contents(*, project_root: Path, interval_seconds: int, config_dir: Path) -> str:
    executable = project_root / ".venv" / "bin" / "hermes"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.imodeveloper.hermes</string>
    <key>ProgramArguments</key>
    <array>
      <string>{executable}</string>
      <string>poll-all</string>
      <string>--config-dir</string>
      <string>{config_dir}</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval_seconds}</integer>
    <key>RunAtLoad</key>
    <true/>
  </dict>
</plist>
"""

