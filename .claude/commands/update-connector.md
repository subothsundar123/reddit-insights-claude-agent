Update this installed connector to the latest verified release with no unnecessary user steps.

1. Confirm the current folder is the `reddit-insights-claude-agent` repository by checking for:
   - `pyproject.toml`
   - `src/reddit_insights_agent`
   - `.claude/commands`
   - `updates/latest.md`
2. Check `git status --short`. If tracked files have uncommitted user changes, do not overwrite them. Explain the conflict and stop.
3. Run:

   `git fetch origin main`

   `git pull --ff-only origin main`

4. After the pull completes, read `updates/latest.md`. Follow the dated update instruction referenced there exactly.
5. Ensure the local virtual environment still uses the current connector code by running:

   `.venv/bin/python -m pip install -e .`

6. Refresh the verified insights data:

   `bash scripts/refresh-data.sh`

7. Run the complete test suite:

   `.venv/bin/python -m unittest discover -s tests -v`

8. Run the health check:

   `.venv/bin/python -m reddit_insights_agent.cli status`

9. Report only:
   - previous and current Git commit
   - connector version
   - dated update instruction applied
   - latest dump date
   - test result
   - whether Claude Desktop must be restarted

Do not edit unrelated repositories, delete local dumps, create a report or send external messages.
