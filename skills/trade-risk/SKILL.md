# Risk Assessment — KARTHIK

## Trigger
`/trade risk <TICKER>`

## What To Do

Risk-only deep assessment. No bullish bias — pure risk analysis.

## Output Must Include

1. **Beta vs Nifty50** — volatility relative to market
2. **Historical Max Drawdown** — 1Y, 3Y from peak
3. **Promoter Pledging %** — if applicable (red flag if >20%)
4. **Debt Situation** — Debt/Equity, interest coverage, credit rating (CRISIL/ICRA)
5. **Liquidity** — avg daily volume. Can you exit quickly?
6. **Scenario Analysis**:
   - Portfolio impact at -5%, -10%, -20% from current price
   - What catalyst could cause each scenario
7. **Position Sizing Matrix**:

| Portfolio Size | Max Risk (2%) | Position Size (2× ATR stop) |
|---|---|---|
| ₹50,000 | ₹1,000 | X shares |
| ₹1,00,000 | ₹2,000 | X shares |
| ₹5,00,000 | ₹10,000 | X shares |
| ₹10,00,000 | ₹20,000 | X shares |

8. **Circuit Filter Risk** — is stock in T2T group? (no intraday)
9. **F&O Ban Status** — currently in ban? Near ban threshold?
10. **Correlation Risk** — does this overlap with existing portfolio exposure?
11. **Event Calendar** — upcoming earnings, AGM, ex-dividend, bonus dates

## Risk Framework
- Max portfolio heat: 6% total open risk
- Sector concentration: max 20% in one sector
- Drawdown rules: -5% = reduce 50%, -10% = go flat, -15% = stop and audit
