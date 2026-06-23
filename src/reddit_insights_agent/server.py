from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from .core import compare_periods, daily_insights, feature_lookup, search

mcp = FastMCP(
    "reddit-product-insights",
    instructions=(
        "This connector provides evidence-grounded Reddit product insights. "
        "When the user asks for daily insights, today's insights, hot topics, "
        "API demand, webinars, roadmap, or similar product analysis, call "
        "run_daily_insights first. That tool performs incremental synchronization "
        "before analysis, so do not ask the user to run a separate sync step. "
        "Preserve the retail versus API/algo split and all Nubra status qualifications."
    ),
)

@mcp.tool()
def run_daily_insights(days: int = 30) -> dict:
    """One-step operation: sync all missing dumps/catalog versions, import, analyze, save and return the daily product report."""
    return daily_insights(days)

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
        f"the last {days} days. Sync missing data first, then report freshness, "
        "retail/API-algo hot topics, explicit feature demand, Nubra coverage, "
        "webinar ideas, roadmap signals, awareness gaps, strategy-builder expectations, "
        "evidence and confidence. Offer relevant follow-up analyses at the end."
    )

def main() -> None:
    mcp.run()

if __name__ == "__main__": main()
