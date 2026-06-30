Check whether Reddit Product Insights is ready.

Preferred path:
1. Call `get_connector_status` with `refresh=false`.
2. Show connector version, status, latest dump, record count, feature count, upcoming-feature count, last check and cache entries.
3. If unhealthy, call `refresh_insights_data` once and check status again.
4. Report the exact remaining issue and next action.

If MCP tools are unavailable, run:

`.venv/bin/python -m reddit_insights_agent.cli status`

Do not generate a product-insights report.
