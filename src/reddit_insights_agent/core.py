from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import sqlite3
import subprocess
from collections import Counter, defaultdict
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]


def local_root() -> pathlib.Path:
    raw = os.getenv("INSIGHTS_LOCAL_DATA_DIR") or str(pathlib.Path.home() / "Documents" / "Nubra Product Insights")
    return pathlib.Path(os.path.expandvars(raw)).expanduser().resolve()


def _load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class Source:
    def __init__(self) -> None:
        local = os.getenv("INSIGHTS_DATA_REPO_PATH")
        self.local = pathlib.Path(local).expanduser().resolve() if local else None
        self.url = os.getenv("INSIGHTS_DATA_REPO_URL")
        self.branch = os.getenv("INSIGHTS_DATA_BRANCH", "main")
        self.cache = local_root() / ".data-repo-cache"
        self.warning: str | None = None
        if not self.local and not self.url:
            raise RuntimeError("Set INSIGHTS_DATA_REPO_PATH or INSIGHTS_DATA_REPO_URL")

    def refresh(self) -> None:
        if self.local:
            return
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        timeout = int(os.getenv("INSIGHTS_GIT_TIMEOUT_SECONDS", "20"))
        try:
            if not (self.cache / ".git").exists():
                self.cache.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["git", "clone", "--filter=blob:none", "--no-checkout", "--branch", self.branch, self.url, str(self.cache)],
                    check=True, timeout=timeout, stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                )
            else:
                subprocess.run(
                    ["git", "fetch", "--quiet", "origin", self.branch],
                    cwd=self.cache, check=True, timeout=timeout, stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
            if (self.cache / ".git").exists():
                self.warning = (
                    f"Git refresh did not complete within {timeout} seconds; "
                    "the latest verified local cache was used."
                )
            else:
                detail = getattr(exc, "stderr", b"")
                if isinstance(detail, bytes):
                    detail = detail.decode("utf-8", errors="replace")
                raise RuntimeError(
                    "Unable to initialize the private data repository. "
                    "Authenticate Git on this computer and retry. " + str(detail)
                ) from exc

    def bytes(self, rel: str) -> bytes:
        rel = rel.replace("\\", "/")
        if self.local:
            return (self.local / rel).read_bytes()
        result = subprocess.run(["git", "show", f"origin/{self.branch}:{rel}"], cwd=self.cache, check=True, capture_output=True)
        return result.stdout

    def json(self, rel: str) -> Any:
        return json.loads(self.bytes(rel).decode("utf-8-sig"))


def sync() -> dict[str, Any]:
    root = local_root(); root.mkdir(parents=True, exist_ok=True)
    source = Source(); source.refresh()
    state_path = root / "sync-state.json"
    state = _load(state_path) if state_path.exists() else {"dumps": [], "catalog_version": None}
    index = source.json("manifests/all_dumps.json")
    pulled = []
    for entry in index.get("dumps", []):
        date = entry["collection_date"]
        if date in state["dumps"]:
            continue
        manifest = source.json(entry["manifest"])
        for item in manifest["files"]:
            destination = root / "raw" / item["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.bytes(item["path"]))
            if _sha(destination) != item["sha256"]:
                destination.unlink(missing_ok=True)
                raise RuntimeError(f"Checksum mismatch for {item['path']}")
        local_manifest = root / "raw" / entry["manifest"]
        local_manifest.parent.mkdir(parents=True, exist_ok=True)
        local_manifest.write_bytes(source.bytes(entry["manifest"]))
        state["dumps"].append(date); pulled.append(date)

    catalog_manifest = source.json("product-catalog/manifest.json")
    if (catalog_manifest["current_version"] != state.get("catalog_version")
            or catalog_manifest["sha256"] != state.get("catalog_sha256")):
        destination = root / "catalog" / "current.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.bytes(catalog_manifest["path"]))
        if _sha(destination) != catalog_manifest["sha256"]:
            raise RuntimeError("Feature catalog checksum mismatch")
        state["catalog_version"] = catalog_manifest["current_version"]
        state["catalog_sha256"] = catalog_manifest["sha256"]
    state["dumps"] = sorted(set(state["dumps"]))
    state["last_checked_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    _write(state_path, state)
    import_local(root)
    return {"new_dumps": pulled, "available_through": max(state["dumps"]) if state["dumps"] else None,
            "catalog_version": state.get("catalog_version"), "local_folder": str(root),
            "warning": source.warning}


def connect(root: pathlib.Path | None = None) -> sqlite3.Connection:
    root = root or local_root(); root.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(root / "insights.sqlite3")
    db.row_factory = sqlite3.Row
    db.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS dumps(collection_date TEXT PRIMARY KEY, imported_at TEXT);
    CREATE TABLE IF NOT EXISTS posts(
      id TEXT PRIMARY KEY, collection_date TEXT, subreddit TEXT, segment TEXT, title TEXT, body TEXT,
      flair TEXT, score INTEGER, num_comments INTEGER, created_utc REAL, permalink TEXT,
      source_method TEXT, evidence_quality TEXT);
    CREATE TABLE IF NOT EXISTS comments(
      id TEXT, post_id TEXT, collection_date TEXT, body TEXT, score INTEGER, created_utc REAL,
      PRIMARY KEY(id, post_id));
    CREATE TABLE IF NOT EXISTS features(
      id TEXT PRIMARY KEY, name TEXT, category TEXT, status TEXT, availability TEXT,
      surfaces TEXT, aliases TEXT, notes TEXT, source TEXT);
    CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(kind, item_id, title, body, subreddit, collection_date);
    """)
    columns = {row[1] for row in db.execute("PRAGMA table_info(posts)")}
    if "source_method" not in columns:
        db.execute("ALTER TABLE posts ADD COLUMN source_method TEXT")
    if "evidence_quality" not in columns:
        db.execute("ALTER TABLE posts ADD COLUMN evidence_quality TEXT")
    db.execute("UPDATE posts SET source_method='reddit_collector' WHERE source_method IS NULL OR source_method=''")
    db.execute("UPDATE posts SET evidence_quality='direct_collection' WHERE evidence_quality IS NULL OR evidence_quality=''")
    db.commit()
    return db


def _segment(subreddit: str, text: str) -> str:
    api_terms = r"\b(api|sdk|websocket|socket|algo|algorithmic|automation|endpoint|python|developer|latency|backtest|strategy builder|order update)\b"
    return "api_algo" if subreddit.lower() == "indiaalgotrading" or re.search(api_terms, text, re.I) else "retail"


def import_local(root: pathlib.Path | None = None) -> None:
    root = root or local_root(); db = connect(root)
    state_path = root / "sync-state.json"
    if not state_path.exists(): return
    state = _load(state_path)
    for date in state.get("dumps", []):
        if db.execute("SELECT 1 FROM dumps WHERE collection_date=?", (date,)).fetchone(): continue
        folder = root / "raw" / "daily-dumps" / date
        with gzip.open(folder / "posts.jsonl.gz", "rt", encoding="utf-8") as f:
            for line in f:
                p = json.loads(line); text = f"{p.get('title','')} {p.get('body','')}"
                db.execute("""INSERT OR REPLACE INTO posts(
                    id, collection_date, subreddit, segment, title, body, flair, score,
                    num_comments, created_utc, permalink, source_method, evidence_quality
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                    p["id"], date, p.get("subreddit"), _segment(p.get("subreddit", ""), text),
                    p.get("title"), p.get("body"), p.get("flair"), p.get("score", 0),
                    p.get("num_comments", 0), p.get("created_utc"), p.get("permalink"),
                    p.get("source_method") or "reddit_collector",
                    p.get("evidence_quality") or "direct_collection"))
                db.execute("INSERT INTO evidence_fts VALUES(?,?,?,?,?,?)", ("post", p["id"], p.get("title"), p.get("body"), p.get("subreddit"), date))
        with gzip.open(folder / "comments.jsonl.gz", "rt", encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                db.execute("INSERT OR REPLACE INTO comments VALUES(?,?,?,?,?,?)", (
                    c["id"], c["post_id"], date, c.get("body"), c.get("score", 0), c.get("created_utc")))
                db.execute("INSERT INTO evidence_fts VALUES(?,?,?,?,?,?)", ("comment", c["id"], "", c.get("body"), "", date))
        db.execute("INSERT INTO dumps VALUES(?,?)", (date, dt.datetime.now(dt.timezone.utc).isoformat()))
    catalog = root / "catalog" / "current.json"
    if catalog.exists():
        db.execute("DELETE FROM features")
        for f in _load(catalog)["features"]:
            db.execute("INSERT INTO features VALUES(?,?,?,?,?,?,?,?,?)", (
                f["id"], f["name"], f.get("category"), f["status"], f.get("availability"),
                json.dumps(f.get("surfaces", [])), json.dumps(f.get("aliases", [])), f.get("notes"), json.dumps(f.get("source"))))
    db.commit(); db.close()


TOPICS = {
    "API reliability & WebSockets": ["websocket", "socket", "disconnect", "latency", "reconnect", "reliability"],
    "Historical data & backtesting": ["historical", "backtest", "backtesting", "candle", "tick data"],
    "Strategy building & automation": ["strategy builder", "strategy", "automation", "algo", "no-code", "signal"],
    "Options analytics & risk": ["option", "greeks", "payoff", "margin", "slippage", "liquidity", "open interest", " oi "],
    "Order execution & OMS": ["order", "execution", "fill", "stop loss", "trailing", "basket", "multi-leg"],
    "Market news & sentiment": ["news", "sentiment", "event", "announcement"],
    "Developer onboarding": ["documentation", "docs", "example", "authentication", "totp", "static ip", "support"],
    "Portfolio & P&L analytics": ["p&l", "pnl", "portfolio", "tradebook", "charges", "brokerage"],
    "Investment education": ["learn", "beginner", "how to", "education", "knowledge"],
}
REQUEST = re.compile(r"\b(need|want|wish|request|missing|looking for|would like|should have|feature|support for|can we|is there an api)\b", re.I)


def _engagement(score: int, comments: int) -> float:
    return round(math.log1p(max(score, 0)) + 0.6 * math.log1p(max(comments, 0)), 3)


def _range_clause(days: int | None) -> tuple[str, list[Any]]:
    if not days: return "", []
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    return " WHERE collection_date >= ?", [cutoff]


def search(query: str, limit: int = 20) -> list[dict[str, Any]]:
    db = connect()
    safe = " OR ".join(re.findall(r"[\w-]+", query)) or query
    rows = db.execute(
        """SELECT kind, item_id, title,
                  snippet(evidence_fts, 3, '[', ']', ' ... ', 45) AS excerpt,
                  subreddit, collection_date, bm25(evidence_fts) AS rank
           FROM evidence_fts
           WHERE evidence_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (safe, min(max(limit, 1), 50)),
    ).fetchall()
    result = []
    seen_items: set[tuple[str, str]] = set()
    for row in rows:
        item = dict(row)
        identity = (item["kind"], item["item_id"])
        if identity in seen_items:
            continue
        seen_items.add(identity)
        if item["kind"] == "post":
            post = db.execute(
                "SELECT permalink, score, num_comments, segment, source_method FROM posts WHERE id=?",
                (item["item_id"],),
            ).fetchone()
            if post:
                item.update(dict(post))
        result.append(item)
    db.close()
    return result


def feature_lookup(query: str) -> list[dict[str, Any]]:
    db = connect(); needle = query.lower(); found = []
    for row in db.execute("SELECT * FROM features"):
        aliases = json.loads(row["aliases"])
        if needle in row["name"].lower() or any(needle in str(a).lower() for a in aliases): found.append(dict(row))
    db.close(); return found


def analyze(days: int | None = 30) -> dict[str, Any]:
    db = connect(); clause, params = _range_clause(days)
    posts = [dict(r) for r in db.execute("SELECT * FROM posts" + clause, params)]
    features = [dict(r) for r in db.execute("SELECT * FROM features")]
    db.close()
    topic_rows: dict[str, dict[str, Any]] = {}
    feature_rows: dict[str, dict[str, Any]] = {}
    evidence = []
    for p in posts:
        text = f"{p['title']} {p['body']}".lower(); weight = _engagement(p["score"], p["num_comments"])
        technical_only = {
            "API reliability & WebSockets",
            "Historical data & backtesting",
            "Strategy building & automation",
            "Order execution & OMS",
            "Developer onboarding",
        }
        matched_topics = [
            name for name, keys in TOPICS.items()
            if (name not in technical_only or p["segment"] == "api_algo")
            and any(k in text for k in keys)
        ] or ["Other market discussion"]
        for name in matched_topics:
            item = topic_rows.setdefault(name, {"topic": name, "mentions": 0, "engagement": 0.0, "retail": 0, "api_algo": 0, "examples": []})
            item["mentions"] += 1; item["engagement"] += weight; item[p["segment"]] += 1
            if len(item["examples"]) < 3: item["examples"].append({"title": p["title"], "subreddit": p["subreddit"], "url": p["permalink"]})
        # Product-demand ranking is intentionally restricted to API/algo-context
        # posts. Retail investment language such as "funds" or "orders" otherwise
        # creates false matches against API capability names.
        if p["segment"] == "api_algo" and REQUEST.search(text):
            for f in features:
                aliases = [f["name"]] + json.loads(f["aliases"])
                if any(str(a).lower() in text for a in aliases if len(str(a)) >= 4):
                    item = feature_rows.setdefault(f["id"], {"feature": f["name"], "status": f["status"], "mentions": 0, "engagement": 0.0, "examples": []})
                    item["mentions"] += 1; item["engagement"] += weight
                    if len(item["examples"]) < 3: item["examples"].append({"title": p["title"], "url": p["permalink"]})
        evidence.append((weight, p))
    topics = sorted(topic_rows.values(), key=lambda x: (x["mentions"], x["engagement"]), reverse=True)
    requested = sorted(feature_rows.values(), key=lambda x: (x["mentions"], x["engagement"]), reverse=True)
    for row in topics + requested: row["engagement"] = round(row["engagement"], 2)
    top_evidence = [{"title": p["title"], "segment": p["segment"], "score": p["score"], "comments": p["num_comments"], "url": p["permalink"]} for _, p in sorted(evidence, key=lambda item: item[0], reverse=True)[:15]]
    source_counts = Counter(p.get("source_method") or "unknown" for p in posts)
    direct_count = sum(v for k, v in source_counts.items() if k != "web_search_review")
    confidence = "high" if direct_count >= 200 else "medium" if direct_count >= 50 else "low"
    return {"period_days": days, "sample": {
                "posts": len(posts), "direct_posts": direct_count,
                "web_research_summaries": source_counts.get("web_search_review", 0),
                "source_methods": dict(source_counts), "confidence": confidence
            }, "methodology_note": (
                "Web-search research summaries have unknown Reddit vote metrics. "
                "They increase thematic coverage and mention frequency but add zero engagement weight."
            ), "topics": topics[:12],
            "feature_requests": requested[:15], "top_evidence": top_evidence}


def _roadmap_action(status: str) -> str:
    return {"available": "Awareness/docs/adoption", "upcoming": "Validate release status and readiness", "partial": "Close scope/access gaps",
            "internal_unverified": "Confirm ownership and public exposure", "not_available": "Evaluate for discovery/roadmap"}.get(status, "Investigate")


def daily_insights(days: int = 30) -> dict[str, Any]:
    sync_result = sync(); data = analyze(days)
    webinars = []
    actionable_topics = [t for t in data["topics"] if t["topic"] != "Other market discussion"]
    for t in actionable_topics[:6]:
        webinars.append({"topic": t["topic"], "why_now": f"{t['mentions']} matched discussions; engagement {t['engagement']}",
                         "audience": "API/algo" if t["api_algo"] >= t["retail"] else "Retail", "format": "Demo + Q&A"})
    roadmap = []
    for f in data["feature_requests"][:10]:
        roadmap.append({**f, "recommended_action": _roadmap_action(f["status"])})
    available_requests = [x for x in roadmap if x["status"] == "available"]
    report = render_markdown(sync_result, data, webinars, roadmap, available_requests)
    report_dir = local_root() / "reports"; report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"daily-insights-{dt.date.today().isoformat()}.md"; path.write_text(report, encoding="utf-8")
    return {"sync": sync_result, "analysis": data, "webinars": webinars, "roadmap": roadmap,
            "awareness_gaps": available_requests, "report_markdown": report, "report_path": str(path),
            "available_commands": ["/api-insights", "/retail-insights", "/feature-demand", "/webinar-plan", "/product-roadmap", "/awareness-gaps", "/strategy-builder", "/competitor-insights", "/evidence", "/compare-periods"]}


def render_markdown(sync_result, data, webinars, roadmap, awareness) -> str:
    lines = ["# Daily Reddit Product Insights", "", f"Data available through: **{sync_result['available_through']}** · New dumps pulled: **{len(sync_result['new_dumps'])}** · Catalog: **{sync_result['catalog_version']}**", "",
             f"Sample: **{data['sample']['posts']} posts** · Confidence: **{data['sample']['confidence']}**", "", "## Executive summary", ""]
    executive_topics = [t for t in data["topics"] if t["topic"] != "Other market discussion"][:5]
    for t in executive_topics: lines.append(f"- **{t['topic']}** — {t['mentions']} discussions; retail {t['retail']}, API/algo {t['api_algo']}.")
    lines += ["", "## Retail vs API/algo hot topics", "", "| Topic | Mentions | Retail | API/algo | Engagement |", "|---|---:|---:|---:|---:|"]
    for t in data["topics"][:10]: lines.append(f"| {t['topic']} | {t['mentions']} | {t['retail']} | {t['api_algo']} | {t['engagement']} |")
    lines += ["", "## Most requested capabilities", "", "| Capability | Nubra status | Mentions | Product response |", "|---|---|---:|---|"]
    if roadmap:
        for f in roadmap: lines.append(f"| {f['feature']} | {f['status']} | {f['mentions']} | {f['recommended_action']} |")
    else: lines.append("| No high-confidence explicit feature request matched | — | — | Expand collection window or inspect evidence |")
    lines += ["", "## Webinar opportunities", ""]
    for w in webinars: lines.append(f"- **{w['topic']}** — {w['audience']}; {w['why_now']}.")
    lines += ["", "## Product roadmap signals", ""]
    for f in roadmap[:6]: lines.append(f"- **{f['feature']}**: {f['recommended_action']} ({f['status']}).")
    lines += ["", "## Awareness and documentation gaps", ""]
    if awareness:
        for f in awareness: lines.append(f"- **{f['feature']}** is already available but still requested: improve discovery, examples, webinar coverage, and in-product guidance.")
    else: lines.append("- No strong available-but-requested match in this window.")
    lines += ["", "## Evidence and caveats", "", "Reddit score is a platform-provided net-vote signal, not unique users or demand by itself. Ranking combines frequency with log-scaled score/comment engagement. Treat low-volume signals as discovery inputs, not roadmap commitments.", "", "## Drill-down commands", "",
              "`/api-insights` · `/retail-insights` · `/feature-demand` · `/webinar-plan` · `/product-roadmap` · `/awareness-gaps` · `/strategy-builder` · `/competitor-insights` · `/evidence` · `/compare-periods`", ""]
    return "\n".join(lines)


def compare_periods(days_a: int = 7, days_b: int = 30) -> dict[str, Any]:
    return {f"last_{days_a}_days": analyze(days_a), f"last_{days_b}_days": analyze(days_b)}
