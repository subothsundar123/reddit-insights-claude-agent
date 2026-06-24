#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
"$PYTHON" "$ROOT/scripts/setup_unix.py" "$@"
STATUS=$?
echo
if [ "$STATUS" -eq 0 ]; then
  echo "Installation finished. You can close this window."
else
  echo "Installation did not finish. Review the message above."
fi
read -r -p "Press Return to close..." _
exit "$STATUS"
