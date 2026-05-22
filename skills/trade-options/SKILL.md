# Options Strategy Analysis — KARTHIK

## Trigger
`/trade options <TICKER> <BULLISH/BEARISH/NEUTRAL>`

## What To Do

Deep options analysis for NSE F&O stocks. Fetch live options chain data via WebSearch (NSE India).

## Output Must Include

1. **Current IV, IVR, IV Percentile** — with interpretation
2. **IV Skew Analysis** — put skew vs call skew
3. **PCR and Max Pain** — current PCR, max pain strike
4. **OI Distribution** — identify OI walls at key strikes (support/resistance)
5. **3 Strategies Ranked** — by suitability given IV + directional bias:

For each strategy:
- Strategy name (Iron Condor, Bull Call Spread, Short Strangle, etc.)
- Exact strikes and expiry
- Premium received/paid
- Max Profit / Max Loss
- Breakeven(s)
- Greeks Profile: Delta, Theta/day, Vega
- Ideal exit condition
- Adjustment plan if trade goes against

6. **Theta Decay Schedule** — decay per day in last 7 days
7. **Event Risk Check** — earnings/RBI/FOMC within expiry window
8. **Hedging Recommendation** — if premium selling

## Strategy Selection Logic

| IV Environment | Bias | Preferred Strategies |
|---|---|---|
| IVR > 50 (High IV) | Bullish | Bull Put Spread, Jade Lizard |
| IVR > 50 (High IV) | Bearish | Bear Call Spread |
| IVR > 50 (High IV) | Neutral | Iron Condor, Short Strangle |
| IVR < 30 (Low IV) | Bullish | Long Call, Bull Call Spread, Calendar |
| IVR < 30 (Low IV) | Bearish | Long Put, Bear Put Spread |
| IVR < 30 (Low IV) | Neutral | Long Straddle (if event upcoming) |

## NSE-Specific Notes
- Weekly expiry: Nifty (Thu), BankNifty (Wed), FinNifty (Tue), Sensex (Fri)
- Lot sizes: Nifty 25, BankNifty 15, FinNifty 40
- SEBI margin rules: SPAN + Exposure margin
- Check F&O ban list before recommending any position
- Flag stocks near circuit limit
- Always mention capital required per lot
