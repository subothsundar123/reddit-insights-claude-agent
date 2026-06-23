import argparse
import json
from .core import daily_insights, sync

def main() -> None:
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="command", required=True)
    s.add_parser("sync"); d = s.add_parser("daily-insights"); d.add_argument("--days", type=int, default=30)
    a = p.parse_args()
    result = sync() if a.command == "sync" else daily_insights(a.days)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__": main()
