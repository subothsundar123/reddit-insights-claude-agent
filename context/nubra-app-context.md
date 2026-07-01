# Nubra Android App - QA Context Map

> Baseline reference for design comparison, user-journey testing, and retail feature analysis.
> This document describes what exists and where it lives in the live app.

## Overview

| Field | Value |
|---|---|
| App | Nubra - Indian stock / F&O / commodities trading app (NSE / BSE / MCX) |
| App version | v1.1.90 |
| Active persona/mode | Investor |
| Crawled | 2026-06-29 |
| Device | Android, 1080 x 2392 portrait |

Baseline state:
- Portfolio -> Holdings (1): IDEA, Qty 48.
- Portfolio -> Positions (0): none.
- Orders -> all status tabs empty.
- Watchlist "Staging": empty.

## Global navigation

Persistent bottom bar:
- Explore -> "At a Glance" home
- Watchlist -> Watchlists
- Portfolio -> Holdings / Positions
- Orders -> Order book
- Compass -> Quicklinks + Mode overlay

Persistent top bar:
- Screen title
- AI sparkle entry on Watchlist and stock detail
- Global search
- Balance chip and profile avatar
- Index strip for NIFTY 50 and SENSEX

## Explore - At a Glance

Main sections:
- Index strip
- P&L summary card
- Quicklinks tile grid:
  - Option chain
  - Strategies
  - Scalper
  - Ask AI
  - Chart analyser
  - RSI/EMA Alerts
  - Options Heat Map
  - Commodities
- Discover Stocks
- Mutual Funds / IPOs / ETFs / G-Sec category row
- Volume & OI Shockers
- High Profitable Strategies

## Watchlist

Includes:
- Watchlist selector
- Add instruments
- Search Instruments / Create AI Conditions
- Recent searches
- Category filter chips

## Portfolio

Holdings:
- P&L summary
- Stocks / Mutual Funds / G-Sec sub-toggle
- Holding rows with AI badge, investment/current value, P&L, quantity and LTP
- Holding detail bottom sheet with Add, Exit, Pledge Holdings

Positions:
- Stocks & F&O / Commodities
- Empty-state when no positions exist

## Orders

Tabs:
- Stocks and F&O
- Commodities
- Mutual Funds

Status chips:
- Open
- Executed
- Rejected
- Cancelled
- likely GTT

## Compass overlay

Contains:
- Mode selector with Investor mode
- Quicklinks
- Home screen customization entry

Mode selector is important but incomplete: full list of personas/modes was not captured.

## Trading tools

### Option chain

Current capabilities:
- Mode dropdown: Option Buyer
- Filter
- Underlying selector
- Exchange dropdown
- Lot size
- Max Pain
- PCR
- Total Put
- Expiry dropdown
- Calls/Puts columns
- Strike ladder

Retail analysis implication:
- Strong base for option-chain customization, buyer/seller presets, OI/PCR/max-pain interpretation and one-click trade from chain.

### Strategies

Current capabilities:
- Pre-built / My Strategies tabs
- Strategy cards with:
  - Name
  - Number of legs
  - P&L
  - Trade button
  - Payoff
  - Max Profit
  - Breakeven
  - Max Loss
  - Funds required
  - Probability badge
- Create Strategy

Retail analysis implication:
- Existing surface already aligns with risk-first strategy appstore positioning.
- Future analysis should evaluate whether discovery, sorting, market-view filters and suitability guidance are strong enough.

### Scalper

Current capabilities:
- Landscape mode
- One-tap fast buy/sell ladder

Retail analysis implication:
- Useful for active traders but needs guardrails and clear risk controls.

### Ask AI

Current capabilities:
- Screen stocks
- Analyze

Retail analysis implication:
- Can become the interpretation layer for OI, IV, volume, FII-DII, sector movement, and strategy suitability.

### Chart analyser

Current capabilities:
- Chart tab
- F&O analytics tab
- OI / Volatility / Premium / Volume
- PCR
- Bottom action bar

