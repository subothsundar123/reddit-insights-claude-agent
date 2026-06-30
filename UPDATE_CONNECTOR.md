# Update the Reddit Product Insights Connector

Use this when the connector is already installed and the user wants the latest prompts, tools, feature catalog and dumps.

## Goal

Update the existing local connector setup completely with minimal user effort.

After this update, the user should be able to run:

- `/ask-insights <question>` and `/status` in Claude Code
- `/new-feature-analysis` in Claude Code
- `ask_product_question` and `connector_health` from the Claude Desktop connector prompt menu
- `new_feature_analysis` from the Claude Desktop connector prompt menu

## What to do

1. Confirm you are inside the connector repository.

   The current folder should contain:

   - `pyproject.toml`
   - `src/reddit_insights_agent`
   - `.claude/commands`
   - `CLAUDE.md`

   If not, locate the repo in common folders such as:

   - `~/reddit-insights-claude-agent`
   - `~/Downloads/reddit-insights-claude-agent`
   - `~/Documents/reddit-insights-claude-agent`
   - `~/reddit_insights_claude_agent`
   - `~/Downloads/reddit_insights_claude_agent`

   Then change into that folder.

2. Pull the latest connector code.

   Run:

   ```bash
   git pull
   ```

   If Git is not installed or the repo was installed from a ZIP, tell the user:

   - Download the latest ZIP from `https://github.com/subothsundar123/reddit-insights-claude-agent`
   - Replace the old folder with the new extracted folder
   - Reopen Claude Code from that folder

   Do not continue pretending the update succeeded if the latest code cannot be pulled or replaced.

3. Ensure the local environment exists.

   If `.venv` is missing, create it and install the package:

   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   python -m pip install -U pip
   python -m pip install -e .
   ```

   If `.venv` already exists, activate it:

   ```bash
   . .venv/bin/activate
   ```

4. Refresh the latest insights data.

   Prefer the repo script:

   ```bash
   bash scripts/refresh-data.sh
   ```

   If the script is unavailable or fails, use the Python CLI/help in this repo to refresh/sync the data if available. If refresh still fails, report the exact blocker.

5. Verify the update.

   Check that this file exists:

   ```bash
   test -f .claude/commands/ask-insights.md && echo "ask-insights command found"
   test -f .claude/commands/status.md && echo "status command found"
   test -f .claude/commands/new-feature-analysis.md && echo "new-feature-analysis command found"
   ```

   Check that the latest connector contains the universal query, status and feature-analysis prompts:

   ```bash
   grep -R "def ask_product_insights" -n src/reddit_insights_agent/server.py
   grep -R "def get_connector_status" -n src/reddit_insights_agent/server.py
   grep -R "def new_feature_analysis" -n src/reddit_insights_agent/server.py
   ```

   Run the built-in health check:

   ```bash
   python -m reddit_insights_agent.cli status
   ```

   Check that the retail upcoming feature list exists:

   ```bash
   test -f context/nubra-app-context.md && echo "app context found"
   ```

   If the data repo has been pulled locally, verify the latest retail data includes the latest dump. The expected latest dump at the time this guide was written is:

   - Date: `2026-06-29`
   - Signals: around `439`

   Do not fail the update only because the signal count is higher than this; higher is fine.

6. Run tests if practical.

   If the environment is ready, run:

   ```bash
   python -m unittest discover -s tests
   ```

   If tests fail, report the failing test and likely reason. Do not hide failures.

## Final message to the user

When finished, respond with a short status:

- whether connector code was updated
- whether latest data was refreshed
- whether `/ask-insights` and `/status` are available
- whether `/new-feature-analysis` is available
- whether Claude Desktop needs reload

Use this final wording:

```text
Update complete.

You can now use /ask-insights, /status and /new-feature-analysis in Claude Code.

If you use Claude Desktop, fully quit and reopen Claude Desktop, then toggle the reddit-product-insights connector off/on. After that use:
+ → Connectors → Add from reddit-product-insights → new_feature_analysis
```

## Important rules

- Keep this update focused only on the connector and local insights data.
- Do not edit unrelated repos.
- Do not create a PDF or report.
- Do not run Slack or external messaging automations.
- Do not ask the user to do manual steps unless a tool is missing or a command fails.
