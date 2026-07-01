from __future__ import annotations

import pathlib

from mcp.server.fastmcp import FastMCP
from .core import (
    ask_insights,
    compare_periods,
    connector_status,
    daily_insights,
    feature_lookup,
    retail_upcoming_features,
    search,
    seo_keyword_catalog,
    sync,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]

mcp = FastMCP(
    "reddit-product-insights",
    instructions=(
        "This connector provides evidence-grounded product insights. "
        "For a natural-language question about users, products, features, competitors, "
        "content, roadmap or Nubra, call ask_product_insights first. For a complete daily "
        "review call run_daily_insights. Both paths validate local data, refresh stale data "
        "when possible and use cached analysis for speed. "
        "Preserve the retail versus API/algo split and all Nubra status qualifications. "
        "Use the synchronized dump as the primary community-signal foundation, then enrich "
        "the analysis with current web research and sound product reasoning when those "
        "capabilities are available. Produce one cohesive overall analysis rather than "
        "separate dump-versus-web sections. Reconcile feature ideas against the Nubra catalog, "
        "avoid unsupported certainty, and include useful source links naturally where relevant. "
        "Write in simple, clean English: direct, product-focused and non-repetitive. "
        "For every major signal, explain the product implication and give a practical solution. "
        "Return the complete report directly in Claude Chat using concise text and clean tables. "
        "Do not create, attach or save a PDF or Markdown report file. "
        "Do not display sync status, freshness, sample size, methodology or confidence. "
        "Start directly with useful insights, implications and practical actions. "
        "Do not produce generic AI commentary or a separate strategy-builder section."
    ),
)

@mcp.tool()
def run_daily_insights(days: int = 30) -> dict:
    """Load and analyze the verified local dumps as the primary input for a broader research-enriched product analysis."""
    result = daily_insights(days)
    policy = {
        "scope": "integrated_dump_web_reasoning",
        "primary_signal": "Synchronized Reddit dumps",
        "enrichment": "Current web research and product reasoning",
        "catalog_usage": "Reconcile recommendations with Nubra's existing, partial, upcoming and missing capabilities",
        "presentation": "One unified analysis; do not split findings into dump and external-research sections",
    }
    analysis = result["analysis"]
    compact_topics = [
        {key: row[key] for key in ("topic", "mentions", "engagement", "retail", "api_algo")}
        for row in analysis["topics"] if row["topic"] != "Other market discussion"
    ][:15]
    compact_features = [
        {key: row[key] for key in ("feature", "status", "mentions", "engagement")}
        for row in analysis["feature_requests"][:12]
    ]
    compact_opportunities = [
        {key: row[key] for key in ("topic", "signal", "priority", "product_thinking", "nubra_context", "solution", "horizon")}
        for row in result["product_opportunities"][:12]
    ]
    compact_awareness = [
        {key: row[key] for key in ("feature", "status", "mentions")}
        for row in result["awareness_gaps"][:5]
    ]
    return {
        "topics": compact_topics,
        "feature_requests": compact_features,
        "product_opportunities": compact_opportunities,
        "webinar_opportunities": result["webinars"],
        "product_roadmap": result["roadmap"],
        "existing_capabilities_users_are_missing": compact_awareness,
        "improve_now_inputs": {
            "product_opportunities": compact_opportunities[:5],
            "current_roadmap_actions": result["roadmap"].get("Now", [])[:6],
        },
        "emerging_topic_candidates": analysis.get("emerging_topic_candidates", [])[:10],
        "cross_topic_insights": analysis.get("cross_topic_insights", [])[:12],
        "competitor_signals": analysis.get("competitor_signals", [])[:10],
        "top_evidence": analysis["top_evidence"][:10],
        "feature_gap_matrix": result.get("feature_gap_matrix", [])[:12],
        "opportunity_scores": result.get("opportunity_scores", [])[:12],
        "trend_changes": result.get("trend_changes", {}).get("changes", [])[:12],
        "suggested_followups": [
            "Show evidence for the strongest signal.",
            "Compare the strongest opportunity with relevant competitors.",
            "Separate genuine product gaps from awareness and onboarding gaps.",
            "Turn the strongest user problem into a webinar and launch message.",
        ],
        "cache_hit": result.get("cache_hit", False),
        "analysis_policy": policy,
        "report_contract": {
            "tone": "Concise, clear and product-led insights",
            "required_sections": [
                "Executive Summary",
                "Most Discussed Topics and Product Response",
                "Most Requested API Capabilities",
                "Retail and API/Algo Discussion Split",
                "Webinar Opportunities",
                "Product Roadmap",
                "Existing Capabilities Users Are Missing",
                "What Nubra Can Improve Now",
                "Emerging Topics and New Ideas",
                "Competitor Signals",
            ],
            "rules": [
                "Lead with outcomes, not methodology",
                "Attach product thinking and a practical solution to every major signal",
                "Do not repeat the same insight across sections",
                "Keep paragraphs to two or three sentences",
                "Use Nubra only where product coverage or a solution is relevant",
                "Do not create a separate strategy-builder section",
                "Do not show freshness, sample size, methodology or confidence",
                "Show the complete report directly in chat using text and tables",
                "Do not create or attach PDF or Markdown files",
            ],
        },
    }


