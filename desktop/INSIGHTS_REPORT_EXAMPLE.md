# Insights Report Writing Example

Use this only as a style and quality reference. Replace all numbers and findings with the current evidence.

## Executive Summary

1. **WebSocket reliability remains a trust issue.** Users evaluate an API not only by available streams but by reconnect behaviour and visibility during failures. **Product response:** publish a stream-level health dashboard and add recovery examples to the SDK.
2. **Historical-data demand is partly a discovery problem.** Users are unsure about available instruments, intervals and date ranges. **Product response:** create a coverage directory and availability endpoint, with a requirement box that can also act as a lead-acquisition channel.
3. **Users want usable analytics over raw fields.** Option chain, OI and Greeks are valuable, but decisions require scenarios, costs and liquidity context. **Product response:** add payoff, IV-rank, slippage and liquidity analytics through the SDK and MCP.

## Most Discussed Topics and Product Response

| Topic | Discussion | Product thinking | Suggested solution |
|---|---|---|---|
| API reliability | Users discuss disconnects, latency and recovery behaviour. | Reliability must be visible and diagnosable to earn developer trust. | Public health dashboard, incident history, heartbeat guidance and reconnect examples. |
| Historical data | Users ask what data exists and whether it is suitable for backtesting. | Coverage clarity is part of the product experience. | Coverage directory, availability endpoint and backtest-ready examples. |

## Product Roadmap

| Horizon | Recommendation |
|---|---|
| Now | Improve discovery of existing APIs, publish coverage information and create production-ready examples. |
| Next | Add advanced analytics and package connected SDK/MCP workflows. |
| Later | Evaluate advanced execution and scenario tooling after focused customer discovery. |

### Writing rules demonstrated

- State the signal first.
- Explain why it matters.
- Give a concrete product response.
- Do not repeat the same point in multiple sections.
- Avoid vague phrases such as “enhance the experience” without explaining how.
- Keep the report useful for product analysis and decision-making.
