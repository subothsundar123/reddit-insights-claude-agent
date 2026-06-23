# Daily product insights

Use the Reddit Product Insights connector and create a clear product insights report from all locally saved data.

Use the synchronized dump as the primary community-signal foundation. Enrich it with current web research and strong product reasoning, reconcile recommendations with the Nubra feature catalog, and produce one cohesive overall report. Do not create separate “dump findings” and “external research findings” sections.

Load every verified dump and the latest Nubra feature catalog already saved in the shared local insights folder. Do not access GitHub from Claude Desktop. If no local data exists, tell the user to open Claude Code and run `/update-insights-data`.

Write the result as a clean product insights report. Use short, direct sentences and avoid generic AI explanations, repeated observations and long methodology sections. Lead with the insight and business implication. Every major signal must include practical product thinking and a suggested solution.

Use this simple structure:

1. Executive Summary
2. Most Discussed Topics and Product Response
3. Most Requested API Capabilities
4. Retail and API/Algo Discussion Split
5. Webinar Opportunities
6. Product Roadmap: Now, Next and Later
7. Existing Capabilities Users Are Missing
8. What Nubra Can Improve Now

For the topic and feature tables, include what users are discussing, why it matters from a product standpoint, Nubra's current coverage and the recommended action. If Nubra already has a requested capability, recommend discovery, documentation, examples or marketing instead of rebuilding it.

Do not treat Reddit score as unique demand. Separate explicit requests from general discussion and qualify internal or upcoming Nubra capabilities.

Use simple, clean English. Keep the report product-focused and solution-oriented. Include useful source links naturally where relevant. Do not create a separate strategy-builder section; incorporate related signals into feature and roadmap recommendations.

Show the complete report directly in Claude Chat using concise text and clean tables. Do not create, attach or save a PDF or Markdown report file.
