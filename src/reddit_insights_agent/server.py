from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from .core import compare_periods, daily_insights, feature_lookup, search

mcp = FastMCP("reddit-product-insights")

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

def main() -> None:
    mcp.run()

if __name__ == "__main__": main()