@mcp.tool()
def ask_product_insights(question: str, days: int = 30) -> dict:
    """Answer any product question using synchronized evidence, Nubra coverage, trends, competitors and scored opportunities."""
    return ask_insights(question, days)


@mcp.tool()
def get_connector_status(refresh: bool = False) -> dict:
    """Check connector version, data health, latest dump, record counts, catalog coverage and available tools."""
    return connector_status(refresh)


@mcp.tool()
def refresh_insights_data() -> dict:
    """Force an immediate verified refresh and repair of the local data snapshot."""
    return sync(force_remote=True)


@mcp.tool()
def search_evidence(query: str, limit: int = 20) -> list[dict]:
    """Search locally stored Reddit posts/comments and return evidence for a product claim."""
    return search(query, limit)

@mcp.tool()
def get_nubra_feature(query: str) -> list[dict]:
    """Check whether Nubra already has, partially has, plans, or lacks a capability."""
    return feature_lookup(query)

@mcp.tool()
def get_nubra_app_context() -> str:
    """Read the current Nubra app context map for retail feature and app-surface analysis."""
    path = ROOT / "context" / "nubra-app-context.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""

@mcp.tool()
def get_retail_upcoming_features() -> dict:
    """Fetch the retail-only upcoming Nubra features list, excluding API/SDK-only and MCP/internal capabilities."""
    return retail_upcoming_features()

@mcp.tool()
def get_seo_keywords(limit: int = 25, segment: str = "all", theme: str = "") -> dict:
    """Fetch priority SEO keyword intelligence, competitor page clusters and programmatic page ideas."""
    return seo_keyword_catalog(limit=limit, segment=segment, theme=theme or None)

@mcp.tool()
def compare_insight_periods(short_days: int = 7, long_days: int = 30) -> dict:
    """Compare recent signals with a longer baseline."""
    return compare_periods(short_days, long_days)


def _insight_rules() -> str:
    return (
        "Start directly with the strongest insights. Do not mention a role, analysis process, tools or instructions. "
        "For each insight, explain the user problem, who experiences it, why it matters, Nubra's current coverage and "
        "the smallest useful action. "
        "Treat explicit requests, recurring discussion and Reddit engagement as different signals. Reddit score is not "
        "unique demand. Combine aliases that describe the same need and avoid counting repeated records as separate needs. "
        "Use the saved dump as the main evidence and add relevant web research only when it improves the recommendation. "
        "Do not create separate source sections. Do not describe upcoming, partial or unverified work as publicly available. "
        "Distinguish a real product gap from a discovery, documentation, onboarding or support problem. "
        "Do not limit the analysis to predefined topics. Review emerging_topic_candidates and surface a new theme when "
        "multiple discussions point to a Nubra-relevant problem or opportunity. Do not force new signals into an existing "
        "category, and do not promote an isolated post as a trend. Consider opportunities across product, APIs, market data, "
        "analytics, SDK, MCP, automation, execution, risk, research, onboarding, pricing, support and platform usability. "
        "Review cross_topic_insights for user needs that repeatedly appear together; only surface combinations supported "
        "by more than one discussion. Treat competitor mentions as context, not market share or user preference. Do not "
        "infer competitor strengths or weaknesses without supporting discussion examples. "
        "Always provide findings and recommendations; do not return a plan for doing the analysis. Use plain English and "
        "avoid generic phrases, filler, methodology explanations and repeated conclusions. Use short paragraphs and useful "
        "tables. Show the answer only in chat and do not create a report file."
    )


