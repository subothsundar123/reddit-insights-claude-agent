# Reddit Product Insights Agent

Version 2 adds self-healing data sync, connector health checks, cached analysis,
evidence-backed answers, feature-gap classification, opportunity scoring,
period-over-period change detection and one universal product-question workflow.

## Fast setup prompt for Linux

If you are setting this up through Claude Code on Linux, use:

[LINUX_SETUP_PROMPT.md](LINUX_SETUP_PROMPT.md)

The user only needs to give Claude Code the repo link and ask it to follow the setup guide in this repository.

## Linux setup for Claude Code

Use this path when Claude Desktop is not available.

1. Clone or download this repository.
2. Open the repository folder in a terminal.
3. Run:

```bash
./setup-code.sh
```

The setup creates a local Python environment, pulls all available public dump data into `~/Documents/Nubra Product Insights`, and installs a daily morning updater using a systemd user timer or cron fallback.

After setup, launch the insights workspace from anywhere:

```bash
reddit-insights
```

Then use the project commands:

| Command | Use |
|---|---|
| `/update-connector` | Pull and apply the latest dated connector release automatically |
| `/ask-insights <question>` | Ask any product question using all available intelligence |
| `/status` | Check connector version, data health, record counts, catalogue and cache |
| `/daily-insights` | Complete product insight report from the latest dumps; supports days, channels and focus filters |
| `/retail-feature-research` | Detailed retail analysis of upcoming Nubra features vs Reddit demand and competitors |
| `/channel-insights` | Source-wise view across Reddit, GitHub, Hacker News, broker docs and future channels |
| `/github-insights` | Developer/API demand from public GitHub issues and repos |
| `/youtube-insights` | Retail/API YouTube comment signals, reach metrics, competitor mentions and content ideas |
| `/seo-insights` | Marketing SEO keyword opportunities mapped to Nubra features, competitors and community demand |
| `/trend-check` | Rising, stable and emerging topics across available data |
| `/content-plan` | Webinars, docs, lead magnets, demos and post ideas |
| `/next-actions` | Execution-focused product, SDK, MCP, docs, support and marketing actions |
| `/feature-requests` | Requested API/product features and Nubra coverage |
| `/webinar-ideas` | Webinar and content ideas from repeated user pain points |
| `/roadmap` | Now / Next / Later product roadmap signals |
| `/lead-magnets` | Lead magnet ideas for API, retail and algo users |
| `/competitors` | Competitor mentions and positioning opportunities |
| `/existing-capabilities` | Requested features Nubra may already have but users are missing |

For manual data refresh anytime:

```bash
bash scripts/refresh-data.sh
```

For future connector code, prompt and intelligence-engine updates, open the
workspace with `reddit-insights` and run:

```text
/update-connector
```

The command pulls the latest `main` branch, reads the latest dated instruction
from `updates/latest.md`, refreshes data, reinstalls the local package, runs the
tests and reports whether Claude Desktop needs a restart.

The data source is public, so no GitHub account, token or SSH key is required. If Git is not installed, the sync engine falls back to GitHub ZIP download.

Daily insights can be filtered when needed:

```text
/daily-insights days=30 channels=all focus=both
/daily-insights days=30 channels=youtube focus=retail
/daily-insights days=14 channels=reddit,youtube focus=content
/daily-insights days=30 channels=all focus=new_features
```

Supported channels are `all`, `reddit`, `youtube`, `github`, `hacker_news`, `broker_docs`, `manual_research` and `internal_catalog`.
Supported focus values are `both`, `retail`, `api`, `new_features`, `content`, `competitors`, `pain_points`, `roadmap`, `webinars` and `lead_magnets`.

If the shell says `reddit-insights: command not found`, add `~/.local/bin` to `PATH`, then reopen the terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## First-time setup

The easiest setup is designed for someone who receives a ZIP and does not want to configure Python or Claude manually.

1. Download and extract the agent ZIP.
2. Open the extracted folder in Claude Code.
3. Enter this single prompt:

> Set up Reddit Product Insights for Claude Desktop on this computer. Install everything, download the available data and verify the connector.

Claude Code follows `CLAUDE.md` and runs the correct installer. On macOS or Linux the direct command is:

```bash
./install.sh
```

