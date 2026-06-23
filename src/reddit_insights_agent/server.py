from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from .core import compare_periods, daily_insights, feature_lookup, search

mcp = FastMCP(
    "reddit-product-insights",
    instructions=(
        "This connector provides evidence-grounded Reddit product insights. "
        "When the user asks for daily insights, today's insights, hot topics, "
        "API demand, webinars, roadmap, or similar product analysis, call "
        "run_daily_insights first. In Claude Desktop, that tool reads the verified dumps "
        "already saved in the shared local folder; GitHub updates are performed separately "
        "by Claude Code through /update-insights-data. "
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
        for row in analysis["topics"][:10]
    ]
    compact_features = [
        {key: row[key] for key in ("feature", "status", "mentions", "engagement")}
        for row in analysis["feature_requests"][:12]
    ]
    compact_opportunities = [
        {key: row[key] for key in ("topic", "signal", "priority", "product_thinking", "nubra_context", "solution", "horizon")}
        for row in result["product_opportunities"][:8]
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
        "top_evidence": analysis["top_evidence"][:10],
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
def search_evidence(query: str, limit: int = 20) -> list[dict]:
    """Search locally stored Reddit posts/comments and return evidence for a product claim."""
    return search(query, limit)

@mcp.tool()
def get_nubra_feature(query: str) -> list[dict]:
    """Check whether Nubra already has, partially has, plans, or lacks a capability."""
    return feature_lookup(query)

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
        "Always provide findings and recommendations; do not return a plan for doing the analysis. Use plain English and "
        "avoid generic phrases, filler, methodology explanations and repeated conclusions. Use short paragraphs and useful "
        "tables. Show the answer only in chat and do not create a report file."
    )


@mcp.prompt()
def daily_product_insights(days: int = 30) -> str:
    """Reusable Claude Desktop prompt for the full daily product-insights workflow."""
    return (
        f"Call run_daily_insights for the last {days} days and prepare the complete product review. "
        "Use this exact structure: 1. Executive Summary; 2. Most Discussed Topics and Product Response; "
        "3. Most Requested API Capabilities; 4. Retail and API/Algo Discussion Split; 5. Webinar Opportunities; "
        "6. Product Roadmap; 7. Existing Capabilities Users Are Missing; 8. What Nubra Can Improve Now. "
        "For each major topic, state the user problem, affected segment, signal in the data, product implication, "
        "Nubra's current coverage and the recommended response. Keep the executive summary to the most important "
        "decisions. Use tables for topics, requests, segments, webinars, roadmap and immediate improvements. "
        "Do not repeat the same recommendation across sections and do not add a separate strategy-builder section. "
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

def main() -> None:
    mcp.run()

if __name__ == "__main__": main()
