import argparse
import json
import sys
from .core import ask_insights, connector_status, daily_insights, sync

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="command", required=True)
    sync_parser = s.add_parser("sync")
    sync_parser.add_argument("--force", action="store_true")
    d = s.add_parser("daily-insights")
    d.add_argument("--days", type=int, default=30)
    d.add_argument("--no-cache", action="store_true")
    status = s.add_parser("status")
    status.add_argument("--refresh", action="store_true")
    ask = s.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--days", type=int, default=30)
    a = p.parse_args()
    if a.command == "sync":
        result = sync(force_remote=a.force)
    elif a.command == "daily-insights":
        result = daily_insights(a.days, use_cache=not a.no_cache)
    elif a.command == "status":
        result = connector_status(refresh=a.refresh)
    else:
        result = ask_insights(a.question, a.days)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__": main()