@mcp.prompt()
def ask_product_question(question: str, days: int = 30) -> str:
    """Ask one product question using all relevant connector intelligence."""
    return (
        f'Call ask_product_insights with this question: "{question}" and days={days}. '
        "Answer the question directly before adding supporting detail. Use the returned evidence, "
        "feature-gap classification, opportunity score, trend changes, competitor context and Nubra "
        "coverage only where they materially improve the answer. Separate genuine build gaps from "
        "visibility, onboarding, documentation and support gaps. End with the most useful suggested "
        "follow-ups returned by the tool. "
        + _insight_rules()
    )


@mcp.prompt()
def connector_health() -> str:
    """Check whether the connector and its local intelligence store are ready."""
    return (
        "Call get_connector_status with refresh=false. Show a compact readiness table with connector "
        "version, status, latest dump, record count, feature count, last check and cache entries. "
        "If the status is not ready or issues are present, call refresh_insights_data once, then call "
        "get_connector_status again. State the exact remaining problem and next action. Do not produce "
        "a product-insights report."
    )


def _channel_focus_rules(channels: str, focus: str) -> str:
    channel_text = (channels or "all").strip().lower()
    focus_text = (focus or "both").strip().lower()
    return (
        f"Channel selection: {channel_text}. Focus selection: {focus_text}. "
        "Supported channels are all, reddit, youtube, github, hacker_news, broker_docs, manual_research and internal_catalog. "
        "The user may also pass comma-separated combinations such as reddit,youtube or youtube,github. "
        "If channels is all, use every available source in the synchronized dump plus the Nubra catalog. "
        "If a specific channel is selected, use only evidence from that channel plus the Nubra catalog for coverage checks. "
        "Map channel filters this way: reddit means Reddit posts/comments and Reddit research signals; youtube means YouTube Data API "
        "video/comment signals; github means GitHub public issues and repositories; hacker_news means Hacker News public search signals; "
        "broker_docs means public broker/API documentation pages; manual_research means manual web research and user-provided research notes; "
        "internal_catalog means Nubra feature catalog and app context only. "
        "Supported focus values are both, retail, api, new_features, content, competitors, pain_points, roadmap, webinars and lead_magnets. "
        "If focus is retail, exclude API/developer-only conclusions. If focus is api, exclude retail-only conclusions. "
        "If focus is new_features, emphasize upcoming Nubra feature demand and competitor comparison. If focus is content, webinars or "
        "lead_magnets, turn repeated questions and pain points into practical content ideas. If focus is competitors, emphasize competitor "
        "mentions and positioning without treating mention count as market share. If focus is pain_points, prioritize repeated complaints, "
        "confusion and workflow blockers. If focus is roadmap, translate signals into Now/Next/Later product actions. "
        "When a selected channel has little or no evidence, say so briefly and use the closest available selected evidence rather than inventing."
    )


@mcp.prompt()
def daily_product_insights(days: int = 30, channels: str = "all", focus: str = "both") -> str:
    """Reusable Claude Desktop prompt for daily product insights with channel and focus filters."""
    return (
        f"Call run_daily_insights for the last {days} days and prepare the complete product review. "
        + _channel_focus_rules(channels, focus) + " "
        "Use this exact structure: 1. Executive Summary; 2. Most Discussed Topics and Product Response; "
        "3. Most Requested API Capabilities; 4. Retail and API/Algo Discussion Split; 5. Webinar Opportunities; "
        "6. Product Roadmap; 7. Existing Capabilities Users Are Missing; 8. What Nubra Can Improve Now; "
        "9. Emerging Topics and New Ideas; 10. Competitor Signals. "
        "For each major topic, state the user problem, affected segment, signal in the data, product implication, "
        "Nubra's current coverage and the recommended response. Keep the executive summary to the most important "
        "decisions and call out meaningful changes from trend_changes. In the topic and roadmap tables, use the returned "
        "opportunity score as a prioritization aid and explain the user signal behind it. Use feature_gap_matrix to classify "
        "capabilities as Available, Partial, Upcoming, Missing or Needs verification. Attach representative evidence links "
        "to major conclusions. Inside the topic section, add a short related-topic table when cross_topic_insights reveal a meaningful "
        "combined need. Use tables for topics, requests, segments, webinars, roadmap and immediate improvements. "
        "Do not repeat the same recommendation across sections and do not add a separate strategy-builder section. End with "
        "the most useful suggested follow-up questions returned by the connector. "
        + _insight_rules()
    )


