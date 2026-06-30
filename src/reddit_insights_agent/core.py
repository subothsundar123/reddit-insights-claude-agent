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
import tempfile
import urllib.request
import zipfile
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONNECTOR_VERSION = "2.2.0"
CACHE_SCHEMA_VERSION = 1
DEFAULT_SYNC_MAX_AGE_HOURS = 6


def local_root() -> pathlib.Path:
    raw = os.getenv("INSIGHTS_LOCAL_DATA_DIR") or str(pathlib.Path.home() / "Documents" / "Nubra Product Insights")
    return pathlib.Path(os.path.expandvars(raw)).expanduser().resolve()


def _load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _state_age_hours(state: dict[str, Any]) -> float | None:
    value = state.get("last_checked_at")
    if not value:
        return None
    try:
        checked = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if checked.tzinfo is None:
            checked = checked.replace(tzinfo=dt.timezone.utc)
        return max(0.0, (dt.datetime.now(dt.timezone.utc) - checked).total_seconds() / 3600)
    except (TypeError, ValueError):
        return None


def _dump_issues(root: pathlib.Path, collection_date: str) -> list[str]:
    folder = root / "raw" / "daily-dumps" / collection_date
    manifest_path = folder / "manifest.json"
    issues = []
    for filename in ("posts.jsonl.gz", "comments.jsonl.gz", "manifest.json"):
        if not (folder / filename).exists():
            issues.append(f"{collection_date}/{filename} is missing")
    if not manifest_path.exists():
        return issues
    try:
        manifest = _load(manifest_path)
        for item in manifest.get("files", []):
            path = root / "raw" / item["path"]
            if not path.exists():
                issues.append(f"{item['path']} is missing")
            elif item.get("sha256") and _sha(path) != item["sha256"]:
                issues.append(f"{item['path']} checksum does not match")
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        issues.append(f"{collection_date}/manifest.json is unreadable")
    return list(dict.fromkeys(issues))


def _local_data_health(root: pathlib.Path) -> dict[str, Any]:
    issues: list[str] = []
    state_path = root / "sync-state.json"
    state: dict[str, Any] = {}
    if not state_path.exists():
        issues.append("sync-state.json is missing")
    else:
        try:
            state = _load(state_path)
        except (OSError, json.JSONDecodeError, TypeError):
            issues.append("sync-state.json is unreadable")

    dumps = sorted(set(state.get("dumps", []))) if isinstance(state.get("dumps", []), list) else []
    if not dumps:
        issues.append("no data dumps are registered")
    for collection_date in dumps:
        issues.extend(_dump_issues(root, str(collection_date)))

    catalog = root / "catalog" / "current.json"
    if not catalog.exists():
        issues.append("feature catalog is missing")
    else:
        expected = state.get("catalog_sha256")
        if expected:
            try:
                if _sha(catalog) != expected:
                    issues.append("feature catalog checksum does not match")
            except OSError:
                issues.append("feature catalog cannot be read")
        try:
            payload = _load(catalog)
            if not isinstance(payload.get("features"), list):
                issues.append("feature catalog has an invalid structure")
        except (OSError, json.JSONDecodeError, TypeError, AttributeError):
            issues.append("feature catalog is unreadable")

    return {
        "healthy": not issues,
        "issues": issues,
        "state": state,
        "latest_dump": max(dumps) if dumps else None,
        "dump_count": len(dumps),
        "state_age_hours": _state_age_hours(state),
    }


def _local_sync_result(root: pathlib.Path, health: dict[str, Any], mode: str, warning: str | None = None) -> dict[str, Any]:
    state = health.get("state", {})
    return {
        "new_dumps": [],
        "available_through": health.get("latest_dump"),
        "catalog_version": state.get("catalog_version"),
        "local_folder": str(root),
        "warning": warning,
        "mode": mode,
        "last_checked_at": state.get("last_checked_at"),
        "health": "healthy" if health.get("healthy") else "needs_repair",
    }


class Source:
    def __init__(self) -> None:
        local = os.getenv("INSIGHTS_DATA_REPO_PATH")
        self.local = pathlib.Path(local).expanduser().resolve() if local else None
        self.url = os.getenv("INSIGHTS_DATA_REPO_URL")
        self.branch = os.getenv("INSIGHTS_DATA_BRANCH", "main")
        self.cache = local_root() / ".data-repo-cache"
        self.zip_cache = local_root() / ".data-repo-zip"
        self.warning: str | None = None
        if not self.local and not self.url:
            raise RuntimeError("Set INSIGHTS_DATA_REPO_PATH or INSIGHTS_DATA_REPO_URL")

    def _zip_url(self) -> str | None:
        if not self.url:
            return None
        match = re.match(r"https://github\.com/([^/]+)/([^/.]+?)(?:\.git)?/?$", self.url)
        if not match:
            return None
        owner, repo = match.groups()
        return f"https://github.com/{owner}/{repo}/archive/refs/heads/{self.branch}.zip"

    def _download_zip_cache(self) -> None:
        zip_url = self._zip_url()
        if not zip_url:
            raise RuntimeError("ZIP fallback only supports public GitHub HTTPS repositories.")
        self.zip_cache.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            archive = tmp_path / "repo.zip"
            urllib.request.urlretrieve(zip_url, archive)
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(tmp_path / "extract")
            roots = [p for p in (tmp_path / "extract").iterdir() if p.is_dir()]
            if not roots:
                raise RuntimeError("Downloaded GitHub ZIP did not contain a repository folder.")
            if self.zip_cache.exists():
                shutil.rmtree(self.zip_cache)
            shutil.move(str(roots[0]), str(self.zip_cache))
        self.local = self.zip_cache
        self.warning = "Git was unavailable or failed, so the public GitHub ZIP feed was used."

    def refresh(self) -> None:
        if self.local:
            return
        if not shutil.which("git"):
            self._download_zip_cache()
            return
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GCM_INTERACTIVE"] = "Never"
        env["GIT_ASKPASS"] = "echo"
        env["SSH_ASKPASS"] = "echo"
        timeout = int(os.getenv("INSIGHTS_GIT_TIMEOUT_SECONDS", "20"))
        try:
            if not (self.cache / ".git").exists():
                self.cache.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["git", "clone", "--filter=blob:none", "--no-checkout", "--branch", self.branch, self.url, str(self.cache)],
                    check=True, timeout=timeout, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
                )
            else:
                subprocess.run(
                    ["git", "remote", "set-url", "origin", self.url],
                    cwd=self.cache, check=True, timeout=timeout, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
                )
                subprocess.run(
                    ["git", "fetch", "--quiet", "origin", self.branch],
                    cwd=self.cache, check=True, timeout=timeout, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
                )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
            if (self.cache / ".git").exists():
                self.warning = (
                    f"Git refresh did not complete within {timeout} seconds; "
                    "the latest verified local cache was used."
                )
            else:
                try:
                    self._download_zip_cache()
                except Exception as zip_exc:
                    raise RuntimeError(
                        "Unable to initialize the data repository through Git or public ZIP download. "
                        "If the repository is private, authenticate Git on this computer and retry."
                    ) from zip_exc

    def bytes(self, rel: str) -> bytes:
        rel = rel.replace("\\", "/")
        if self.local:
            return (self.local / rel).read_bytes()
        result = subprocess.run(["git", "show", f"origin/{self.branch}:{rel}"], cwd=self.cache, check=True, capture_output=True)
        return result.stdout

    def json(self, rel: str) -> Any:
        return json.loads(self.bytes(rel).decode("utf-8-sig"))


