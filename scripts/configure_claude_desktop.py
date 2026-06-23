from __future__ import annotations

import argparse
import json
import pathlib
import shutil
from datetime import datetime


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=pathlib.Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--local-data-dir", required=True)
    args = parser.parse_args()

    args.config.parent.mkdir(parents=True, exist_ok=True)
    if args.config.exists():
        backup = args.config.with_name(
            f"{args.config.name}.backup-{datetime.now():%Y%m%d-%H%M%S}"
        )
        shutil.copy2(args.config, backup)
        raw = args.config.read_text(encoding="utf-8-sig").strip()
        config = json.loads(raw) if raw else {}
    else:
        config = {}

    servers = config.setdefault("mcpServers", {})
    servers["reddit-product-insights"] = {
        "command": args.python,
        "args": ["-m", "reddit_insights_agent.server"],
        "env": {
            "INSIGHTS_DATA_REPO_URL": args.repo_url,
            "INSIGHTS_DATA_BRANCH": "main",
            "INSIGHTS_LOCAL_DATA_DIR": args.local_data_dir,
        },
    }
    args.config.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