@mcp.prompt()
def feature_requests(days: int = 30) -> str:
    """Show the strongest feature requests found in the saved discussions."""
    return (
        f"Call run_daily_insights for the last {days} days and review the strongest feature requests. "
        "First consolidate different phrases that refer to the same capability. Separate direct requests from pain points "
        "that may need a different solution. Check the retail versus API/algo split and validate every leading request "
        "against the Nubra feature catalogue. Prioritize using recurrence, user impact, engagement and product relevance; "
        "do not rank by Reddit score alone. Start with three short product takeaways. Then use a table with Rank, Request, "
        "Primary segment, Demand signal, Underlying user need, Nubra coverage, Why it matters and Recommended action. "
        "End with the three requests worth validating next and state what should be learned from users before committing. "
        + _insight_rules()
    )


@mcp.prompt()
def feature_gaps(days: int = 30) -> str:
    """Compare user demand with Nubra's existing feature coverage."""
    return (
        f"Call run_daily_insights for the last {days} days and compare user demand with the Nubra feature catalogue. "
        "Classify each need as Already available, Partly covered, Upcoming, Missing or Needs verification. For every item, "
        "separate the requested capability from the remaining user problem. Decide whether the real gap is product scope, "
        "access, documentation, examples, discoverability, onboarding or support. Use a table with Capability, User need, "
        "Primary segment, Nubra status, What is still missing, Gap type and Recommended action. Then add a short section "
        "called Existing Capabilities Users Are Missing, with the specific visibility or adoption fix for each feature. "
        "Finish with the top three genuine product gaps and the top three adoption gaps so they are not mixed together. "
        + _insight_rules()
    )


@mcp.prompt()
def trend_check(short_days: int = 7, long_days: int = 30) -> str:
    """Compare recent discussion signals with a longer period."""
    return (
        f"Call compare_insight_periods with {short_days} days and {long_days} days. Compare the recent rate and share of "
        "discussion with the longer baseline; do not compare raw totals from unequal windows as if they were equivalent. "
        "Separate retail and API/algo movement and flag genuinely new themes. Use Rising, Stable, Declining or New only "
        "when the evidence supports the label. Start with the three changes that matter most. Then use a "
        "table with Topic, Segment, Direction, What changed, Likely user reason, Product implication and Recommended response. "
        "End with Watch next week: no more than three signals and what evidence would confirm that each trend is real. "
        + _insight_rules()
    )


@mcp.prompt()
def improve_now(days: int = 30) -> str:
    """Find practical improvements Nubra can make now."""
    return (
        f"Call run_daily_insights for the last {days} days and prepare What Nubra Can Improve Now. Review Product, SDK, "
        "MCP and Support separately, but recommend only actions supported by recurring user needs. For each problem, check "
        "whether an existing Nubra capability can solve it before proposing new build work. Prefer small changes that reduce "
        "friction quickly: better placement, clearer coverage, calculators, examples, reusable workflows, guided MCP actions "
        "or support routing. Use a table with Area, User problem, Current coverage, Improvement, Why now, Expected user "
        "outcome and Relative effort (Small, Medium or Large). Finish with the best three quick wins and explain why each "
        "should be done first. Do not call a large new product feature a quick win. "
        + _insight_rules()
    )


@mcp.prompt()
def webinar_ideas(days: int = 30) -> str:
    """Turn repeated user questions into useful webinar ideas."""
    return (
        f"Call run_daily_insights for the last {days} days and turn repeated questions, confusion and feature demand into "
        "webinar ideas. Choose topics that solve a real learning problem and can naturally demonstrate relevant Nubra "
        "capabilities. Avoid broad market commentary unless it leads to a useful product workflow. Use a table with Priority, "
        "Webinar title, Audience, User question, Learning outcome, Live demonstration, Relevant Nubra capability and Product "
        "outcome. After the table, give a practical outline for the top webinar: opening problem, three teaching sections, "
        "demo, questions and call to action. Suggest one adoption metric to watch after each webinar. "
        + _insight_rules()
    )


