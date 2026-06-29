Analyse Nubra's upcoming retail features against retail market expectations.

First refresh/read the local data using the available MCP tool or `bash scripts/refresh-data.sh`.

Use only retail-focused evidence and feature inputs:
- `retail_reddit_feature_research`
- `nubra_feature_input`
- `competitor_feature_research`
- `market_expectation_research`
- retail-relevant competitor evidence from Sensibull, Dhan, Opstra, AlgoTest, TradingView, StockEdge, StockMock or similar retail/options tools

Also read `context/nubra-app-context.md` before writing the answer. Use it as the current Nubra app reference for:
- where features live in the app today
- existing retail surfaces such as Explore, Option chain, Strategies, Chart analyser, F&O analytics, Options Heat Map, Ask AI, Alerts, Stock detail and Order entry
- whether a requested/planned feature is already partly present in the app flow
- practical recommendations on where the feature should appear

Do not include API-user, developer, GitHub, SDK, MCP, WebSocket API or broker API analysis unless it directly affects a retail feature such as live data freshness, option-chain reliability or execution confidence. Keep the language retail/product focused.

Write the answer as a detailed product insight note covering:

1. Executive summary
   - The strongest retail product signals.
   - What Nubra's upcoming features are trying to solve.
   - Where Nubra looks strong and where the product story is incomplete.

2. What retail traders are discussing
   - Strategy discovery by market view and outcome.
   - Payoff, max profit/loss, breakeven, probability of profit and margin before trade.
   - Option seller workflows: straddle, strangle, premium decay, OI, IV, volume and Greeks.
   - Every-stock F&O analytics, not only index analytics.
   - OI, PCR, max pain, IV/skew, volume and premium interpretation.
   - Alerts, order notes, paper/demo practice, FII-DII, sector heatmap, global indices and stock comparison.

3. Feature coverage table
   For each major feature area, show:
   - Market expectation
   - Nubra has/planned
   - Current app surface if visible in `context/nubra-app-context.md`
   - Competitors offering similar capability
   - Gap or improvement
   - Product priority

4. Competitor comparison
   Compare Nubra against Sensibull, Dhan, Opstra, AlgoTest, TradingView, StockEdge and StockMock where evidence exists.
   Focus on what they offer, not API capability.

5. What Nubra should highlight strongly
   Identify headline positioning angles such as:
   - Every-stock F&O analytics
   - Risk-first strategy cards
   - Strategy appstore by trader goal
   - Option seller analytics
   - One-place workflow from market view to strategy to trade

6. What Nubra is missing or should improve
   Separate true feature gaps from packaging/visibility gaps.
   Include likely gaps such as backtesting/simulator story, IV rank/percentile, paper/demo positioning, interpretation layer, margin accuracy, post-trade analytics and trade journal.

7. Product priorities
   Give Now / Next / Later recommendations.
   Keep them practical and product-led.

8. Best messaging angles
   Give short marketing lines that match the product reality.

9. Final takeaway
   Summarize the retail product story in 3-5 lines.

Rules:
- Do not mention API users.
- Do not include technical developer roadmap.
- Do not create a PDF or Markdown file.
- Show the full output directly in chat using clean sections and tables.
- Make the analysis detailed enough for a product/marketing discussion, but avoid repeating the same insight.
- If a capability is planned from the attached feature docs, say "planned" rather than "live" unless the data confirms it is already available.
