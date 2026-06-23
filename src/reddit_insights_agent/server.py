from __future__ import annotations

import base64

from mcp import types
from mcp.server.fastmcp import FastMCP
from .core import compare_periods, daily_insights, feature_lookup, local_root, search
from .pdf_report import generate_insights_pdf

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
        "After completing the analysis and any web research, call create_insights_pdf and return "
        "the PDF as the final report. Do not return or save a Markdown report. "
        "Do not display sync status, freshness, sample size, methodology or confidence. "
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
        "awareness_gaps": compact_awareness,
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
                "Awareness, Documentation and Onboarding Gaps",
            ],
            "rules": [
                "Lead with outcomes, not methodology",
                "Attach product thinking and a practical solution to every major signal",
                "Do not repeat the same insight across sections",
                "Keep paragraphs to two or three sentences",
                "Use Nubra only where product coverage or a solution is relevant",
                "Do not create a separate strategy-builder section",
                "Do not show freshness, sample size, methodology or confidence",
                "Create and return the final report as a PDF, not Markdown",
            ],
        },
    }


@mcp.tool()
def create_insights_pdf(
    executive_summary: list[str],
    topics: list[dict[str, str]],
    api_capabilities: list[dict[str, str]],
    segment_split: list[dict[str, str]],
    webinars: list[dict[str, str]],
    roadmap: dict[str, list[str]],
    awareness_gaps: list[str],
) -> types.CallToolResult:
    """Create and return the final Product Insights PDF after analysis and web research are complete."""
    report = {
        "executive_summary": executive_summary,
        "topics": topics,
        "api_capabilities": api_capabilities,
        "segment_split": segment_split,
        "webinars": webinars,
        "roadmap": roadmap,
        "awareness_gaps": awareness_gaps,
    }
    path = local_root() / "reports" / "reddit-product-api-user-insights.pdf"
    generate_insights_pdf(path, report)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    uri = path.as_uri()
    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text="The Product Insights PDF has been created and attached.",
            ),
            types.ResourceLink(
                type="resource_link",
                name=path.name,
                title="Reddit Product and API-User Insights",
                uri=uri,
                mimeType="application/pdf",
                size=path.stat().st_size,
            ),
            types.EmbeddedResource(
                type="resource",
                resource=types.BlobResourceContents(
                    uri=uri,
                    mimeType="application/pdf",
                    blob=encoded,
                ),
            ),
        ],
        structuredContent={
            "pdf_path": str(path),
            "file_name": path.name,
            "mime_type": "application/pdf",
        },
    )

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
        "webinar ideas, roadmap signals, awareness gaps, "
        "product opportunities and practical solutions. For every important signal, explain the product implication "
        "and recommend a practical solution. Use the dump as the primary signal, enrich it with "
        "current web research and product reasoning, reconcile it with the Nubra feature "
        "catalog, and present one cohesive product-insights analysis rather than separate source sections. "
        "Use the returned product opportunities and roadmap as the foundation. Use simple, clean English, keep it concise, "
        "avoid repetition and do not add a separate strategy-builder section. After the analysis and web research, "
        "call create_insights_pdf with the finished sections. Return the PDF instead of Markdown text."
    )

def main() -> None:
    mcp.run()

if __name__ == "__main__": main()