Retail analysis implication:
- Core surface for the new F&O Analytics story.

### RSI/EMA Alerts

Current capabilities:
- Basic price alerts
- Technical alerts: RSI / SMA / EMA

Retail analysis implication:
- Can extend into OI, volume, IV, premium and option-chain alerts.

### Options Heat Map

Current capabilities:
- Volume & OI Shockers
- Index selector
- Volume/OI toggle
- Calls/Puts toggle
- Expiry dropdown
- Ranked option rows
- High Profitable Strategies Today
- Strategy cards with max profit, breakeven, max loss, funds required, probability and Trade button

Retail analysis implication:
- Existing dashboard already supports discovery from market signal to strategy idea.

### Commodities

Current capabilities:
- MCX commodity search
- Create AI Conditions
- Recent MCX searches
- Option-chain shortcuts

## Global search and stock detail

Stock detail includes:
- Chart / Details / F&O analytics tabs
- AI signal cards
- Option chain / Scalper / Strategies bottom action bar
- One-click toggle
- Buy/Sell buttons

Details tab includes:
- Fundamentals
- Financials
- Corporate actions
- Key ratios
- Shareholding pattern
- Profit & Loss

F&O analytics tab includes:
- Options dropdown
- OI / Volatility / Premium / Volume
- OI bar chart by strike
- Call/Put legend
- ATM line
- Filters and Reset

Retail analysis implication:
- Stock detail is the natural hub for every-stock F&O analytics and stock-to-strategy workflow.

## Order entry

Order ticket includes:
- Apply Preset
- Buy/Sell toggle
- Delivery/Intraday toggle
- Quantity stepper
- Market/price field
- Stoploss and Target Profit expansion
- Advanced Entry/Exit with Trigger and Iceberg
- Validity dropdown
- Required amount and Balance

Retail analysis implication:
- Existing order ticket already supports the future SL/TP and preset story.
- Analysis should check whether strategy margin/risk data reconciles with the order ticket before trade.

## Account and settings

Relevant features:
- Funds available
- Kill Switch
- Alerts
- Reports
- Flexible Brokerage Plan
- Learn with Nubra
- Support, tutorials and feedback

Retail analysis implication:
- Reports, alerts, order notes and trade review can become a broader trade-journal and learning loop.

## Confirmed new-build feature input

The following retail capabilities were confirmed as new-build/upcoming input on 2026-07-01. They must not be described as generally available until rollout is verified:

- Watchlists supporting up to 250 instruments with automatic refresh
- Saved OMS order presets
- Best-fill-price execution on NSE
- Instant withdrawal and instant fund addition up to ₹5 lakh
- Natural-language AI-generated scans
- Persona-based broker experience for Option Sellers, Option Buyers, Investors and OI Traders
- Flexible brokerage plan
- Chart analyser
- Scalper mode and one-click mode
- Strategy-level portfolios, P&L/risk-reward SL-TP and mixed-instrument time-series charts
- Quantity sizing by investment amount or available margin
- Strategy Appstore with 40+ pre-built strategies
- Two configurable iceberg modes
- Removal of unnecessary app-level price restrictions, subject to exchange and risk limits
- Technical and option-chain alerts
- Bid/ask visibility in option chain and on charts
- Saved option-chain filters and persona modes
- GTT and AMO
- Flexible order-type modification, including eligible iceberg conversions

Retail analysis implication:
- Treat “customised broker” as part of persona-based customisation, not as a separate feature.
- Compare each capability with community demand and competitor execution, and separate feature gaps from launch, visibility and education gaps.

## Open questions

- Mode selector list and effect of modes are not captured.
- Add funds flow not reviewed.
- Scalper live one-tap buttons not exercised.
- Kill Switch, 2FA, Change PIN, Logout, Pledge Holdings and Exit not activated.
- Orders status chips beyond Cancelled not fully captured.
