Analyse Nubra marketing SEO keyword opportunities against product and community demand.

First refresh/read the local data:
- Preferred: call `get_seo_keywords` with `segment=retail`, `limit=25`, then call `run_daily_insights` for 30 days.
- Use `search_evidence` for the strongest returned themes, especially option chain, FII DII, PCR, max pain, charts, strategy builder, broker comparison, alerts, scanners and Nubra.

Optional examples:

```text
/seo-insights
/seo-insights segment=retail theme=option
/seo-insights segment=all theme=api
```

Return:
1. Executive Summary
2. Highest-Value SEO Opportunities
   - Keyword/cluster
   - Search intent
   - Volume/traffic signal
   - Competitor ranking
   - Nubra relevance
   - Recommended action
3. Product Feature Mapping
4. Competitor Page Gaps
5. Programmatic Page Opportunities
6. Webinar, Lead Magnet and Content Ideas
7. What to Prioritize Now

Rules:
- Do not treat keyword volume alone as demand.
- Combine SEO volume, competitor coverage, Nubra feature relevance and community signals.
- Keep it retail-first unless the user asks for API/algo.
- Use clean tables and short practical recommendations.
- Do not create a PDF or Markdown file. Show the answer directly in chat.
