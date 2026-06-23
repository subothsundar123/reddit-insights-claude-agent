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
        "Write in a concise insights-report tone: direct, product-focused and non-repetitive. "
        "For every major signal, explain the product implication and give a practical solution. "
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
        {key: row[key] for key in ("topic", "signal", "priority", "nubra_context", "solution", "horizon")}
        for row in result["product_opportunities"][:8]
    ]
    return {
        "sync": result["sync"],
        "sample": analysis["sample"],
        "methodology_note": analysis.get("methodology_note"),
        "topics": compact_topics,
        "feature_requests": compact_features,
        "product_opportunities": compact_opportunities,
        "webinar_opportunities": result["webinars"],
        "product_roadmap": result["roadmap"],
        "awareness_gaps": result["awareness_gaps"],
        "top_evidence": analysis["top_evidence"][:10],
        "report_markdown": result["report_markdown"],
        "report_path": result["report_path"],
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
                "Awareness, Documentation and Onboarding Gaps",
                "Evidence and Confidence",
            ],
            "rules": [
                "Lead with outcomes, not methodology",
                "Attach product thinking and a practical solution to every major signal",
                "Do not repeat the same insight across sections",
                "Keep paragraphs to two or three sentences",
                "Use Nubra only where product coverage or a solution is relevant",
                "Do not create a separate strategy-builder section",
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
        f"the last {days} days. Load all verified dumps currently saved in the shared local folder, then report freshness, "
        "retail/API-algo hot topics, explicit feature demand, Nubra coverage, "
        "webinar ideas, roadmap signals, awareness gaps, "
        "evidence and confidence. For every important signal, explain the product implication "
        "and recommend a practical solution. Use the dump as the primary signal, enrich it with "
        "current web research and product reasoning, reconcile it with the Nubra feature "
        "catalog, and present one cohesive product-insights analysis rather than separate source sections. "
        "Use the returned report_markdown as the editorial foundation. Keep it concise, "
        "avoid repetition and do not add a separate strategy-builder section."
    )

def main() -> None:
    mcp.run()

if __name__ == "__main__": main()
