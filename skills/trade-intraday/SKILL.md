# Intraday Trading Analysis — KARTHIK

## Trigger
`/trade intraday <TICKER>`

## What To Do

Deep intraday-specific analysis for NSE stocks. Fetch live data via WebSearch.

## Output Must Include

1. **Opening Gap Analysis** — gap fill probability based on gap size vs ATR
2. **VWAP Position** — above/below, significance for bias
3. **ORB Levels** — 15-min and 30-min Opening Range high/low
4. **Intraday S/R** — Previous Day High/Low, Pivot Points (Classic + Camarilla)
5. **Volume Analysis** — current vs 20-day average volume
6. **F&O Data** — futures premium/discount, OI change, PCR
7. **3 Intraday Setups** — each with specific entry, stop, target, R:R
8. **Time-Based Trade Plan** by market phase:
   - 9:15–9:30: Opening range (observe)
   - 9:30–10:30: First trend move (best entries)
   - 10:30–12:00: Continuation/reversal
   - 12:00–1:30: Lunch zone (avoid)
   - 1:30–2:30: Secondary trend (FII/DII data impact)
   - 2:30–3:30: Power hour (momentum)
9. **India VIX Assessment** — impact on expected intraday range
10. **Square-off Reminder** — 3:10 PM latest, trailing stop instructions

## Intraday Risk Rules (Non-negotiable)
- Max 2% of capital per trade
- Max 3 trades if first 2 are losses (mandatory stop)
- Position size = (Capital × Risk%) / (Entry – Stop)
- Never add to losing position intraday
- Flag T2T stocks (no intraday allowed)

## Key Indicators To Check
- VWAP + 1SD, 2SD bands
- 9 EMA, 21 EMA
- Volume confirmation on every breakout
- India VIX (>20 = reduce size)
- Futures OI change + price (Long buildup / Short covering / etc.)
