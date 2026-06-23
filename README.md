# Reddit Product Insights Agent

The lead uses one command in Claude Code:

```text
/daily-insights
```

That command automatically checks the private publisher repository, downloads only unseen daily dump and feature-catalog files, verifies checksums, imports them into a separate local SQLite store, generates a decision-ready report, saves it locally, and offers drill-down commands. There is no separate sync step for the lead.

## Install

```powershell
.\scripts\install.ps1
```

Configure either `INSIGHTS_DATA_REPO_URL` (normal team usage) or `INSIGHTS_DATA_REPO_PATH` (local development). For a private GitHub repository, authenticate Git once on the lead's computer; credentials are never stored in this project.

Claude Code discovers `.claude/commands` and the project charter automatically when opened in this folder. Claude Desktop can use `config/claude_desktop_config.example.json` to start the same MCP server.

The committed `.mcp.json` connects Claude Code to the local MCP server automatically. On first use, approve the project MCP server when Claude Code asks.

## Local data separation

By default, pulled data, sync state, SQLite, and reports live in `%USERPROFILE%\Documents\Nubra Product Insights`, outside this code repository. Existing dates are never downloaded twice. Checksums prevent partial or altered imports.

## Insight coverage

The daily report includes retail/API-algo hot topics, explicit feature requests, feature availability reconciliation, webinar ideas, roadmap signals, awareness/documentation gaps, strategy-builder expectations, evidence and confidence. The prompt library adds developer funnel, reliability, personas, content/GitHub, support automation, competitive signals and release-impact analysis.

No Slack integration and no autonomous external messaging are included.
