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
        "Write like a practical internal product note prepared by a team member. "
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

@mcp.prompt()
def daily_product_insights(days: int = 30) -> str:
    """Reusable Claude Desktop prompt for the full daily product-insights workflow."""
    return (
        f"Run the Reddit Product Insights connector's complete daily workflow for "
        f"the last {days} days. Load all verified dumps currently saved in the shared local folder, then report "
        "retail/API-algo hot topics, explicit feature demand, Nubra coverage, "
        "webinar ideas, roadmap signals, existing capabilities users are missing, "
        "what Nubra can improve now, "
        "product opportunities and practical solutions. For every important signal, explain the product implication "
        "and recommend a practical solution. Use the dump as the primary signal, enrich it with "
        "current web research and product reasoning, reconcile it with the Nubra feature "
        "catalog, and present one cohesive product-insights analysis rather than separate source sections. "
        "Use the returned product opportunities and roadmap as the foundation. Use simple, clean English, keep it concise, "
        "avoid repetition and do not add a separate strategy-builder section. Show the full report directly "
        "in this chat using short text and clean tables. Do not create or attach a PDF or Markdown file."
    )


@mcp.prompt()
def feature_requests(days: int = 30) -> str:
    """Show the strongest feature requests found in the saved discussions."""
    return (
        f"Use run_daily_insights for the last {days} days and show the strongest feature requests. "
        "Separate explicit requests from general discussion. Use a table with Feature, User need, "
        "Nubra status and Recommended action. Check the Nubra catalogue before suggesting anything. "
        "If Nubra already has it, focus on visibility, examples or adoption instead of rebuilding it. "
        "Keep the wording short and natural, like an internal product note. Show the answer only in chat."
    )


@mcp.prompt()
def feature_gaps(days: int = 30) -> str:
    """Compare user demand with Nubra's existing feature coverage."""
    return (
        f"Use run_daily_insights for the last {days} days and compare the requested capabilities with "
        "the Nubra feature catalogue. Group them as Already available, Partly covered, Upcoming and Missing. "
        "For each item, explain the remaining user need and the next practical action. Include a separate short "
        "table for existing capabilities users are missing. Do not treat upcoming or unverified work as publicly available. "
        "Write like a product team member and show the answer only in chat."
    )


@mcp.prompt()
def trend_check(short_days: int = 7, long_days: int = 30) -> str:
    """Compare recent discussion signals with a longer period."""
    return (
        f"Use compare_insight_periods with {short_days} days and {long_days} days. Show what is rising, "
        "what is stable and what is declining across retail and API/algo discussions. Focus on meaningful changes, "
        "not raw Reddit score alone. Use a compact table with Topic, Direction, What changed and Product response. "
        "Keep the conclusions practical and show the answer only in chat."
    )


@mcp.prompt()
def improve_now(days: int = 30) -> str:
    """Find practical improvements Nubra can make now."""
    return (
        f"Use run_daily_insights for the last {days} days and prepare a section called What Nubra Can Improve Now. "
        "Give short, practical improvements across Product, SDK, MCP and Support. Base each action on a recurring "
        "user need and check whether Nubra already has relevant coverage. Use a table with Area, User problem, "
        "Improvement and Expected outcome. Avoid broad phrases and long explanations. Show the answer only in chat."
    )


@mcp.prompt()
def webinar_ideas(days: int = 30) -> str:
    """Turn repeated user questions into useful webinar ideas."""
    return (
        f"Use run_daily_insights for the last {days} days and suggest webinar ideas from repeated questions, "
        "confusion and feature demand. Use a table with Topic, Audience, User question, What to demonstrate and "
        "Relevant Nubra capability. Prefer topics that can educate users and improve product adoption. "
        "Do not invent demand that is not present in the data. Show the answer only in chat."
    )


@mcp.prompt()
def roadmap(days: int = 30) -> str:
    """Turn current discussion signals into a product roadmap view."""
    return (
        f"Use run_daily_insights for the last {days} days and prepare a simple Now, Next and Later roadmap. "
        "Consider recurring demand, user impact, Nubra's current coverage and whether the problem is product, "
        "SDK, MCP, support or discovery. Do not add an available feature as new roadmap work; recommend adoption "
        "or visibility improvements instead. Use one clean table and keep the reasoning direct. Show the answer only in chat."
    )

def main() -> None:
    mcp.run()

if __name__ == "__main__": main()
