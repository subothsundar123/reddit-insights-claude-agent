# Linux Claude Code Setup Prompt

Paste this into Claude Code on a Linux system:

```text
Set up the Reddit Product Insights workflow from this GitHub repo:

https://github.com/subothsundar123/reddit-insights-claude-agent.git

Use the Linux setup guide inside the repo and complete the setup end-to-end.

What to do:
1. Pull or download the repo.
2. Follow the repo's Linux Claude Code setup instructions.
3. Run the setup script provided by the repo.
4. Sync all available dump data into the local data folder.
5. Install the automatic daily updater if the system supports it.
6. Verify that the local data is available.
7. Verify that the Claude Code slash commands are ready.
8. Tell me the one command I should run next for daily insights.

Important:
- This is for Claude Code on Linux, not Claude Desktop.
- Do not ask me to manually edit files unless absolutely required.
- The GitHub repos are public, so no GitHub login or token should be needed.
- If Git is unavailable, use the repo's ZIP fallback path.
- The setup is not complete unless local dump data is synced.
- Keep the final answer simple.
```

After setup, open Claude Code inside the repo and run:

```text
/daily-insights
```

Other useful commands:

```text
/feature-requests
/webinar-ideas
/roadmap
/lead-magnets
/competitors
/existing-capabilities
```