On macOS, `install.command` can also be opened directly from Finder. Windows continues to use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_claude_desktop.ps1
```

The macOS/Linux installer copies the agent into a stable user directory, creates an isolated Python environment, downloads and verifies all available data, backs up and merges Claude Desktop's configuration, and installs an 08:00 local-time daily updater with catch-up after shutdown or sleep.

Completely quit and reopen Claude Desktop. In a new chat, confirm the `reddit-product-insights` connector under **+ → Connectors**, then say:

> Give me today's daily product insights.

Claude Desktop reads verified local dumps and the local SQLite store. The scheduled updater downloads new data separately, so report generation does not wait for GitHub.

The installer preserves existing MCP servers and Claude preferences. Run `python3 scripts/diagnose.py` from the extracted folder to check the local data, connector path and scheduler.

### GitHub access

- A public data repository works without a GitHub account.
- The current publisher repository is public, so a first-time user does not need GitHub login.
- If the repository becomes private later, credentials must be configured through Git/GitHub's authentication flow. They are never stored in the ZIP, Claude configuration or project files.

A deploy key allows the lead to receive automatic updates without creating a GitHub account. Generate the key on the lead's computer, add only its public half to the publisher repository as a read-only deploy key, and install with:

```bash
./install.sh --repo-url git@github.com:subothsundar123/reddit-scraper-github-publisher.git
```

The repository owner must complete that one-time authorization; afterwards the 08:00 updater runs unattended.

The full copy-ready prompt is available in `desktop/DAILY_INSIGHTS_PROMPT.md`.

### Focused connector prompts

Claude Desktop also exposes reusable prompts for focused work:

- `ask_product_question` - answer one natural-language product question using the full intelligence layer
- `connector_health` - check data readiness and repair unhealthy local data
- `feature_requests` - strongest user requests and the right product response
- `feature_gaps` - requested capabilities compared with Nubra's current coverage
- `trend_check` - rising, stable and declining discussion themes
- `improve_now` - practical improvements across product, SDK, MCP and support
- `webinar_ideas` - webinar topics drawn from repeated questions and demand
- `roadmap` - a simple Now, Next and Later product view
- `new_ideas` - emerging Nubra-relevant topics outside the standard categories
- `competitors` - competitor mentions, related user needs and supported opportunities
- `topic_links` - combined opportunities where discussion themes repeatedly overlap
- `youtube_insights` - YouTube text/comment signals split into retail and API/algo views
- `seo_insights` - marketing SEO keyword opportunities mapped to product, competitor and community demand

These prompts use the same locally stored dumps and Nubra feature catalogue. Each prompt starts with the strongest insights, identifies the user problem, separates demand signals, checks current coverage, distinguishes product gaps from adoption gaps and recommends the smallest useful action. The engine also returns relevant unclassified discussions so new Nubra topics and ideas are not lost when they fall outside the standard categories. Outputs appear as concise text and tables directly in chat without describing the analysis process.

### Intelligence layer

- Local state, dump files and the feature catalogue are validated before analysis.
- Missing or corrupted local files trigger an automatic verified repair.
- Healthy recent snapshots are reused, while stale snapshots are refreshed when a source is available.
- Common daily analyses are cached and invalidated whenever dumps, catalogue data or connector version changes.
- Major conclusions include representative evidence with date, channel, engagement and source link.
- Requested features are classified as Available, Partial, Upcoming, Missing or Needs verification.
- Opportunities are scored using recurrence, engagement, segment reach, connected user needs, competitor context and Nubra relevance.
- Trend output compares recent daily rates with the preceding period instead of comparing unequal raw totals.
- Every universal answer includes practical follow-up questions for deeper evidence, competitor review, product requirements or content planning.
- Marketing SEO keyword intelligence from the Nubra priority keyword workbook is synced as a compact catalog and used by `/seo-insights` for SEO, content, competitor and product mapping.

Useful CLI checks:

```bash
insights-agent status
insights-agent status --refresh
insights-agent ask "What should Nubra improve in the option-chain workflow?"
```

## Automatic shared-folder workflow

1. Setup performs the first sync immediately.
2. At 08:00 local time, macOS `launchd` or a Linux `systemd` user timer checks for new dumps and catalogue updates.
3. If the computer was off or asleep, the persistent job runs after the next login or wake.
4. Only missing dumps are downloaded and every file is checksum-verified.
5. Claude Desktop analyses the local files when the user requests insights.

## Claude Code alternative

Claude Code users should run `./setup-code.sh` on Linux/macOS, then launch with `reddit-insights` and invoke `/daily-insights` or any focused command listed above. Desktop users should use the natural-language prompt above because project `.claude/commands` are specific to Claude Code.

Configure either `INSIGHTS_DATA_REPO_URL` (normal team usage) or `INSIGHTS_DATA_REPO_PATH` (local development). Private repository authentication is handled by Git, outside this project.

Claude Code discovers `.claude/commands` and the project charter automatically when opened in this folder. Claude Desktop can use `config/claude_desktop_config.example.json` to start the same MCP server.

The committed `.mcp.json` connects Claude Code to the local MCP server automatically. On first use, approve the project MCP server when Claude Code asks.

## Local data separation

By default, pulled data, sync state and SQLite live in `~/Documents/Nubra Product Insights` (or the Windows Documents equivalent), outside this code repository. Existing dates are never downloaded twice. Checksums prevent partial or altered imports.

## App context reference

`context/nubra-app-context.md` stores the current Nubra Android app context map. The `/retail-feature-research` command uses it to connect market demand and upcoming feature analysis to actual app surfaces such as Explore, Option chain, Strategies, Chart analyser, F&O analytics, Options Heat Map, Ask AI, Alerts, Stock detail and Order entry.

## Insight coverage

The daily insights report uses simple, clean and product-focused language. It includes retail/API-algo topics, cross-channel public signals, explicit feature requests, product implications, practical solutions, feature-availability reconciliation, webinar ideas, a Now/Next/Later roadmap, existing capabilities users are missing and immediate improvements across product, SDK, MCP and support. Related workflow and execution signals are incorporated into feature and roadmap recommendations instead of appearing as a separate section. The complete report is shown directly in Claude Chat or Claude Code using text and tables; no PDF or Markdown report file is created.

No Slack integration and no autonomous external messaging are included.
