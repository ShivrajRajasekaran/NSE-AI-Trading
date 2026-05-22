# Full Multi-Dimensional Analysis — KARTHIK's Trading Desk

## Trigger
`/trade analyze <NSE:TICKER or CRYPTO>`

## What To Do

Run a complete 5-dimension analysis. Use WebSearch to gather live data from NSE, MoneyControl, TradingView, or CoinGecko.

## Output Format

```
╔══════════════════════════════════════════════════════════════╗
║  KARTHIK'S TRADING DESK                                      ║
║  [TICKER] — [Company Name / Crypto Name]                     ║
║  Market: NSE/BSE/CRYPTO | Segment: EQ/F&O/SPOT/PERP         ║
╚══════════════════════════════════════════════════════════════╝

MASTER TRADE SCORE: [X]/100 (Grade: [X]) | Signal: [SIGNAL]
India VIX: [X] | Market Regime: [Trending/Ranging/Volatile]

┌─────────────────────────┬───────┬────────┬──────────────┐
│ Dimension               │ Score │ Weight │ Assessment   │
├─────────────────────────┼───────┼────────┼──────────────┤
│ Technical Structure     │  XX   │  25%   │ [status]     │
│ Fundamental Quality     │  XX   │  20%   │ [status]     │
│ Options/Derivatives     │  XX   │  20%   │ [status]     │
│ Sentiment & Order Flow  │  XX   │  20%   │ [status]     │
│ Risk Profile            │  XX   │  15%   │ [status]     │
└─────────────────────────┴───────┴────────┴──────────────┘
```

## Analysis Sections (ALL required)

### 1. Technical Analysis
- Trend (Weekly/Daily/Hourly)
- Market Structure (HH-HL / LH-LL / Ranging)
- Price vs Key MAs (21/50/200 EMA)
- VWAP Position
- RSI(14), MACD, Supertrend
- India VIX interpretation
- Key Support/Resistance levels (₹)
- Chart Pattern + Volume Analysis
- Smart Money Zones: Order Blocks, FVGs

### 2. Options Analysis (F&O stocks only)
- ATM IV / IV Rank
- Put-Call Ratio → interpretation
- Max Pain Strike
- OI Build-up at key strikes
- Suggested Strategy with full setup
- Greeks Profile (Delta, Theta, Vega)
- Max Profit/Loss/Breakeven

### 3. Fundamental Snapshot
- P/E vs sector avg, PEG
- ROE/ROCE, Debt/Equity, FCF Yield
- Promoter Holding (change last quarter)
- FII/DII trends
- Upcoming triggers (earnings, events)

### 4. Intraday Plan
- Setup Type (ORB/VWAP reclaim/Momentum/Reversal)
- Entry Zone, Stop Loss, Target 1 & 2
- Risk/Reward ratio
- Position Size (for ₹1L capital, 1% risk)
- Time-based exit (3:10 PM)
- Invalidation conditions

### 5. Swing Plan
- Pattern/strategy name
- Entry trigger (specific condition, not just a price)
- Stop, Target 1, Target 2
- Hold period, trailing stop methodology
- Invalidation level

### 6. KARTHIK'S VERDICT
- 2-3 paragraphs of honest, direct assessment
- TOP 3 CATALYSTS
- TOP 3 RISKS
- MASTER SIGNAL: STRONG BUY / BUY / HOLD / AVOID / SHORT

## Rules
- Always fetch LIVE price data via web search before analysis
- All prices in ₹ for Indian stocks, USD for crypto
- Mention lot size and capital required for F&O recommendations
- Flag F&O ban stocks, T2T stocks, circuit limit risks
- Include DISCLAIMER at the end
