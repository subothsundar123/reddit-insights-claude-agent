Run the complete daily product-insights flow with one user command.

Optional filters the user can include in the command text:

```text
/daily-insights days=30 channels=all focus=both
/daily-insights days=30 channels=youtube focus=retail
/daily-insights days=14 channels=reddit,youtube focus=content
/daily-insights days=30 channels=all focus=new_features
```

Supported channels:

```text
all, reddit, youtube, github, hacker_news, broker_docs, manual_research, internal_catalog
```

Supported focus values:

```text
both, retail, api, new_features, content, competitors, pain_points, roadmap, webinars, lead_magnets
```

First refresh/read the local data:
- Preferred: call `run_daily_insights` with 30 days unless the user supplies another window.
- If the MCP tool is unavailable in Claude Code, run `bash scripts/refresh-data.sh`, then run `.venv/bin/python -m reddit_insights_agent.cli daily-insights --days 30` and use the JSON as the analysis base.

Apply channel and focus filters in the final answer:
- If channels is `all`, use every available source.
- If channels includes `youtube`, use YouTube video/comment signals and comment-derived pain points.
- If channels includes `reddit`, use Reddit posts/comments and Reddit research signals.
- If channels includes `github`, use public GitHub developer/API signals.
- If focus is `retail`, exclude API/developer-only conclusions.
- If focus is `api`, exclude retail-only conclusions.
- If focus is `new_features`, compare upcoming Nubra features with community demand and competitor evidence.
- If focus is `content`, `webinars` or `lead_magnets`, turn repeated questions and pain points into practical content ideas.
- If focus is `competitors`, emphasize competitor mentions and positioning without treating mention count as market share.
- If focus is `pain_points`, prioritize repeated complaints, confusion and workflow blockers.
- If focus is `roadmap`, translate signals into Now/Next/Later product actions.

Write the answer like a clean product insight note, not a data dump.

Required output:
1. Executive summary with the strongest 5-6 product signals and practical product responses.
2. Most discussed topics and product response.
3. Most requested API/product capabilities.
4. Retail vs API/algo split.
5. Existing capabilities users are missing and how to improve visibility.
6. Webinar/content opportunities.
7. Product roadmap signals in Now / Next / Later.
8. What Nubra can improve now across product, SDK, MCP and support.
9. Competitor signals and positioning opportunities.
10. Cross-topic insights where repeated user problems connect.
11. Emerging topics and new ideas when the dump supports them.
12. Opportunity priorities using the connector's opportunity scores.
13. What changed versus the preceding period.

Rules:
- Keep one unified narrative. Do not separate "dump data" and "external thinking".
- Use current web research only if it materially improves the recommendation.
- Do not create or attach PDF/Markdown files. Show the answer directly in chat.
- Avoid generic statements. Every major point needs a user problem, product implication and practical action.
- Use representative evidence links for major conclusions.
- Separate available, partial, upcoming, missing and needs-verification capabilities.
- Do not create a separate strategy-builder section; include those signals inside feature, roadmap or workflow recommendations.
- End with only useful follow-up questions or commands.