@mcp.prompt()
def roadmap(days: int = 30) -> str:
    """Turn current discussion signals into a product roadmap view."""
    return (
        f"Call run_daily_insights for the last {days} days and prepare a Now, Next and Later roadmap. Evaluate each signal "
        "using recurrence, affected segment, user impact, Nubra coverage, likely effort, dependencies and whether more "
        "discovery is needed. Separate new product work from adoption, documentation and support improvements. Do not place "
        "an already available feature on the build roadmap. Use a table with Horizon, User problem, Recommended action, "
        "Why this horizon, Nubra dependency, Expected outcome and Suggested success measure. Keep Now limited to work that "
        "can start with existing knowledge; use Next for validated larger work; use Later for uncertain or dependency-heavy "
        "ideas. Finish with Decisions needed, listing assumptions that require product or engineering confirmation. "
        + _insight_rules()
    )


@mcp.prompt()
def new_ideas(days: int = 30) -> str:
    """Find new Nubra-relevant topics and opportunities outside the usual categories."""
    return (
        f"Call run_daily_insights for the last {days} days and review both the known topics and "
        "emerging_topic_candidates. Find recurring user problems, workflows or ideas that are not already represented "
        "well by the standard topic list. Group related discussions into a clear new theme only when more than one signal "
        "supports it. Use a table with Emerging topic, Supporting signal, Affected segment, Why it matters for Nubra, "
        "Possible opportunity and What to validate next. Separate genuinely new product ideas from extensions to existing "
        "features. End with the two strongest ideas worth further discovery; return fewer if the evidence is weak. "
        + _insight_rules()
    )


@mcp.prompt()
def competitors(days: int = 30) -> str:
    """Review competitor mentions and the user needs discussed around them."""
    return (
        f"Call run_daily_insights for the last {days} days and review competitor_signals with their supporting examples "
        "and related topics. Show which platforms are mentioned, which segment mentions them, what user problem or workflow "
        "is being discussed and what Nubra can learn from the discussion. Use a table with Competitor, Discussion signal, "
        "Segment, Related need, Evidence example and Possible Nubra response. Do not treat mention count as market share, "
        "recommendation or sentiment. Do not label a competitor strength or weakness unless the supporting discussion says "
        "so clearly. End with no more than three competitive opportunities supported by repeated evidence. "
        + _insight_rules()
    )


@mcp.prompt()
def topic_links(days: int = 30) -> str:
    """Find product opportunities where user discussion themes repeatedly overlap."""
    return (
        f"Call run_daily_insights for the last {days} days and review cross_topic_insights. Keep only topic combinations "
        "supported by at least two separate discussions. Explain the common user workflow or problem connecting the topics, "
        "rather than simply listing two labels together. Use a table with Related topics, Supporting signal, Primary segment, "
        "Combined user need, Nubra coverage and Product opportunity. End with the strongest combined opportunities that "
        "would be missed if each topic were analysed separately. "
        + _insight_rules()
    )

@mcp.prompt()
def youtube_insights(days: int = 30) -> str:
    """Analyse YouTube text signals across retail and API/algo partitions."""
    return (
        f"Call run_daily_insights for the last {days} days and search_evidence for youtube, youtube_data_api, "
        "public_youtube_api, video_comment_thread, views_per_day, comments_per_day, Nubra API, Nubra trading app, "
        "option chain, broker API, websocket, strategy builder, payoff and algo trading. "
        "Use YouTube as a product-signal channel, not as a popularity contest. Separate retail signals from API/algo "
        "signals using the stored segment and platform partition. Focus on what comments reveal: feature requests, "
        "pain points, questions, competitor comparisons, repeated confusion and lead-magnet or webinar opportunities. "
        "Use video metrics only to understand reach and discussion intensity: views, comments, likes, views per day, "
        "comments per day, engagement rate, recent comments, feature-request count, pain-point count and question count. "
        "Do not mention thumbnails or media assets. "
        "Write the answer with this structure: "
        "1. Executive Summary; "
        "2. Retail YouTube Signals - table with Topic, User problem, Comment signal, Product implication, Nubra response; "
        "3. API/Algo YouTube Signals - table with Topic, Developer problem, Comment signal, Product implication, Nubra response; "
        "4. Videos/Channels Worth Tracking - explain why each matters using reach and discussion intensity; "
        "5. Competitor and Nubra Mentions - what users compare and what Nubra should learn; "
        "6. Content, Webinar and Lead-Magnet Ideas; "
        "7. Product Actions. "
        "If no YouTube records are available yet, say that the YouTube agent is ready but no YouTube dump has been synced, "
        "then list the exact data it will use once YOUTUBE_API_KEY is configured. "
        + _insight_rules()
    )

