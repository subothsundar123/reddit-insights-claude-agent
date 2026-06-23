# Reddit Product Insights Agent

## Recommended: Claude Desktop

On the lead's Windows computer:

```powershell
git clone https://github.com/subothsundar123/reddit-insights-claude-agent.git
cd reddit-insights-claude-agent
powershell -ExecutionPolicy Bypass -File .\scripts\install_claude_desktop.ps1
```

Completely quit and reopen Claude Desktop. In a new chat, confirm the `reddit-product-insights` connector under **+ → Connectors**, then say:

> Give me today's daily product insights.

The connector automatically checks the private publisher repository, downloads only unseen daily dump and feature-catalog files, verifies checksums, imports them into a separate local SQLite store, generates a decision-ready report, saves it locally, and offers follow-up analyses. There is no separate sync step.

The full copy-ready prompt is available in `desktop/DAILY_INSIGHTS_PROMPT.md`.

## Claude Code alternative

```powershell
.\scripts\install.ps1
```

Claude Code users can invoke `/daily-insights`. Desktop users should use the natural-language prompt above because project `.claude/commands` are specific to Claude Code.

Configure either `INSIGHTS_DATA_REPO_URL` (normal team usage) or `INSIGHTS_DATA_REPO_PATH` (local development). For the private GitHub repository, authenticate Git once on the lead's computer; credentials are never stored in this project.

Claude Code discovers `.claude/commands` and the project charter automatically when opened in this folder. Claude Desktop can use `config/claude_desktop_config.example.json` to start the same MCP server.

The committed `.mcp.json` connects Claude Code to the local MCP server automatically. On first use, approve the project MCP server when Claude Code asks.

## Local data separation

By default, pulled data, sync state, SQLite, and reports live in `%USERPROFILE%\Documents\Nubra Product Insights`, outside this code repository. Existing dates are never downloaded twice. Checksums prevent partial or altered imports.

## Insight coverage

The daily report includes retail/API-algo hot topics, explicit feature requests, feature availability reconciliation, webinar ideas, roadmap signals, awareness/documentation gaps, strategy-builder expectations, evidence and confidence. The prompt library adds developer funnel, reliability, personas, content/GitHub, support automation, competitive signals and release-impact analysis.

No Slack integration and no autonomous external messaging are included.