def sync(force_remote: bool = False) -> dict[str, Any]:
    """Validate local data, refresh it when needed, and repair incomplete state.

    A healthy recent local snapshot is used immediately. A stale or damaged
    snapshot is refreshed even when Desktop local-only mode is configured.
    If the network is unavailable, a healthy local snapshot remains usable.
    """
    root = local_root()
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / "sync-state.json"
    local_only = os.getenv("INSIGHTS_DESKTOP_LOCAL_ONLY", "").lower() in {"1", "true", "yes"}
    try:
        max_age_hours = max(0.0, float(os.getenv("INSIGHTS_SYNC_MAX_AGE_HOURS", DEFAULT_SYNC_MAX_AGE_HOURS)))
    except ValueError:
        max_age_hours = float(DEFAULT_SYNC_MAX_AGE_HOURS)

    health = _local_data_health(root)
    age = health.get("state_age_hours")
    recent = age is not None and age <= max_age_hours
    if not force_remote and health["healthy"] and recent:
        import_local(root)
        return _local_sync_result(
            root,
            health,
            "local_files_only" if local_only else "cached_local",
        )

    # Local-only remains the normal fast path, but stale or broken local data
    # is allowed to self-repair from the configured public source.
    if local_only and health["healthy"] and not force_remote and not os.getenv("INSIGHTS_DATA_REPO_URL") and not os.getenv("INSIGHTS_DATA_REPO_PATH"):
        import_local(root)
        return _local_sync_result(root, health, "local_files_only", "Remote source is not configured.")

    try:
        source = Source()
        source.refresh()
        try:
            state = _load(state_path) if state_path.exists() else {"dumps": [], "catalog_version": None}
        except (OSError, json.JSONDecodeError, TypeError):
            state = {"dumps": [], "catalog_version": None}
        state.setdefault("dumps", [])

        # A dump is considered synchronized only while all required local
        # files exist. Removing the state entry lets the normal download loop
        # restore a partial or accidentally deleted dump.
        valid_dumps = []
        for collection_date in sorted(set(state.get("dumps", []))):
            if not _dump_issues(root, str(collection_date)):
                valid_dumps.append(collection_date)
        state["dumps"] = valid_dumps

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
            state["dumps"].append(date)
            pulled.append(date)

        catalog_manifest = source.json("product-catalog/manifest.json")
        destination = root / "catalog" / "current.json"
        catalog_valid = (
            destination.exists()
            and state.get("catalog_sha256") == catalog_manifest.get("sha256")
            and _sha(destination) == catalog_manifest.get("sha256")
        )
        if (
            catalog_manifest["current_version"] != state.get("catalog_version")
            or not catalog_valid
        ):
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.bytes(catalog_manifest["path"]))
            if _sha(destination) != catalog_manifest["sha256"]:
                destination.unlink(missing_ok=True)
                raise RuntimeError("Feature catalog checksum mismatch")
            state["catalog_version"] = catalog_manifest["current_version"]
            state["catalog_sha256"] = catalog_manifest["sha256"]

        state["dumps"] = sorted(set(state["dumps"]))
        state["last_checked_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        _write(state_path, state)
        import_local(root)
        repaired_health = _local_data_health(root)
        if not repaired_health["healthy"]:
            raise RuntimeError("Local data validation failed after refresh: " + "; ".join(repaired_health["issues"]))
        return {
            "new_dumps": pulled,
            "available_through": max(state["dumps"]) if state["dumps"] else None,
            "catalog_version": state.get("catalog_version"),
            "local_folder": str(root),
            "warning": source.warning,
            "mode": "github_sync",
            "last_checked_at": state.get("last_checked_at"),
            "health": "healthy",
        }
    except Exception as exc:
        fallback = _local_data_health(root)
        if fallback["healthy"]:
            import_local(root)
            return _local_sync_result(
                root,
                fallback,
                "degraded_local",
                f"Remote refresh failed; using the last verified local data. {type(exc).__name__}: {exc}",
            )
        raise RuntimeError(
            "Insights data is incomplete and automatic repair failed. "
            f"Problems: {', '.join(fallback['issues'])}. Refresh error: {exc}"
        ) from exc


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


def _normalize_segment(segment: str | None, channel: str, text: str) -> str:
    raw = (segment or "").lower()
    if raw == "api_algo":
        return "api_algo"
    if raw.startswith("retail"):
        return "retail"
    return _segment(channel, text)


def _signal_score(signal: dict[str, Any]) -> int:
    engagement = signal.get("engagement") or {}
    total = 0
    for key in ("score", "points", "reactions", "likes", "reposts", "stars"):
        try:
            total += int(float(engagement.get(key) or 0))
        except (TypeError, ValueError):
            continue
    return total


def _signal_comments(signal: dict[str, Any]) -> int:
    engagement = signal.get("engagement") or {}
    try:
        return int(float(engagement.get("comments") or 0))
    except (TypeError, ValueError):
        return 0


def _signal_created_utc(signal: dict[str, Any]) -> float | None:
    value = signal.get("created_at")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value:
        try:
            normalized = value.replace("Z", "+00:00")
            return dt.datetime.fromisoformat(normalized).timestamp()
        except ValueError:
            return None
    return None


def import_local(root: pathlib.Path | None = None) -> None:
    root = root or local_root(); db = connect(root)
    state_path = root / "sync-state.json"
    if not state_path.exists(): return
    state = _load(state_path)
    for date in state.get("dumps", []):
        folder = root / "raw" / "daily-dumps" / date
        imported = db.execute("SELECT 1 FROM dumps WHERE collection_date=?", (date,)).fetchone()
        if not imported:
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
        signal_path = folder / "signals.jsonl.gz"
        if signal_path.exists():
            with gzip.open(signal_path, "rt", encoding="utf-8") as f:
                for line in f:
                    s = json.loads(line)
                    signal_id = "sig_" + str(s.get("id"))
                    if db.execute("SELECT 1 FROM posts WHERE id=?", (signal_id,)).fetchone():
                        continue
                    channel = f"{s.get('source') or 'public_signal'}:{s.get('channel') or 'unknown'}"
                    text = f"{s.get('title','')} {s.get('body','')}"
                    db.execute("""INSERT OR REPLACE INTO posts(
                        id, collection_date, subreddit, segment, title, body, flair, score,
                        num_comments, created_utc, permalink, source_method, evidence_quality
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                        signal_id, date, channel, _normalize_segment(s.get("segment"), channel, text),
                        s.get("title"), s.get("body"), ",".join(s.get("tags") or []),
                        _signal_score(s), _signal_comments(s), _signal_created_utc(s), s.get("url"),
                        s.get("source_method") or "public_signal_collector",
                        s.get("evidence_quality") or "public_signal"))
                    db.execute("INSERT INTO evidence_fts VALUES(?,?,?,?,?,?)", ("signal", signal_id, s.get("title"), s.get("body"), channel, date))
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
    "Market data & data quality": ["market data", "live data", "real-time data", "realtime data", "data feed", "data quality", "stale data", "missing candle", "ohlc", "quote api"],
    "Fundamental data & research": ["fundamental", "financial statement", "balance sheet", "earnings data", "valuation", "pe ratio", "financials", "research api"],
    "Scanners, indicators & alerts": ["scanner", "screener", "indicator", "rsi", "macd", "alert", "notification", "watchlist"],
    "Paper trading & UAT": ["paper trading", "paper trade", "sandbox", "uat", "test environment", "mock trading", "virtual trading"],
    "Funds, margin & settlement": ["funds", "collateral", "pledge", "settlement", "margin shortfall", "buying power", "cash balance"],
    "SDK, MCP & integrations": ["sdk", "python library", "javascript library", "webhook", "mcp", "ai integration", "open source", "integration"],
    "Security, sessions & access": ["2fa", "totp", "static ip", "secondary ip", "multi-session", "session", "login flow", "rate limit"],
    "Pricing, brokerage & taxes": ["brokerage", "charges", "pricing", "subscription", "transaction cost", "stt", "gst", "stamp duty", "tax calculator"],
    "Instrument & reference data": ["instrument master", "symbol mapping", "instrument token", "contract master", "lot size", "strike price", "expiry data", "exchange segment"],
    "Platform usability & support": ["user interface", "mobile app", "dashboard", "feature discovery", "chatbot", "support ticket", "customer support", "navigation"],
    "YouTube retail and API signals": ["youtube", "video", "comment", "creator", "channel", "views per day", "comments per day"],
}

PRODUCT_DISCOVERY_TERMS = {
    "api", "sdk", "mcp", "data", "feed", "websocket", "order", "execution", "margin",
    "portfolio", "analytics", "scanner", "screener", "indicator", "alert", "integration",
    "automation", "backtest", "broker", "platform", "dashboard", "documentation", "support",
    "login", "session", "security", "research", "fundamental", "option", "risk", "pricing",
}

COMPETITORS = {
    "Zerodha": ["zerodha", "kite connect", "kite api"],
    "Upstox": ["upstox"],
    "Angel One": ["angel one", "smartapi", "smart api"],
    "Fyers": ["fyers"],
    "Dhan": ["dhan", "dhanhq"],
    "Shoonya": ["shoonya", "finvasia"],
    "Alice Blue": ["alice blue", "ant api"],
    "5paisa": ["5paisa", "5 paisa"],
    "ICICI Direct": ["icici direct", "breeze api"],
    "Kotak Neo": ["kotak neo", "kotak securities"],
    "Groww": ["groww"],
    "Flattrade": ["flattrade"],
    "Tradetron": ["tradetron"],
    "Streak": ["streak"],
    "AlgoTest": ["algotest", "algo test"],
    "Sensibull": ["sensibull"],
    "Nubra": ["nubra", "zanskar"],
}

PRODUCT_PLAYBOOK = {
    "API reliability & WebSockets": {
        "product_thinking": "Reliability is part of the API product, not only an infrastructure metric. Visible health and predictable recovery improve developer trust.",
        "nubra_context": "Realtime WebSocket streams are available; public reliability visibility is a gap.",
        "solution": "Create a public WebSocket health dashboard with uptime, latency, incident history and stream-level status. Add reconnect, heartbeat and recovery examples to the SDK.",
        "webinar": "Building resilient trading systems with WebSockets",
        "horizon": "Now"
    },
    "Historical data & backtesting": {
        "product_thinking": "Users cannot confidently adopt backtesting until they understand coverage, adjustments, expiry handling and data-quality assumptions.",
        "nubra_context": "Basic historical APIs and NubraOSS backtesting exist, but availability and coverage need clearer discovery.",
        "solution": "Publish a historical-data coverage directory by asset, interval and earliest date. Add an availability endpoint and requirement box, then provide backtest-ready examples through NubraOSS and MCP.",
        "webinar": "From historical data to a trustworthy backtest",
        "horizon": "Now"
    },
    "Strategy building & automation": {
        "product_thinking": "The strongest opportunity is reducing the distance between an idea, validation and controlled execution rather than adding another isolated condition form.",
        "nubra_context": "NubraOSS, UAT, market/order APIs and emerging MCP/OMS capabilities cover parts of this workflow.",
        "solution": "Package reusable strategy templates and guided MCP workflows that connect validation, Nubra UAT and controlled execution. Keep OMS V3 claims qualified until public availability is confirmed.",
        "webinar": "Turning a trading idea into a tested automated workflow",
        "horizon": "Next"
    },
    "Options analytics & risk": {
        "product_thinking": "Raw option-chain fields are necessary but users make decisions through scenarios, costs, liquidity and risk interpretation.",
        "nubra_context": "Option chain, OI, IV and Greeks are available; advanced derived analytics remain an opportunity.",
        "solution": "Add payoff, breakeven, Greeks scenarios, IV rank, slippage estimates and liquidity scores through the SDK and MCP. Surface margin and settlement implications before execution.",
        "webinar": "Using option-chain data for risk-aware strategy decisions",
        "horizon": "Next"
    },
    "Order execution & OMS": {
        "product_thinking": "Execution quality depends on state recovery, partial-fill handling, reconciliation and observability—not only order-placement speed.",
        "nubra_context": "Order, basket/flexi, margin and order-update capabilities exist; advanced OMS V3 scope is internal/unverified.",
        "solution": "Provide reference execution patterns for idempotency, partial fills, reconnect recovery and reconciliation. Expose structured execution analytics and webhooks where appropriate.",
        "webinar": "Reliable order execution: partial fills, retries and reconciliation",
        "horizon": "Next"
    },
    "Market news & sentiment": {
        "product_thinking": "News is more valuable when it is connected to instruments, events and the user’s workflow rather than delivered as an isolated feed.",
        "nubra_context": "A news capability is known internally but public API exposure requires confirmation.",
        "solution": "Expose a documented news API and make it available to Nubra MCP for instrument-linked summaries, event context and research workflows.",
        "webinar": "Combining market data and news in API workflows",
        "horizon": "Next"
    },
    "Developer onboarding": {
        "product_thinking": "Authentication and setup friction directly affect activation. Existing capabilities create little value if developers cannot discover and implement them quickly.",
        "nubra_context": "Automated TOTP, primary/secondary IP and multi-session support are available.",
        "solution": "Create a production-readiness quickstart covering TOTP, IP management, sessions, errors and recovery. Consider exposing the existing static-IP update capability as a documented endpoint.",
        "webinar": "Go from API access to a production-ready Nubra integration",
        "horizon": "Now"
    },
    "Portfolio & P&L analytics": {
        "product_thinking": "Users want decision and performance context over their activity, not only raw order, position and holding records.",
        "nubra_context": "Orders, positions, holdings and funds are available and provide the base data.",
        "solution": "Add brokerage and charges calculation, realised/unrealised P&L analytics and strategy/order-history insights using stored trade data.",
        "webinar": "Building portfolio and P&L analytics with Nubra APIs",
        "horizon": "Next"
    },
    "Investment education": {
        "product_thinking": "Repeated beginner questions are both a support burden and an activation opportunity when answered inside the product journey.",
        "nubra_context": "The documentation assistant and MCP can provide contextual education.",
        "solution": "Use MCP and the support assistant to guide users to the right API, example and risk concept. Convert recurring questions into short webinars and runnable notebooks.",
        "webinar": "A practical starting path for retail algo and API users",
        "horizon": "Now"
    },
    "Market data & data quality": {
        "product_thinking": "Data coverage, timeliness and consistency determine whether users can trust downstream analytics and automation.",
        "nubra_context": "Core market-data APIs are available; clearer coverage, data-quality guidance and derived analytics can improve adoption.",
        "solution": "Publish coverage and quality guidance by asset and interval, document adjustments and known limitations, and add data-validation examples to the SDK.",
        "webinar": "Building reliable workflows with market data APIs",
        "horizon": "Now"
    },
    "Fundamental data & research": {
        "product_thinking": "Fundamental data becomes more useful when it supports clear research workflows rather than remaining a collection of raw fields.",
        "nubra_context": "Fundamental data is exposed through the SDK and can be used by Nubra MCP for persona-based research guidance.",
        "solution": "Add documented research examples and MCP workflows for equity, derivatives and fundamental-research personas, with source and update-frequency clarity.",
        "webinar": "Building fundamental research workflows with Nubra data",
        "horizon": "Now"
    },
    "Scanners, indicators & alerts": {
        "product_thinking": "Users want to move from raw market data to timely discovery and action without rebuilding common calculations themselves.",
        "nubra_context": "Basic data APIs provide inputs; scanner and indicator workflows can be added through the SDK and MCP.",
        "solution": "Provide reusable scanner, indicator and alert building blocks with documented formulas, scheduling patterns and instrument filters.",
        "webinar": "Creating scanners, indicators and alerts with Nubra APIs",
        "horizon": "Next"
    },
    "Paper trading & UAT": {
        "product_thinking": "Safe forward testing reduces the jump from backtest results to live execution and helps users validate operational behaviour.",
        "nubra_context": "Nubra UAT already supports testing; the main opportunity is clearer positioning, onboarding and examples.",
        "solution": "Market Nubra UAT as the forward-testing environment and provide end-to-end examples that move from backtest to UAT validation.",
        "webinar": "From backtest to forward testing with Nubra UAT",
        "horizon": "Now"
    },
    "Funds, margin & settlement": {
        "product_thinking": "Users need cost, margin and settlement clarity before execution, not after an order is placed.",
        "nubra_context": "Funds and margin capabilities exist; calculators and clearer workflow guidance can make them easier to use.",
        "solution": "Expose margin, payoff and charges calculators with settlement guidance and pre-trade examples across product, SDK and MCP.",
        "webinar": "Understanding margin, charges and settlement before execution",
        "horizon": "Now"
    },
    "SDK, MCP & integrations": {
        "product_thinking": "Reusable integrations reduce implementation time and help users turn available APIs into complete workflows.",
        "nubra_context": "Nubra SDK, NubraOSS and Nubra MCP provide a base for guided and code-based integrations.",
        "solution": "Package task-based SDK examples and MCP workflows for research, data retrieval, testing and controlled execution, with clear boundaries and error handling.",
        "webinar": "Building complete workflows with Nubra SDK and MCP",
        "horizon": "Now"
    },
    "Security, sessions & access": {
        "product_thinking": "Secure automation must remain reliable across login, IP and session-management requirements.",
        "nubra_context": "Automated TOTP, primary and secondary IP support and multi-session support are available.",
        "solution": "Document the automated login flow and session patterns, and consider exposing the existing static-IP update capability as a supported endpoint.",
        "webinar": "Secure and reliable API access with TOTP, IPs and sessions",
        "horizon": "Now"
    },
    "Pricing, brokerage & taxes": {
        "product_thinking": "Cost transparency helps users evaluate strategies realistically and understand the difference between gross and net outcomes.",
        "nubra_context": "Order and trade data provide the base inputs for charges and P&L analysis.",
        "solution": "Provide brokerage, statutory-charge and net-P&L calculators through product interfaces and SDK utilities.",
        "webinar": "Calculating the true cost of an API-driven strategy",
        "horizon": "Next"
    },
    "Instrument & reference data": {
        "product_thinking": "Stable instrument identifiers and contract metadata are foundational for reliable market-data and order workflows.",
        "nubra_context": "Instrument data is available as part of the data stack; discovery and lifecycle examples can be improved.",
        "solution": "Publish instrument-master examples for symbol mapping, expiry changes, lot sizes and contract rollovers, with validation utilities in the SDK.",
        "webinar": "Working reliably with instrument and contract master data",
        "horizon": "Now"
    },
    "Platform usability & support": {
        "product_thinking": "Users should reach the right capability, API and example without searching across disconnected product surfaces.",
        "nubra_context": "Documentation and support surfaces exist; guided discovery can be improved.",
        "solution": "Improve navigation and search, and use an AI support assistant to route users to the relevant product section, API and runnable example.",
        "webinar": "Finding and using the right Nubra capability faster",
        "horizon": "Now"
    }
}
REQUEST = re.compile(r"\b(need|want|wish|request|missing|looking for|would like|should have|feature|support for|can we|is there an api)\b", re.I)


def _contains_alias(text: str, alias: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)", text) is not None


def _engagement(score: int, comments: int) -> float:
    return round(math.log1p(max(score, 0)) + 0.6 * math.log1p(max(comments, 0)), 3)


def _range_clause(days: int | None) -> tuple[str, list[Any]]:
    if not days: return "", []
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    return " WHERE collection_date >= ?", [cutoff]


def search(query: str, limit: int = 20) -> list[dict[str, Any]]:
    db = connect()
    tokens = re.findall(r"[\w-]+", query)
    safe = " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens) or '""'
    rows = db.execute(
        """SELECT kind, item_id, title,
                  snippet(evidence_fts, 3, '[', ']', ' ... ', 28) AS excerpt,
                  subreddit, collection_date, bm25(evidence_fts) AS rank
           FROM evidence_fts
           WHERE evidence_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (safe, min(max(limit, 1), 15)),
    ).fetchall()
    result = []
    seen_items: set[tuple[str, str]] = set()
    for row in rows:
        item = dict(row)
        identity = (item["kind"], item["item_id"])
        if identity in seen_items:
            continue
        seen_items.add(identity)
        if item["kind"] in {"post", "signal"}:
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


def retail_upcoming_features() -> dict[str, Any]:
    sync_result = sync()
    catalog_path = local_root() / "catalog" / "current.json"
    features = []
    if catalog_path.exists():
        catalog = _load(catalog_path)
        for feature in catalog.get("features", []):
            category = feature.get("category") or ""
            status = feature.get("status") or ""
            availability = feature.get("availability") or ""
            surfaces = feature.get("surfaces") or []
            if not category.startswith("Retail App"):
                continue
            if status not in {"upcoming", "partial"} and availability not in {"new_build_evidence", "source_document_evidence"}:
                continue
            if any(str(surface).lower() in {"api/sdk", "mcp"} for surface in surfaces):
                continue
            features.append({
                "id": feature.get("id"),
                "name": feature.get("name"),
                "category": category,
                "status": status,
                "availability": availability,
                "surfaces": surfaces,
                "capability": feature.get("capability"),
                "notes": feature.get("notes"),
                "user_benefit": feature.get("user_benefit"),
                "priority": feature.get("priority"),
                "aliases": feature.get("aliases", []),
                "source": feature.get("source"),
            })
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    features.sort(key=lambda item: (item["category"], priority_rank.get(item.get("priority"), 3), item["name"]))
    return {
        "scope": "retail_only_upcoming_features",
        "excluded": ["API/SDK-only features", "MCP/internal connector features"],
        "count": len(features),
        "features": features,
        "sync": sync_result,
    }


def _evidence_item(post: dict[str, Any], excerpt_length: int = 220) -> dict[str, Any]:
    body = re.sub(r"\s+", " ", post.get("body") or "").strip()
    return {
        "id": post.get("id"),
        "date": post.get("collection_date"),
        "title": post.get("title"),
        "excerpt": body[:excerpt_length],
        "channel": post.get("subreddit"),
        "segment": post.get("segment"),
        "score": post.get("score", 0),
        "comments": post.get("num_comments", 0),
        "url": post.get("permalink"),
        "source_method": post.get("source_method"),
        "evidence_quality": post.get("evidence_quality"),
    }


def analyze(days: int | None = 30) -> dict[str, Any]:
    db = connect(); clause, params = _range_clause(days)
    posts = [dict(r) for r in db.execute("SELECT * FROM posts" + clause, params)]
    features = [dict(r) for r in db.execute("SELECT * FROM features")]
    db.close()
    topic_rows: dict[str, dict[str, Any]] = {}
    feature_rows: dict[str, dict[str, Any]] = {}
    competitor_rows: dict[str, dict[str, Any]] = {}
    cross_topic_rows: dict[tuple[str, str], dict[str, Any]] = {}
    emerging_candidates: list[dict[str, Any]] = []
    evidence = []
    for p in posts:
        p["segment"] = _normalize_segment(p.get("segment"), p.get("subreddit") or "", f"{p.get('title') or ''} {p.get('body') or ''}")
        text = f"{p['title']} {p['body']}".lower(); weight = _engagement(p["score"], p["num_comments"])
        technical_only = {
            "API reliability & WebSockets",
            "Developer onboarding",
            "SDK, MCP & integrations",
            "Security, sessions & access",
        }
        matched_topics = [
            name for name, keys in TOPICS.items()
            if (name not in technical_only or p["segment"] == "api_algo")
            and any(k in text for k in keys)
        ]
        known_topics = sorted(set(matched_topics))
        for topic_a, topic_b in combinations(known_topics, 2):
            pair_key = (topic_a, topic_b)
            pair = cross_topic_rows.setdefault(pair_key, {
                "topic_a": topic_a,
                "topic_b": topic_b,
                "mentions": 0,
                "engagement": 0.0,
                "retail": 0,
                "api_algo": 0,
                "examples": [],
            })
            pair["mentions"] += 1
            pair["engagement"] += weight
            pair[p["segment"]] += 1
            if len(pair["examples"]) < 3:
                pair["examples"].append(_evidence_item(p))

        for competitor, aliases in COMPETITORS.items():
            if not any(_contains_alias(text, alias) for alias in aliases):
                continue
            item = competitor_rows.setdefault(competitor, {
                "competitor": competitor,
                "mentions": 0,
                "engagement": 0.0,
                "retail": 0,
                "api_algo": 0,
                "related_topics": Counter(),
                "examples": [],
            })
            item["mentions"] += 1
            item["engagement"] += weight
            item[p["segment"]] += 1
            item["related_topics"].update(known_topics)
            if len(item["examples"]) < 3:
                item["examples"].append(_evidence_item(p))
        if not matched_topics:
            if any(term in text for term in PRODUCT_DISCOVERY_TERMS):
                emerging_candidates.append({
                    "title": p["title"],
                    "excerpt": (p["body"] or "")[:280],
                    "segment": p["segment"],
                    "subreddit": p["subreddit"],
                    "engagement": weight,
                    "score": p["score"],
                    "comments": p["num_comments"],
                    "url": p["permalink"],
                })
            matched_topics = ["Other market discussion"]
        for name in matched_topics:
            item = topic_rows.setdefault(name, {"topic": name, "mentions": 0, "engagement": 0.0, "retail": 0, "api_algo": 0, "examples": []})
            item["mentions"] += 1; item["engagement"] += weight; item[p["segment"]] += 1
            if len(item["examples"]) < 3: item["examples"].append(_evidence_item(p))
        # Product-demand ranking is intentionally restricted to API/algo-context
        # posts. Retail investment language such as "funds" or "orders" otherwise
        # creates false matches against API capability names.
        if p["segment"] == "api_algo" and REQUEST.search(text):
            for f in features:
                aliases = [f["name"]] + json.loads(f["aliases"])
                if any(str(a).lower() in text for a in aliases if len(str(a)) >= 4):
                    item = feature_rows.setdefault(f["id"], {"feature": f["name"], "status": f["status"], "mentions": 0, "engagement": 0.0, "examples": []})
                    item["mentions"] += 1; item["engagement"] += weight
                    if len(item["examples"]) < 3: item["examples"].append(_evidence_item(p))
        evidence.append((weight, p))
    topics = sorted(topic_rows.values(), key=lambda x: (x["mentions"], x["engagement"]), reverse=True)
    requested = sorted(feature_rows.values(), key=lambda x: (x["mentions"], x["engagement"]), reverse=True)
    cross_topic_insights = sorted(
        cross_topic_rows.values(),
        key=lambda item: (item["mentions"], item["engagement"]),
        reverse=True,
    )[:15]
    competitor_signals = sorted(
        competitor_rows.values(),
        key=lambda item: (item["mentions"], item["engagement"]),
        reverse=True,
    )[:12]
    for item in competitor_signals:
        item["related_topics"] = [
            {"topic": topic, "mentions": count}
            for topic, count in item["related_topics"].most_common(4)
        ]
    emerging_candidates = sorted(
        emerging_candidates,
        key=lambda item: (item["engagement"], item["comments"]),
        reverse=True,
    )[:12]
    for row in topics + requested + cross_topic_insights + competitor_signals:
        row["engagement"] = round(row["engagement"], 2)
    top_evidence = [_evidence_item(p) for _, p in sorted(evidence, key=lambda item: item[0], reverse=True)[:15]]
    source_counts = Counter(p.get("source_method") or "unknown" for p in posts)
    research_methods = {
        "web_search_review", "public_reddit_rss_review", "github_search_api",
        "hacker_news_algolia_api", "broker_docs_page_fetch", "public_signal_collector",
        "youtube_data_api",
    }
    research_count = sum(v for k, v in source_counts.items() if k in research_methods)
    direct_count = len(posts) - research_count
    confidence = "high" if direct_count >= 200 else "medium" if direct_count >= 50 else "low"
    return {"period_days": days, "sample": {
                "posts": len(posts), "direct_posts": direct_count,
                "web_research_summaries": research_count,
                "source_methods": dict(source_counts), "confidence": confidence
            }, "methodology_note": (
                "Web and RSS research summaries have unknown Reddit vote metrics. "
                "They increase thematic coverage and mention frequency but add zero engagement weight."
            ), "topics": topics[:20],
            "feature_requests": requested[:15], "emerging_topic_candidates": emerging_candidates,
            "cross_topic_insights": cross_topic_insights,
            "competitor_signals": competitor_signals,
            "top_evidence": top_evidence}


def _roadmap_action(status: str) -> str:
    return {"available": "Awareness/docs/adoption", "upcoming": "Validate release status and readiness", "partial": "Close scope/access gaps",
            "internal_unverified": "Confirm ownership and public exposure", "not_available": "Evaluate for discovery/roadmap"}.get(status, "Investigate")


def _feature_action(status: str) -> str:
    return {
        "available": "Do not rebuild. Improve discovery, documentation, examples and adoption.",
        "upcoming": "Confirm release scope, readiness and positioning before external promotion.",
        "partial": "Close the missing workflow or access gap, then package the capability clearly.",
        "internal_unverified": "Validate ownership and public exposure before making a product claim.",
        "not_available": "Run focused discovery, validate demand and scope it as a roadmap candidate.",
    }.get(status, "Investigate the user need and confirm current product coverage.")


def build_product_opportunities(data: dict[str, Any]) -> list[dict[str, Any]]:
    opportunities = []
    for topic in data["topics"]:
        if topic["topic"] == "Other market discussion" or topic["topic"] not in PRODUCT_PLAYBOOK:
            continue
        play = PRODUCT_PLAYBOOK[topic["topic"]]
        priority = "High" if topic["mentions"] >= 20 or topic["api_algo"] >= 15 else "Medium"
        opportunities.append({
            "topic": topic["topic"],
            "signal": f"{topic['mentions']} discussions; retail {topic['retail']}, API/algo {topic['api_algo']}",
            "mentions": topic["mentions"],
            "engagement": topic["engagement"],
            "retail": topic["retail"],
            "api_algo": topic["api_algo"],
            "priority": priority,
            "product_thinking": play["product_thinking"],
            "nubra_context": play["nubra_context"],
            "solution": play["solution"],
            "webinar": play["webinar"],
            "horizon": play["horizon"],
        })
    return opportunities[:12]


def build_roadmap(opportunities: list[dict[str, Any]], feature_requests: list[dict[str, Any]]) -> dict[str, list[str]]:
    roadmap: dict[str, list[str]] = {"Now": [], "Next": [], "Later": []}
    for opportunity in opportunities:
        bucket = opportunity["horizon"]
        roadmap[bucket].append(f"{opportunity['topic']}: {opportunity['solution']}")
    for feature in feature_requests[:8]:
        status = feature["status"]
        if status == "available":
            bucket = "Now"
        elif status in {"partial", "upcoming", "internal_unverified"}:
            bucket = "Next"
        else:
            bucket = "Next" if feature["mentions"] >= 2 else "Later"
        item = f"{feature['feature']}: {_feature_action(status)}"
        if item not in roadmap[bucket]:
            roadmap[bucket].append(item)
    return {bucket: items[:5] for bucket, items in roadmap.items()}


def build_feature_gap_matrix(data: dict[str, Any]) -> list[dict[str, Any]]:
    classification = {
        "available": ("Available", "Awareness or adoption gap"),
        "partial": ("Partial", "Workflow or coverage gap"),
        "upcoming": ("Upcoming", "Launch readiness and positioning"),
        "internal_unverified": ("Needs verification", "Ownership and public-availability check"),
        "not_available": ("Missing", "Product discovery candidate"),
    }
    rows = []
    for request in data.get("feature_requests", []):
        status = request.get("status") or "not_available"
        label, gap_type = classification.get(status, ("Needs verification", "Coverage verification"))
        rows.append({
            "feature": request["feature"],
            "classification": label,
            "catalog_status": status,
            "gap_type": gap_type,
            "mentions": request["mentions"],
            "engagement": request["engagement"],
            "recommended_action": _feature_action(status),
            "evidence": request.get("examples", [])[:3],
        })
    return rows


def score_product_opportunities(data: dict[str, Any], opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not opportunities:
        return []
    max_mentions = max(item["mentions"] for item in opportunities) or 1
    max_engagement = max(float(item["engagement"]) for item in opportunities) or 1.0
    competitor_support = Counter()
    for competitor in data.get("competitor_signals", []):
        for related in competitor.get("related_topics", []):
            competitor_support[related["topic"]] += related["mentions"]
    cross_topic_support = Counter()
    for pair in data.get("cross_topic_insights", []):
        cross_topic_support[pair["topic_a"]] += pair["mentions"]
        cross_topic_support[pair["topic_b"]] += pair["mentions"]

    scored = []
    for opportunity in opportunities:
        topic = opportunity["topic"]
        components = {
            "demand": round(35 * opportunity["mentions"] / max_mentions, 1),
            "engagement": round(20 * float(opportunity["engagement"]) / max_engagement, 1),
            "cross_segment_relevance": 10.0 if opportunity["retail"] and opportunity["api_algo"] else 5.0,
            "cross_topic_support": min(10.0, round(cross_topic_support[topic] * 1.5, 1)),
            "competitor_context": min(10.0, round(competitor_support[topic] * 1.5, 1)),
            "nubra_relevance": 15.0,
        }
        score = min(100, int(round(sum(components.values()))))
        scored.append({
            **opportunity,
            "opportunity_score": score,
            "score_band": "High" if score >= 70 else "Medium" if score >= 45 else "Watch",
            "score_breakdown": components,
            "score_note": "Prioritization signal combining recurrence, engagement, segment reach, related needs, competitor context and Nubra relevance.",
        })
    return sorted(scored, key=lambda item: (item["opportunity_score"], item["mentions"]), reverse=True)


def detect_changes(short_days: int = 7, long_days: int = 30) -> dict[str, Any]:
    short_days = max(1, short_days)
    long_days = max(short_days + 1, long_days)
    recent = analyze(short_days)
    broader = analyze(long_days)
    recent_by_topic = {row["topic"]: row for row in recent["topics"]}
    broader_by_topic = {row["topic"]: row for row in broader["topics"]}
    previous_days = long_days - short_days
    changes = []
    for topic in sorted(set(recent_by_topic) | set(broader_by_topic)):
        if topic == "Other market discussion":
            continue
        recent_row = recent_by_topic.get(topic, {})
        broader_row = broader_by_topic.get(topic, {})
        recent_count = int(recent_row.get("mentions", 0))
        previous_count = max(0, int(broader_row.get("mentions", 0)) - recent_count)
        recent_rate = recent_count / short_days
        previous_rate = previous_count / previous_days
        if previous_count == 0 and recent_count >= 2:
            direction = "New"
            rate_change = None
        elif previous_rate == 0:
            direction = "Stable"
            rate_change = None
        else:
            rate_change = round((recent_rate / previous_rate - 1) * 100, 1)
            direction = "Rising" if rate_change >= 35 else "Declining" if rate_change <= -30 else "Stable"
        changes.append({
            "topic": topic,
            "direction": direction,
            "recent_mentions": recent_count,
            "previous_mentions": previous_count,
            "recent_daily_rate": round(recent_rate, 2),
            "previous_daily_rate": round(previous_rate, 2),
            "rate_change_percent": rate_change,
            "recent_retail": int(recent_row.get("retail", 0)),
            "recent_api_algo": int(recent_row.get("api_algo", 0)),
            "evidence": recent_row.get("examples", [])[:2],
        })
    order = {"New": 0, "Rising": 1, "Stable": 2, "Declining": 3}
    changes.sort(
        key=lambda row: (
            order[row["direction"]],
            -(row["rate_change_percent"] or 0),
            -row["recent_mentions"],
        )
    )
    return {
        "short_days": short_days,
        "long_days": long_days,
        "comparison": f"Last {short_days} days versus the preceding {previous_days} days",
        "changes": changes,
    }


def _analysis_fingerprint(root: pathlib.Path, days: int) -> str:
    health = _local_data_health(root)
    state = health.get("state", {})
    payload = {
        "schema": CACHE_SCHEMA_VERSION,
        "days": days,
        "dumps": state.get("dumps", []),
        "catalog_sha256": state.get("catalog_sha256"),
        "connector_version": CONNECTOR_VERSION,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _cache_path(days: int) -> pathlib.Path:
    return local_root() / "cache" / f"daily-insights-{days}.json"


def _load_cached_daily(days: int, fingerprint: str) -> dict[str, Any] | None:
    path = _cache_path(days)
    if not path.exists():
        return None
    try:
        cached = _load(path)
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    if cached.get("fingerprint") != fingerprint:
        return None
    payload = cached.get("payload")
    return payload if isinstance(payload, dict) else None


def _save_cached_daily(days: int, fingerprint: str, payload: dict[str, Any]) -> None:
    _write(_cache_path(days), {
        "schema": CACHE_SCHEMA_VERSION,
        "fingerprint": fingerprint,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "payload": payload,
    })


def _catalog_matches(text: str, limit: int = 12) -> list[dict[str, Any]]:
    tokens = {token.lower() for token in re.findall(r"[A-Za-z0-9+#-]{3,}", text)}
    if not tokens:
        return []
    db = connect()
    matches = []
    for row in db.execute("SELECT * FROM features"):
        aliases = [row["name"]] + json.loads(row["aliases"])
        haystack = " ".join([
            *(str(alias).lower() for alias in aliases),
            str(row["category"] or "").lower(),
            str(row["notes"] or "").lower(),
        ])
        overlap = sum(1 for token in tokens if token in haystack)
        exact = any(str(alias).lower() in text.lower() for alias in aliases if len(str(alias)) >= 4)
        if exact or overlap >= 2:
            item = dict(row)
            item["match_score"] = overlap + (3 if exact else 0)
            item["aliases"] = json.loads(item["aliases"])
            item["surfaces"] = json.loads(item["surfaces"])
            matches.append(item)
    db.close()
    matches.sort(key=lambda item: item["match_score"], reverse=True)
    return matches[:limit]


def _relevant_topics(question: str, opportunities: list[dict[str, Any]]) -> list[str]:
    lowered = question.lower()
    ranked = []
    for item in opportunities:
        topic = item["topic"]
        keywords = TOPICS.get(topic, [])
        overlap = sum(1 for keyword in keywords if keyword in lowered)
        overlap += sum(1 for token in re.findall(r"\w+", topic.lower()) if len(token) >= 4 and token in lowered)
        ranked.append((overlap, item["opportunity_score"], topic))
    matched = [topic for overlap, _, topic in sorted(ranked, reverse=True) if overlap > 0]
    return matched or [item["topic"] for item in opportunities[:5]]


def suggested_followups(question: str, topics: list[str]) -> list[str]:
    primary = topics[0] if topics else "the strongest signal"
    return [
        f"Show the strongest evidence and counter-signals for {primary}.",
        f"Compare Nubra with relevant competitors for {primary}.",
        f"Turn {primary} into product requirements and success measures.",
        "Separate genuine product gaps from awareness, onboarding and documentation gaps.",
        "Turn the strongest user problem into a webinar, demo and launch message.",
    ]


def connector_status(refresh: bool = False) -> dict[str, Any]:
    root = local_root()
    root.mkdir(parents=True, exist_ok=True)
    sync_result = sync(force_remote=True) if refresh else None
    health = _local_data_health(root)
    counts = {"records": 0, "posts": 0, "comments": 0, "features": 0, "upcoming_features": 0}
    db_path = root / "insights.sqlite3"
    if db_path.exists():
        db = connect(root)
        counts["posts"] = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        counts["comments"] = db.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
        counts["features"] = db.execute("SELECT COUNT(*) FROM features").fetchone()[0]
        counts["upcoming_features"] = db.execute(
            "SELECT COUNT(*) FROM features WHERE status IN ('upcoming','partial')"
        ).fetchone()[0]
        counts["records"] = counts["posts"] + counts["comments"]
        db.close()
    cache_files = list((root / "cache").glob("daily-insights-*.json")) if (root / "cache").exists() else []
    return {
        "connector": "reddit-product-insights",
        "version": CONNECTOR_VERSION,
        "status": "ready" if health["healthy"] else "needs_repair",
        "latest_dump": health["latest_dump"],
        "dump_count": health["dump_count"],
        "catalog_version": health.get("state", {}).get("catalog_version"),
        "last_checked_at": health.get("state", {}).get("last_checked_at"),
        "state_age_hours": None if health["state_age_hours"] is None else round(health["state_age_hours"], 2),
        "local_folder": str(root),
        "counts": counts,
        "cache_entries": len(cache_files),
        "issues": health["issues"],
        "refresh": sync_result,
        "available_tools": [
            "ask_product_insights", "run_daily_insights", "search_evidence",
            "get_nubra_feature", "get_retail_upcoming_features",
            "compare_insight_periods", "get_connector_status", "refresh_insights_data",
        ],
    }


def ask_insights(question: str, days: int = 30) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise ValueError("question cannot be empty")
    daily = daily_insights(days)
    scored = daily["opportunity_scores"]
    topics = _relevant_topics(question, scored)
    relevant_opportunities = [row for row in scored if row["topic"] in topics][:8]
    evidence = search(question, 12)
    catalog = _catalog_matches(question)
    requested_gaps = [
        row for row in daily["feature_gap_matrix"]
        if any(token in row["feature"].lower() for token in re.findall(r"\w{4,}", question.lower()))
    ]
    wants_upcoming = any(term in question.lower() for term in ("upcoming", "planned", "new feature", "coming up"))
    upcoming = retail_upcoming_features()["features"] if wants_upcoming else []
    upcoming_gaps = [{
        "feature": feature["name"],
        "classification": "Upcoming",
        "catalog_status": feature["status"],
        "gap_type": "Launch readiness and positioning",
        "mentions": None,
        "engagement": None,
        "recommended_action": "Validate the user problem, finalize placement and prepare launch education before external promotion.",
        "evidence": [],
        "category": feature["category"],
        "priority": feature.get("priority"),
        "user_benefit": feature.get("user_benefit"),
    } for feature in upcoming]
    relevant_gaps = upcoming_gaps or requested_gaps or daily["feature_gap_matrix"][:8]
    trend = daily["trend_changes"]
    relevant_changes = [row for row in trend["changes"] if row["topic"] in topics][:8]
    return {
        "question": question,
        "period_days": days,
        "answer_inputs": {
            "relevant_topics": topics,
            "product_opportunities": relevant_opportunities,
            "feature_gap_matrix": relevant_gaps,
            "catalog_matches": catalog,
            "retail_upcoming_features": upcoming,
            "trend_changes": relevant_changes,
            "evidence": evidence,
            "competitor_signals": daily["analysis"]["competitor_signals"][:8],
            "cross_topic_insights": daily["analysis"]["cross_topic_insights"][:8],
        },
        "suggested_followups": suggested_followups(question, topics),
        "response_contract": {
            "format": "Answer directly in chat using short sections and clean tables where useful.",
            "required": [
                "Answer the user's question first",
                "Connect evidence to the user problem and product implication",
                "State Nubra coverage accurately",
                "Separate product gaps from visibility, onboarding, documentation or support gaps",
                "Recommend practical actions",
            ],
            "avoid": [
                "Methodology narration",
                "Unsupported certainty",
                "Treating engagement as unique demand",
                "Repeating the same recommendation",
            ],
        },
        "data_status": {
            "available_through": daily["sync"]["available_through"],
            "catalog_version": daily["sync"]["catalog_version"],
            "cache_hit": daily["cache_hit"],
        },
    }


def render_insights_report(
    sync_result: dict[str, Any],
    data: dict[str, Any],
    opportunities: list[dict[str, Any]],
    webinars: list[dict[str, Any]],
    roadmap: dict[str, list[str]],
    awareness: list[dict[str, Any]],
) -> str:
    lines = [
        "# Reddit Product and API-User Insights",
        "",
        "## 1. Executive Summary",
        "",
    ]
    for index, opportunity in enumerate(opportunities[:6], start=1):
        lines.append(
            f"{index}. **{opportunity['topic']}** — {opportunity['signal']}. "
            f"**Product response:** {opportunity['solution']}"
        )

    lines += [
        "",
        "## 2. Most Discussed Topics and Product Response",
        "",
        "| Topic | What the discussion indicates | Product thinking | Suggested solution |",
        "|---|---|---|---|",
    ]
    for opportunity in opportunities[:7]:
        lines.append(
            f"| {opportunity['topic']} | {opportunity['signal']} | "
            f"{opportunity['product_thinking']} | {opportunity['solution']} |"
        )

    lines += [
        "",
        "## 3. Most Requested API Capabilities",
        "",
        "| Capability | Demand signal | Nubra status | Recommended action |",
        "|---|---:|---|---|",
    ]
    if data["feature_requests"]:
        for feature in data["feature_requests"][:10]:
            lines.append(
                f"| {feature['feature']} | {feature['mentions']} explicit matches | "
                f"{feature['status']} | {_feature_action(feature['status'])} |"
            )
    else:
        lines.append("| No strong explicit match | Insufficient evidence | — | Continue collection and targeted discovery |")

    retail_total = sum(item["retail"] for item in opportunities)
    api_total = sum(item["api_algo"] for item in opportunities)
    lines += [
        "",
        "## 4. Retail and API/Algo Discussion Split",
        "",
        "| Segment | Dominant needs | Product use |",
        "|---|---|---|",
        f"| Retail | Options interpretation, risk, education and portfolio context | Use analytics, calculators, guided education and clearer discovery to reduce decision friction. |",
        f"| API/Algo | Reliability, historical data, automation, execution and developer onboarding | Use SDK/MCP workflows, observability, reference implementations and production-readiness guidance to improve activation. |",
        "",
        f"Across the prioritised themes, the observed split is **{retail_total} retail-topic matches** and **{api_total} API/algo-topic matches**.",
        "",
        "## 5. Webinar Opportunities",
        "",
        "| Webinar | Audience | Why it is relevant | Product outcome |",
        "|---|---|---|---|",
    ]
    for webinar in webinars[:6]:
        lines.append(
            f"| {webinar['title']} | {webinar['audience']} | {webinar['why_now']} | {webinar['outcome']} |"
        )

    lines += ["", "## 6. Product Roadmap", "", "| Horizon | Recommended actions |", "|---|---|"]
    for horizon in ("Now", "Next", "Later"):
        actions = "<br>".join(f"• {item}" for item in roadmap[horizon]) or "Continue evidence collection."
        lines.append(f"| {horizon} | {actions} |")

    lines += ["", "## 7. Existing Capabilities Users Are Missing", ""]
    if awareness:
        for feature in awareness[:6]:
            lines.append(
                f"- **{feature['feature']}** is already available but still appears in user demand. "
                "Improve its visibility through product discovery, task-based documentation, runnable examples and webinars."
            )
    else:
        lines.append("- No strong available-but-requested match was found in this analysis window.")

    lines += [
        "",
        "## 8. What Nubra Can Improve Now",
        "",
        "| Area | Practical improvement |",
        "|---|---|",
        "| Product | Surface relevant calculators, analytics and feature entry points where users make decisions. |",
        "| SDK | Add task-based examples, reusable workflows and clearer production-readiness guidance. |",
        "| MCP | Connect existing data and execution capabilities to guided research and support workflows. |",
        "| Support | Use a better AI assistant to route users to the right product section, API and example. |",
    ]

    lines.append("")
    return "\n".join(lines)


def daily_insights(days: int = 30, use_cache: bool = True) -> dict[str, Any]:
    sync_result = sync()
    fingerprint = _analysis_fingerprint(local_root(), days)
    if use_cache:
        cached = _load_cached_daily(days, fingerprint)
        if cached is not None:
            cached["sync"] = sync_result
            cached["cache_hit"] = True
            return cached

    data = analyze(days)
    opportunities = build_product_opportunities(data)
    opportunity_scores = score_product_opportunities(data, opportunities)
    feature_gap_matrix = build_feature_gap_matrix(data)
    trend_changes = detect_changes(min(7, max(1, days - 1)), max(30, days))
    webinars = [
        {
            "title": opportunity["webinar"],
            "audience": "API/algo developers" if "API/algo" in opportunity["signal"] and opportunity["topic"] not in {"Options analytics & risk", "Investment education"} else "Retail and API users",
            "why_now": opportunity["signal"],
            "outcome": "Demonstrate relevant existing capabilities, improve activation and validate demand for the proposed product response.",
        }
        for opportunity in opportunities[:6]
    ]
    roadmap = build_roadmap(opportunities, data["feature_requests"])
    available_requests = [x for x in data["feature_requests"][:10] if x["status"] == "available"]
    payload = {
        "analysis": data,
        "product_opportunities": opportunities,
        "opportunity_scores": opportunity_scores,
        "feature_gap_matrix": feature_gap_matrix,
        "trend_changes": trend_changes,
        "webinars": webinars,
        "roadmap": roadmap,
        "awareness_gaps": available_requests,
        "available_commands": [
            "/update-connector", "/ask-insights", "/status", "/daily-insights", "/new-feature-analysis",
            "/retail-feature-research", "/channel-insights", "/github-insights", "/youtube-insights",
            "/trend-check", "/content-plan", "/next-actions", "/feature-requests",
            "/webinar-ideas", "/roadmap", "/lead-magnets", "/competitors",
            "/existing-capabilities",
        ],
    }
    _save_cached_daily(days, fingerprint, payload)
    return {"sync": sync_result, **payload, "cache_hit": False}


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
    return {
        f"last_{days_a}_days": analyze(days_a),
        f"last_{days_b}_days": analyze(days_b),
        "change_detection": detect_changes(days_a, days_b),
    }
