# Swing Trading Analysis — KARTHIK

## Trigger
`/trade swing <TICKER>`

## What To Do

Swing trade analysis for 5–30 day holds on NSE stocks.

## Output Must Include

1. **Weekly and Daily Trend** — Stage analysis (Weinstein method)
2. **Pattern Identification** — VCP, Cup & Handle, base patterns, flag/pennant
3. **Relative Strength vs Nifty50** — outperforming or underperforming
4. **Fundamental Quality Score** — quick P/E, ROE, debt check
5. **FII/DII Ownership Trend** — rising or falling institutional interest
6. **3 Swing Setups** with specific entry TRIGGERS:
   - Not "buy at ₹X" — instead "buy WHEN price breaks ₹X on volume > 2x avg"
   - Entry, Stop (ATR-based), Target 1 (2:1 R), Target 2 (3:1 R)
   - Hold period estimate
7. **ATR-Based Position Sizing** — for ₹1L, ₹5L, ₹10L portfolios
8. **Staged Entry Plan** — 50% at breakout, 50% on pullback confirmation
9. **Trailing Stop Methodology** — move to BE at +1R, trail below EMA after +2R
10. **Exit Triggers** — time-based and technical invalidation

## Swing Risk Management
- Stop below swing low / pattern low
- Risk per trade: 1-1.5% of portfolio
- Stop = 2× ATR from entry
- Minimum target: 2:1 R, ideally 3:1 R
- Hold time: 5–30 days

## India-Specific Swing Factors
- Check results calendar — avoid holding through earnings unless thesis-based
- FII ownership trend (rising = bullish in bull market)
- Promoter buying = bullish signal; pledging = red flag
- Sector rotation: buy leaders of strongest NSE sector index
- RBI policy impact on banking stocks
- Budget season (Feb 1) themes: infra, defence, PSU
