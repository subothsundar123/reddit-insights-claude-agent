#!/usr/bin/env python3
"""Install Reddit Product Insights for Claude Desktop on macOS or Linux."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import plistlib
import shutil
import subprocess
import sys
from typing import Any


APP_ID = "com.nubra.reddit-product-insights-update"
SERVER_NAME = "reddit-product-insights"
DEFAULT_REPO = "https://github.com/subothsundar123/reddit-scraper-github-publisher.git"
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def platform_name(value: str | None = None) -> str:
    value = value or sys.platform
    if value == "darwin":
        return "macos"
    if value.startswith("linux"):
        return "linux"
    return "unsupported"


def default_install_dir(platform: str, home: pathlib.Path | None = None) -> pathlib.Path:
    home = home or pathlib.Path.home()
    if platform == "macos":
        return home / "Library" / "Application Support" / "Reddit Product Insights"
    return home / ".local" / "share" / "reddit-product-insights"


def claude_config_candidates(platform: str, home: pathlib.Path | None = None) -> list[pathlib.Path]:
    home = home or pathlib.Path.home()
    if platform == "macos":
        return [home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"]
    xdg = pathlib.Path(os.getenv("XDG_CONFIG_HOME", str(home / ".config")))
    return [
        xdg / "Claude" / "claude_desktop_config.json",
        xdg / "claude" / "claude_desktop_config.json",
        home / ".var" / "app" / "com.anthropic.Claude" / "config" / "Claude" / "claude_desktop_config.json",
    ]


def find_claude_config(platform: str, home: pathlib.Path | None = None) -> pathlib.Path:
    candidates = claude_config_candidates(platform, home)
    return next((path for path in candidates if path.exists()), candidates[0])


def merge_claude_config(
    config_path: pathlib.Path,
    python_path: pathlib.Path,
    repo_url: str,
    data_dir: pathlib.Path,
) -> pathlib.Path | None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if config_path.exists():
        backup = config_path.with_name(
            f"{config_path.name}.backup-{dt.datetime.now():%Y%m%d-%H%M%S}"
        )
        shutil.copy2(config_path, backup)
        raw = config_path.read_text(encoding="utf-8-sig").strip()
        try:
            config: dict[str, Any] = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Claude Desktop configuration is not valid JSON: {config_path}") from exc
    else:
        config = {}

    config.setdefault("mcpServers", {})[SERVER_NAME] = {
        "command": str(python_path),
        "args": ["-m", "reddit_insights_agent.server"],
        "env": {
            "INSIGHTS_DATA_REPO_URL": repo_url,
            "INSIGHTS_DATA_BRANCH": "main",
            "INSIGHTS_LOCAL_DATA_DIR": str(data_dir),
            "INSIGHTS_DESKTOP_LOCAL_ONLY": "1",
        },
    }
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return backup


def launchd_payload(
    python_path: pathlib.Path,
    repo_url: str,
    data_dir: pathlib.Path,
    hour: int,
) -> dict[str, Any]:
    log_dir = data_dir / "logs"
    return {
        "Label": APP_ID,
        "ProgramArguments": [str(python_path), "-m", "reddit_insights_agent.cli", "sync"],
        "EnvironmentVariables": {
            "INSIGHTS_DATA_REPO_URL": repo_url,
            "INSIGHTS_DATA_BRANCH": "main",
            "INSIGHTS_LOCAL_DATA_DIR": str(data_dir),
            "INSIGHTS_DESKTOP_LOCAL_ONLY": "0",
            "GIT_TERMINAL_PROMPT": "0",
        },
        "StartCalendarInterval": {"Hour": hour, "Minute": 0},
        "RunAtLoad": True,
        "ProcessType": "Background",
        "StandardOutPath": str(log_dir / "update.log"),
        "StandardErrorPath": str(log_dir / "update-error.log"),
    }


def _systemd_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def systemd_units(
    python_path: pathlib.Path,
    repo_url: str,
    data_dir: pathlib.Path,
    hour: int,
) -> tuple[str, str]:
    service = "\n".join(
        [
            "[Unit]",
            "Description=Update Reddit Product Insights data",
            "After=network-online.target",
            "Wants=network-online.target",
            "",
            "[Service]",
            "Type=oneshot",
            f"Environment={_systemd_quote('INSIGHTS_DATA_REPO_URL=' + repo_url)}",
            'Environment="INSIGHTS_DATA_BRANCH=main"',
            f"Environment={_systemd_quote('INSIGHTS_LOCAL_DATA_DIR=' + str(data_dir))}",
            'Environment="INSIGHTS_DESKTOP_LOCAL_ONLY=0"',
            'Environment="GIT_TERMINAL_PROMPT=0"',
            f"ExecStart={_systemd_quote(str(python_path))} -m reddit_insights_agent.cli sync",
            "StandardOutput=append:%h/.local/state/reddit-product-insights/update.log",
            "StandardError=append:%h/.local/state/reddit-product-insights/update-error.log",
            "",
        ]
    )
    timer = "\n".join(
        [
            "[Unit]",
            "Description=Daily Reddit Product Insights data update",
            "",
            "[Timer]",
            f"OnCalendar=*-*-* {hour:02d}:00:00",
            "Persistent=true",
            "AccuracySec=5m",
            "Unit=reddit-product-insights-update.service",
            "",
            "[Install]",
            "WantedBy=timers.target",
            "",
        ]
    )
    return service, timer


def copy_agent(destination: pathlib.Path) -> pathlib.Path:
    agent_dir = destination / "agent"
    if PROJECT_ROOT.resolve() == agent_dir.resolve():
        return agent_dir
    if agent_dir.exists():
        shutil.rmtree(agent_dir)
    ignore = shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.pyc", "*.egg-info", "local-data")
    shutil.copytree(PROJECT_ROOT, agent_dir, dirs_exist_ok=True, ignore=ignore)
    return agent_dir


def create_environment(install_dir: pathlib.Path, agent_dir: pathlib.Path) -> pathlib.Path:
    venv = install_dir / ".venv"
    python_path = venv / "bin" / "python"
    if not python_path.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    subprocess.run([str(python_path), "-m", "pip", "install", "--quiet", str(agent_dir)], check=True)
    return python_path


def initial_sync(python_path: pathlib.Path, repo_url: str, data_dir: pathlib.Path) -> None:
    env = os.environ.copy()
    env.update(
        {
            "INSIGHTS_DATA_REPO_URL": repo_url,
            "INSIGHTS_DATA_BRANCH": "main",
            "INSIGHTS_LOCAL_DATA_DIR": str(data_dir),
            "INSIGHTS_DESKTOP_LOCAL_ONLY": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    try:
        subprocess.run(
            [str(python_path), "-m", "reddit_insights_agent.cli", "sync"],
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "The agent was installed, but the data repository could not be read. "
            "Public repositories need no GitHub account. For this private repository, "
            "authenticate Git with an approved GitHub account or a securely issued "
            "read-only credential, then run this installer again. Never place a token "
            "inside the ZIP or Claude configuration."
        ) from exc


def install_launchd(payload: dict[str, Any], home: pathlib.Path) -> pathlib.Path:
    data_dir = pathlib.Path(payload["EnvironmentVariables"]["INSIGHTS_LOCAL_DATA_DIR"])
    (data_dir / "logs").mkdir(parents=True, exist_ok=True)
    path = home / "Library" / "LaunchAgents" / f"{APP_ID}.plist"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        plistlib.dump(payload, stream)
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", domain, str(path)], check=False, capture_output=True)
    subprocess.run(["launchctl", "bootstrap", domain, str(path)], check=True)
    subprocess.run(["launchctl", "enable", f"{domain}/{APP_ID}"], check=True)
    return path


def install_systemd(service: str, timer: str, home: pathlib.Path) -> pathlib.Path:
    unit_dir = home / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    state_dir = home / ".local" / "state" / "reddit-product-insights"
    state_dir.mkdir(parents=True, exist_ok=True)
    service_path = unit_dir / "reddit-product-insights-update.service"
    timer_path = unit_dir / "reddit-product-insights-update.timer"
    service_path.write_text(service, encoding="utf-8")
    timer_path.write_text(timer, encoding="utf-8")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(
        ["systemctl", "--user", "enable", "--now", "reddit-product-insights-update.timer"],
        check=True,
    )
    return timer_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", default=DEFAULT_REPO)
    parser.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path.home() / "Documents" / "Nubra Product Insights")
    parser.add_argument("--install-dir", type=pathlib.Path)
    parser.add_argument("--claude-config", type=pathlib.Path)
    parser.add_argument("--hour", type=int, default=8)
    parser.add_argument("--no-schedule", action="store_true")
    args = parser.parse_args()

    platform = platform_name()
    if platform == "unsupported":
        raise SystemExit("This installer supports macOS and Linux. On Windows, use scripts/install_claude_desktop.ps1.")
    if not 0 <= args.hour <= 23:
        raise SystemExit("--hour must be between 0 and 23")
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 or newer is required.")
    if not shutil.which("git"):
        raise SystemExit("Git is required. Install Git, then run the setup again.")

    home = pathlib.Path.home()
    install_dir = (args.install_dir or default_install_dir(platform, home)).expanduser().resolve()
    data_dir = args.data_dir.expanduser().resolve()
    config_path = (args.claude_config or find_claude_config(platform, home)).expanduser().resolve()

    print(f"Installing Reddit Product Insights in {install_dir}")
    agent_dir = copy_agent(install_dir)
    python_path = create_environment(install_dir, agent_dir)
    initial_sync(python_path, args.repo_url, data_dir)
    backup = merge_claude_config(config_path, python_path, args.repo_url, data_dir)

    schedule_path = None
    if not args.no_schedule:
        if platform == "macos":
            schedule_path = install_launchd(
                launchd_payload(python_path, args.repo_url, data_dir, args.hour), home
            )
        else:
            service, timer = systemd_units(python_path, args.repo_url, data_dir, args.hour)
            schedule_path = install_systemd(service, timer, home)

    print("\nSetup complete.")
    print(f"Claude configuration: {config_path}")
    if backup:
        print(f"Configuration backup: {backup}")
    print(f"Local data: {data_dir}")
    if schedule_path:
        print(f"Daily updater: {schedule_path} ({args.hour:02d}:00 local time with catch-up)")
    print("Completely quit and reopen Claude Desktop, then enable reddit-product-insights.")


if __name__ == "__main__":
    main()