@mcp.prompt()
def seo_insights(limit: int = 25, segment: str = "retail", theme: str = "") -> str:
    """Use marketing SEO keywords to find content, product and competitor opportunities."""
    return (
        f"Call get_seo_keywords with limit={limit}, segment='{segment}' and theme='{theme}'. "
        "Also call run_daily_insights for 30 days and use search_evidence for the strongest SEO themes returned, especially "
        "option chain, FII DII, PCR, max pain, charts, strategy builder, broker comparison, alerts, scanners and Nubra. "
        "Connect SEO keyword opportunity with product and community evidence. Do not treat keyword volume alone as demand; "
        "combine volume, priority cluster, competitor coverage, Nubra feature relevance and user discussion signals. "
        "Write the answer with this structure: "
        "1. Executive Summary; "
        "2. Highest-Value SEO Opportunities - table with Keyword/cluster, Search intent, Volume/traffic signal, Competitor ranking, Nubra relevance, Recommended action; "
        "3. Product Feature Mapping - which Nubra existing/upcoming features each keyword can support; "
        "4. Competitor Page Gaps - what competitor pages exist and what Nubra should learn; "
        "5. Programmatic Page Opportunities - scalable pages worth creating; "
        "6. Webinar, Lead Magnet and Content Ideas; "
        "7. What to Prioritize Now. "
        "Keep it product and marketing focused. For retail segment, exclude API/developer-only conclusions unless the keyword explicitly relates to API/algo. "
        "Use clean tables and short practical recommendations. Do not create a file; show the answer directly in chat. "
        + _insight_rules()
    )

@mcp.prompt()
def retail_feature_research(days: int = 30) -> str:
    """Detailed retail analysis of upcoming Nubra features vs retail demand and competitors."""
    return (
        f"Call run_daily_insights for the last {days} days. Also call get_nubra_app_context. "
        "Start directly with the strongest insights and do not return a plan for doing the analysis. "
        "Use search_evidence for these exact retail-focused source/query terms as needed: "
        "retail_reddit_feature_research, nubra_feature_input, competitor_feature_research, "
        "market_expectation_research, Revamp Marketing Features, Strategies Appstore, FO Analytics on Nubra, "
        "Sensibull, Dhan, Opstra, AlgoTest, TradingView, StockEdge, IndiaOptionsSelling, IndianStockMarket, "
        "IndianStreetBets, payoff, strategy builder, F&O analytics, option chain, margin, OI, IV, PCR, max pain, "
        "straddle, strangle, premium, alerts, order notes, sector heatmap, FII-DII, stock comparison. "
        "Use only retail-focused evidence and feature inputs. Do not include API-user, developer, GitHub, SDK, MCP, "
        "broker API or technical platform analysis unless it directly affects a retail feature such as live data "
        "freshness, option-chain trust, or execution confidence. "
        "For FII/DII, distinguish ownership/shareholding-pattern data from daily or intraday FII-DII cash-market, "
        "derivatives participant-positioning and sector-flow views. Nubra's catalog can include FII/domestic "
        "institution ownership data under shareholding pattern, so do not mark FII/DII as completely missing. "
        "Only call out a gap if the missing item is a retail flow/participant-positioning surface or interpretation layer. "
        "Use the app context to connect each recommendation to current Nubra app surfaces: Explore, Watchlist, "
        "Portfolio, Orders, Compass, Option chain, Strategies, Scalper, Ask AI, Chart analyser, F&O analytics, "
        "RSI/EMA Alerts, Options Heat Map, Commodities, Stock detail and Order entry. "
        "Write a detailed product insight note with this exact structure: "
        "1. Executive Summary; "
        "2. What Retail Traders Are Discussing; "
        "3. Feature Coverage Table with columns Market expectation, Nubra has/planned, Current app surface, "
        "Competitors, Gap or improvement, Product priority; "
        "4. Competitor Comparison; "
        "5. What Nubra Should Highlight Strongly; "
        "6. What Nubra Is Missing or Should Improve; "
        "7. Now / Next / Later Product Priorities; "
        "8. Best Retail Messaging Angles; "
        "9. Final Takeaway. "
        "For Nubra capabilities from attached feature documents, say planned unless the app context confirms the "
        "feature is already visible. Separate true feature gaps from packaging, placement, visibility and explanation "
        "gaps. Show the complete answer directly in chat using clean sections and tables. Do not create a PDF or file. "
        "Do not mention methodology, sample size or confidence. Do not discuss API users."
    )

