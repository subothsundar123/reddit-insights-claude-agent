# Connector Update: v2.5 Retail Feature Catalog

Published: 2026-07-01 17:25 IST

## What changed

- Expanded the deduplicated retail upcoming-feature catalog from 17 to 34 capabilities.
- Added new-build inputs covering watchlists, OMS presets, execution, funds, AI scans, brokerage, chart analysis, strategy-level risk and portfolios, alerts and advanced orders.
- Merged “customised broker” into the existing persona-based experience.
- Expanded `/new-feature-analysis` and the Claude Desktop `new_feature_analysis` prompt to evaluate the new capabilities against market demand and competitors.
- Added the confirmed 2026-07-01 feature input to the Nubra app context.

## How to update

From the connector folder, run:

```bash
git pull --ff-only origin main
.venv/bin/python -m pip install -e .
bash scripts/refresh-data.sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m reddit_insights_agent.cli status --refresh
```

If using Claude Desktop, restart Claude Desktop or toggle the `reddit-product-insights` connector off and on after the update.

## What to test

In Claude Code:

```text
/status
/new-feature-analysis
```

In Claude Desktop, open the `new_feature_analysis` prompt.
