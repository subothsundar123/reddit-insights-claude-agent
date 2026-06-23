Run the complete daily product-insights flow with one user command.

1. Call `run_daily_insights` with 30 days unless the user supplies another window.
2. Tell the user whether new dumps were pulled and the latest available date.
3. Use the returned structured topics, product opportunities and roadmap as the editorial foundation. Preserve the concise insights tone, product thinking, practical solutions, section order, retail/API-algo split and Nubra status.
4. Enrich the report with current web research where it materially improves the recommendation, but keep one unified narrative and avoid repeating the same insight.
5. Add `Existing Capabilities Users Are Missing`, showing requested features Nubra already offers and how to improve their visibility.
6. Add `What Nubra Can Improve Now`, with short practical improvements across product, SDK, MCP and support.
7. Show the full report directly in chat using concise text and clean tables. Do not create or attach a PDF or Markdown file.
8. End with only the most relevant optional drill-down commands. Do not ask the user to run a separate sync command.
