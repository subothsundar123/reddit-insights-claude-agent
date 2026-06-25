# Reddit Product Insights Agent

## Linux setup for Claude Code

Use this path when Claude Desktop is not available.

1. Clone or download this repository.
2. Open the repository folder in a terminal.
3. Run:

```bash
./setup-code.sh
```

The setup creates a local Python environment, pulls all available public dump data into `~/Documents/Nubra Product Insights`, and installs a daily morning updater using a systemd user timer or cron fallback.

After setup, open Claude Code from this folder:

```bash
claude
```

Then use the project commands:

| Command | Use |
|---|---|
| `/daily-insights` | Complete product insight report from the latest dumps |
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

The data source is public, so no GitHub account, token or SSH key is required. If Git is not installed, the sync engine falls back to GitHub ZIP download.

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

Claude Desktop also exposes nine short prompts for focused work:

- `feature_requests` - strongest user requests and the right product response
- `feature_gaps` - requested capabilities compared with Nubra's current coverage
- `trend_check` - rising, stable and declining discussion themes
- `improve_now` - practical improvements across product, SDK, MCP and support
- `webinar_ideas` - webinar topics drawn from repeated questions and demand
- `roadmap` - a simple Now, Next and Later product view
- `new_ideas` - emerging Nubra-relevant topics outside the standard categories
- `competitors` - competitor mentions, related user needs and supported opportunities
- `topic_links` - combined opportunities where discussion themes repeatedly overlap

These prompts use the same locally stored dumps and Nubra feature catalogue. Each prompt starts with the strongest insights, identifies the user problem, separates demand signals, checks current coverage, distinguishes product gaps from adoption gaps and recommends the smallest useful action. The engine also returns relevant unclassified discussions so new Nubra topics and ideas are not lost when they fall outside the standard categories. Outputs appear as concise text and tables directly in chat without describing the analysis process.

## Automatic shared-folder workflow

1. Setup performs the first sync immediately.
2. At 08:00 local time, macOS `launchd` or a Linux `systemd` user timer checks for new dumps and catalogue updates.
3. If the computer was off or asleep, the persistent job runs after the next login or wake.
4. Only missing dumps are downloaded and every file is checksum-verified.
5. Claude Desktop analyses the local files when the user requests insights.

## Claude Code alternative

Claude Code users should run `./setup-code.sh` on Linux/macOS, then invoke `/daily-insights` or any focused command listed above. Desktop users should use the natural-language prompt above because project `.claude/commands` are specific to Claude Code.

Configure either `INSIGHTS_DATA_REPO_URL` (normal team usage) or `INSIGHTS_DATA_REPO_PATH` (local development). Private repository authentication is handled by Git, outside this project.

Claude Code discovers `.claude/commands` and the project charter automatically when opened in this folder. Claude Desktop can use `config/claude_desktop_config.example.json` to start the same MCP server.

The committed `.mcp.json` connects Claude Code to the local MCP server automatically. On first use, approve the project MCP server when Claude Code asks.

## Local data separation

By default, pulled data, sync state and SQLite live in `~/Documents/Nubra Product Insights` (or the Windows Documents equivalent), outside this code repository. Existing dates are never downloaded twice. Checksums prevent partial or altered imports.

## Insight coverage

The daily insights report uses simple, clean and product-focused language. It includes retail/API-algo topics, explicit feature requests, product implications, practical solutions, feature-availability reconciliation, webinar ideas, a Now/Next/Later roadmap, existing capabilities users are missing and immediate improvements across product, SDK, MCP and support. Related workflow and execution signals are incorporated into feature and roadmap recommendations instead of appearing as a separate section. The complete report is shown directly in Claude Chat using text and tables; no PDF or Markdown report file is created.

No Slack integration and no autonomous external messaging are included.