@mcp.prompt()
def new_feature_analysis(days: int = 30) -> str:
    """Retail-only analysis of Nubra's upcoming features against community demand and competitors."""
    return (
        f"Call get_retail_upcoming_features, run_daily_insights for the last {days} days, and get_nubra_app_context. "
        "Start directly with the strongest insights and do not return a plan for doing the analysis. "
        "Use search_evidence for retail-only signals around these upcoming feature themes: "
        "trader persona modes, Investor mode, Option Buyer mode, Option Seller mode, option-chain filters, "
        "custom option-chain layout, OI bars, PCR, Total Call OI, Total Put OI, Max Pain, ITM highlight, VWAP, "
        "premium, OI buildup, volume spike, IV, IV change, Greeks, bid-ask spread, OI concentration, one-click trade, "
        "F&O analytics, every-stock F&O analytics, OI vs spot, IV vs spot, premium vs spot, straddle premium, "
        "strangle premium, futures analytics by expiry, buy/sell actionables, strategy appstore, ready-made strategies, "
        "market view, trader outcome, instrument set, payoff, probability of profit, max profit, max loss, breakeven, "
        "margin benefit, SPAN, exposure, live risk update, leg-by-leg strategy builder, cross-instrument hedge, "
        "40+ pre-built strategies, scalper mode, saved TradingView templates, homepage customisation, "
        "250-instrument auto-refresh watchlists, OMS order presets, best-fill-price execution on NSE, instant fund "
        "addition and withdrawal, natural-language AI scans, flexible brokerage, chart analyser, strategy-level "
        "portfolios, strategy-level P&L and risk-reward SL-TP, quantity sizing by amount or margin, two iceberg modes, "
        "app-level price restrictions, technical alerts, option-chain alerts, mixed-instrument strategy time-series, "
        "GTT, AMO, flexible order-type modification, bid-ask on option chain and bid-ask on charts, "
        "sector heatmap, FII-DII, global indices, stock comparison, peer comparison, order notes and instant exit. "
        "Use only retail-focused evidence. Do not include API users, SDK, MCP, GitHub developer repositories, "
        "broker API, WebSocket API or technical platform analysis. If technical reliability affects a retail feature, "
        "translate it into retail terms such as live data freshness, execution confidence or option-chain trust. "
        "Treat every upcoming feature as planned/upcoming unless get_nubra_app_context clearly confirms it is already "
        "visible in the current app. Separate true feature gaps from visibility, packaging, education and interpretation gaps. "
        "For competitor comparison, focus on retail brokers/tools such as Sensibull, Dhan, Opstra, AlgoTest, TradingView, "
        "StockEdge, StockMock, NiftyTrader and Moneycontrol where evidence exists. Do not claim competitor strength without "
        "a supporting signal. "
        "Write the answer with this exact structure: "
        "1. Executive Summary - the biggest retail product conclusions; "
        "2. Upcoming Feature Map - table with Feature, User problem solved, Nubra status/surface, Why it matters, Priority; "
        "3. Community Demand Check - table with Feature theme, What traders discuss, Demand strength, Evidence signal, Product read; "
        "4. Competitor Benchmark - table with Feature area, Competitors with similar capability, What they do, Nubra implication; "
        "5. What Looks Strong for Nubra - strongest advantages from the upcoming set; "
        "6. What Is Still Missing or Needs Sharpening - practical gaps, interpretation gaps and packaging gaps; "
        "7. Launch and Education Angles - messages, demos and webinar topics that can be used without timeline allocation; "
        "8. Final Takeaway - 3 to 5 clean lines. "
        "Keep the output direct, product-led and useful for a retail product/marketing discussion. Use clean tables and short "
        "paragraphs. Do not include Now/Next/Later, time allocation, roadmap timing, delivery phases or effort planning. "
        "Do not mention methodology, sample size, confidence or tool calls. Do not create a PDF or Markdown file; "
        "show the complete answer directly in chat."
    )

def main() -> None:
    mcp.run()

if __name__ == "__main__": main()
