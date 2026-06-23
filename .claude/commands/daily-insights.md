Run the complete daily product-insights flow with one user command.

1. Call `run_daily_insights` with 30 days unless the user supplies another window.
2. Tell the user whether new dumps were pulled and the latest available date.
3. Render the returned report in its prescribed section order. Preserve retail/API-algo bifurcation, Nubra status, evidence and confidence.
4. End with the returned optional drill-down commands. Do not ask the user to run a separate sync command.

