#!/usr/bin/env python3
"""Set up Reddit Product Insights for Claude Code on Linux/macOS."""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys


DEFAULT_REPO = "https://github.com/subothsundar123/reddit-scraper-github-publisher.git"
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(command: list[str], **kwargs) -> None:
    subprocess.run(command, check=True, **kwargs)


def create_environment() -> pathlib.Path:
    venv = PROJECT_ROOT / ".venv"
    python_path = venv / "bin" / "python"
    if not python_path.exists():
        run([sys.executable, "-m", "venv", str(venv)])
    run([str(python_path), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    run([str(python_path), "-m", "pip", "install", "--quiet", "-e", str(PROJECT_ROOT)])
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
    run([str(python_path), "-m", "reddit_insights_agent.cli", "sync"], env=env)


def install_systemd_timer(hour: int) -> pathlib.Path | None:
    if not shutil.which("systemctl"):
        return None
    unit_dir = pathlib.Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    service_path = unit_dir / "reddit-product-insights-update.service"
    timer_path = unit_dir / "reddit-product-insights-update.timer"
    refresh = PROJECT_ROOT / "scripts" / "refresh-data.sh"
    service_path.write_text(
        "\n".join(
            [
                "[Unit]",
                "Description=Refresh Reddit Product Insights local dumps",
                "After=network-online.target",
                "Wants=network-online.target",
                "",
                "[Service]",
                "Type=oneshot",
                f"WorkingDirectory={PROJECT_ROOT}",
                f"ExecStart=/usr/bin/env bash {refresh}",
                "StandardOutput=append:%h/.local/state/reddit-product-insights/update.log",
                "StandardError=append:%h/.local/state/reddit-product-insights/update-error.log",
                "",
            ]
        ),
        encoding="utf-8",
    )
    timer_path.write_text(
        "\n".join(
            [
                "[Unit]",
                "Description=Daily Reddit Product Insights refresh",
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
        ),
        encoding="utf-8",
    )
    (pathlib.Path.home() / ".local" / "state" / "reddit-product-insights").mkdir(parents=True, exist_ok=True)
    run(["systemctl", "--user", "daemon-reload"])
    run(["systemctl", "--user", "enable", "--now", "reddit-product-insights-update.timer"])
    return timer_path


def install_cron(hour: int) -> bool:
    if not shutil.which("crontab"):
        return False
    refresh = PROJECT_ROOT / "scripts" / "refresh-data.sh"
    marker = "# reddit-product-insights-update"
    try:
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False).stdout
    except Exception:
        current = ""
    lines = [line for line in current.splitlines() if marker not in line]
    lines.append(f"0 {hour} * * * /usr/bin/env bash {refresh} {marker}")
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", default=DEFAULT_REPO)
    parser.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path.home() / "Documents" / "Nubra Product Insights")
    parser.add_argument("--hour", type=int, default=8)
    parser.add_argument("--no-schedule", action="store_true")
    args = parser.parse_args()

    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 or newer is required.")
    if not 0 <= args.hour <= 23:
        raise SystemExit("--hour must be between 0 and 23")

    data_dir = args.data_dir.expanduser().resolve()
    print("Setting up Reddit Product Insights for Claude Code")
    print(f"Project folder: {PROJECT_ROOT}")
    print(f"Local data folder: {data_dir}")

    python_path = create_environment()
    initial_sync(python_path, args.repo_url, data_dir)

    schedule = "not installed"
    if not args.no_schedule:
        timer_path = install_systemd_timer(args.hour)
        if timer_path:
            schedule = f"systemd user timer: {timer_path}"
        elif install_cron(args.hour):
            schedule = f"cron job at {args.hour:02d}:00"
        else:
            schedule = "not installed because systemd user timers and crontab were unavailable"

    print("\nSetup complete.")
    print(f"Python environment: {python_path}")
    print(f"Local data folder: {data_dir}")
    print(f"Daily updater: {schedule}")
    print("\nNext step:")
    print("1. Open this folder in terminal.")
    print("2. Run: claude")
    print("3. Type: /daily-insights")


if __name__ == "__main__":
    main()
