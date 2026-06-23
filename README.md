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

Claude Code updates the shared data folder with `/update-insights-data`. Claude Desktop reads those verified local dumps and the local SQLite store, generates a decision-ready report, saves it locally, and offers follow-up analyses. Desktop does not access GitHub during report generation.

The installer supports both the classic installer and Microsoft Store versions of Claude Desktop. It backs up and merges the active configuration, preserving existing MCP servers and preferences.

The full copy-ready prompt is available in `desktop/DAILY_INSIGHTS_PROMPT.md`.

### Focused connector prompts

Claude Desktop also exposes six short prompts for focused work:

- `feature_requests` - strongest user requests and the right product response
- `feature_gaps` - requested capabilities compared with Nubra's current coverage
- `trend_check` - rising, stable and declining discussion themes
- `improve_now` - practical improvements across product, SDK, MCP and support
- `webinar_ideas` - webinar topics drawn from repeated questions and demand
- `roadmap` - a simple Now, Next and Later product view

These prompts use the same locally stored dumps and Nubra feature catalogue. Each prompt follows a product-manager workflow: identify the user problem, separate demand signals, check current coverage, distinguish product gaps from adoption gaps, prioritize the smallest useful action and state the expected outcome. They return concise text and tables directly in chat.

## Shared-folder workflow

1. Open this repository in Claude Code and run `/update-insights-data`.
2. New dumps and catalog versions are saved under `%USERPROFILE%\Documents\Nubra Product Insights`.
3. Open Claude Desktop and run the daily prompt.
4. Desktop analyses only the files in that shared folder, so reporting remains fast and does not depend on GitHub credentials.

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

The daily insights report uses simple, clean and product-focused language. It includes retail/API-algo topics, explicit feature requests, product implications, practical solutions, feature-availability reconciliation, webinar ideas, a Now/Next/Later roadmap, existing capabilities users are missing and immediate improvements across product, SDK, MCP and support. Related workflow and execution signals are incorporated into feature and roadmap recommendations instead of appearing as a separate section. The complete report is shown directly in Claude Chat using text and tables; no PDF or Markdown report file is created.

No Slack integration and no autonomous external messaging are included.
