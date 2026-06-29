Analyse Nubra's upcoming retail features against community demand and competitor offerings.

First refresh/read the local data:
- Preferred: call `get_retail_upcoming_features`, `run_daily_insights` for 30 days, and `get_nubra_app_context`.
- If MCP tools are not available in Claude Code, run `bash scripts/refresh-data.sh`, then inspect the local catalog and dumps directly.

Use only retail-focused evidence:
- `product-catalog/retail-upcoming-features.json`
- `nubra_feature_input`
- `retail_reddit_feature_research`
- `competitor_feature_research`
- `market_expectation_research`
- `context/nubra-app-context.md`

Do not include API-user, SDK, MCP, GitHub developer, broker API or WebSocket API analysis. If a technical topic affects a retail feature, translate it into retail language such as live data freshness, execution confidence or option-chain trust.

Upcoming retail feature themes to evaluate:
- Trader persona modes, Investor mode and persona-based settings
- Option Buyer mode and Option Seller mode
- Option-chain filters, custom layouts and column controls
- OI bars, PCR, Total Call OI, Total Put OI, Max Pain and ITM highlighting
- VWAP, premium, OI, OI buildup, volume, volume spike, IV, IV change, Greeks, bid-ask spread and OI concentration
- One-click trade with bid/ask across strikes
- F&O analytics on every stock
- OI/IV/premium/volume plotted against price
- Straddle and strangle premium charts
- Futures analytics by expiry
- Buy/sell actionables inside F&O analytics
- Strategy Appstore, ready-made strategies and risk-first strategy cards
- Market View, Trader Outcome and Instrument Set filters
- Payoff, probability of profit, max profit, max loss, breakeven, margin benefit, SPAN and exposure
- Build strategy leg by leg with live risk recalculation
- Cross-instrument hedging across options, futures and stocks
- Scalper and Trading View saved templates
- Homepage customisation
- Sector heatmap, FII-DII, global indices, stock comparison and peer comparison
- Order notes, SL-TP modification, instant exit, OI alerts and volume alerts

Compare against retail competitors/tools where evidence exists:
- Sensibull
- Dhan
- Opstra
- AlgoTest
- TradingView
- StockEdge
- StockMock
- NiftyTrader
- Moneycontrol

Write the answer as a clean retail product analysis with this structure:

1. Executive Summary
   - Biggest product conclusions.
   - Which upcoming features are strongest.
   - Which areas still need clarity or packaging.

2. Upcoming Feature Map
   - Table columns: Feature, User problem solved, Nubra status/surface, Why it matters, Priority.

3. Community Demand Check
   - Table columns: Feature theme, What traders discuss, Demand strength, Evidence signal, Product read.
   - Explain whether the community actually needs this or whether it is mostly a packaging/education opportunity.

4. Competitor Benchmark
   - Table columns: Feature area, Competitors with similar capability, What they do, Nubra implication.
   - Do not claim competitor strength unless the evidence supports it.

5. What Looks Strong for Nubra
   - Highlight strongest advantages from the upcoming feature set.

6. What Is Still Missing or Needs Sharpening
   - Separate true product gaps from visibility, packaging, education and interpretation gaps.

7. Launch and Education Angles
   - Retail launch themes, demo ideas, webinar topics and messaging lines.
   - Do not include Now / Next / Later timelines, time allocation, delivery phases or effort planning.

8. Final Takeaway
   - 3 to 5 concise lines.

Rules:
- Retail only.
- Do not mention API users.
- Do not create a PDF or Markdown file.
- Show the full answer directly in chat using clean sections and tables.
- Treat source-document features as planned/upcoming unless the app context confirms they are already visible.
- Start directly with insights, not methodology.
- Do not include a product recommendation/timeline section.
