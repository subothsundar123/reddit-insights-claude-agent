import argparse
from .core import daily_insights, sync

def main() -> None:
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="command", required=True)
    s.add_parser("sync"); d = s.add_parser("daily-insights"); d.add_argument("--days", type=int, default=30)
    a = p.parse_args()
    result = sync() if a.command == "sync" else daily_insights(a.days)
    print(result if a.command == "sync" else result["report_markdown"])

if __name__ == "__main__": main()
