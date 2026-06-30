Answer this product question using the complete local insights engine:

`$ARGUMENTS`

Preferred path:
1. Call `ask_product_insights` with the complete question and a 30-day window.
2. Use its relevant evidence, Nubra feature coverage, feature-gap classification, opportunity scores, trend changes, competitor context and cross-topic signals.
3. Answer the question directly before adding supporting analysis.
4. Distinguish genuine build gaps from visibility, onboarding, documentation and support gaps.
5. Recommend practical product, marketing, content or support actions only when relevant.
6. End with a short list of useful follow-up questions.

If the MCP tool is unavailable, run:

`.venv/bin/python -m reddit_insights_agent.cli ask "$ARGUMENTS" --days 30`

Use the returned JSON as the answer foundation. Do not narrate the tool process, create a report file or treat engagement as unique user demand.
