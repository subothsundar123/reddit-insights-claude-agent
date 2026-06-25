#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${INSIGHTS_AGENT_PYTHON:-$ROOT/.venv/bin/python}"
DATA_DIR="${INSIGHTS_LOCAL_DATA_DIR:-$HOME/Documents/Nubra Product Insights}"
REPO_URL="${INSIGHTS_DATA_REPO_URL:-https://github.com/subothsundar123/reddit-scraper-github-publisher.git}"

if [ ! -x "$PYTHON" ]; then
  BASE_PYTHON="${PYTHON_BIN:-python3}"
  "$BASE_PYTHON" -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/python" -m pip install --quiet --upgrade pip
  "$ROOT/.venv/bin/python" -m pip install --quiet -e "$ROOT"
  PYTHON="$ROOT/.venv/bin/python"
fi

INSIGHTS_DATA_REPO_URL="$REPO_URL" \
INSIGHTS_DATA_BRANCH="${INSIGHTS_DATA_BRANCH:-main}" \
INSIGHTS_LOCAL_DATA_DIR="$DATA_DIR" \
INSIGHTS_DESKTOP_LOCAL_ONLY=0 \
GIT_TERMINAL_PROMPT=0 \
"$PYTHON" -m reddit_insights_agent.cli sync
