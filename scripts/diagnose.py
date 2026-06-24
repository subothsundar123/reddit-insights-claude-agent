#!/usr/bin/env python3
"""Check the local Reddit Product Insights installation without changing it."""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys


SETUP_PATH = pathlib.Path(__file__).with_name("setup_unix.py")
SPEC = importlib.util.spec_from_file_location("insights_setup", SETUP_PATH)
assert SPEC and SPEC.loader
SETUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SETUP)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path.home() / "Documents" / "Nubra Product Insights")
    parser.add_argument("--claude-config", type=pathlib.Path)
    args = parser.parse_args()

    platform = SETUP.platform_name()
    config_path = (args.claude_config or SETUP.find_claude_config(platform)).expanduser()
    data_dir = args.data_dir.expanduser()
    problems: list[str] = []

    server = None
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8-sig"))
            server = config.get("mcpServers", {}).get(SETUP.SERVER_NAME)
        except (json.JSONDecodeError, OSError) as exc:
            problems.append(f"Claude configuration could not be read: {exc}")
    else:
        problems.append(f"Claude configuration is missing: {config_path}")
    if not server:
        problems.append("reddit-product-insights is not registered in Claude Desktop")
    elif not pathlib.Path(server.get("command", "")).exists():
        problems.append(f"Connector Python does not exist: {server.get('command')}")

    state_path = data_dir / "sync-state.json"
    state = None
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError) as exc:
            problems.append(f"Sync state could not be read: {exc}")
    else:
        problems.append(f"No synced data was found: {state_path}")

    scheduler = "not detected"
    if platform == "macos":
        plist = pathlib.Path.home() / "Library" / "LaunchAgents" / f"{SETUP.APP_ID}.plist"
        scheduler = str(plist) if plist.exists() else "missing"
        if not plist.exists():
            problems.append("macOS daily updater is not installed")
    elif platform == "linux":
        result = subprocess.run(
            ["systemctl", "--user", "is-enabled", "reddit-product-insights-update.timer"],
            capture_output=True,
            text=True,
            check=False,
        )
        scheduler = result.stdout.strip() or result.stderr.strip() or "missing"
        if result.returncode:
            problems.append("Linux daily updater is not enabled")

    print(f"Claude configuration: {config_path}")
    print(f"Local data: {data_dir}")
    print(f"Latest dump: {max(state.get('dumps', [])) if state and state.get('dumps') else 'none'}")
    print(f"Catalog version: {state.get('catalog_version') if state else 'none'}")
    print(f"Daily updater: {scheduler}")
    if problems:
        print("\nProblems:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print("\nInstallation looks ready. Restart Claude Desktop if the connector is not visible yet.")


if __name__ == "__main__":
    main()
