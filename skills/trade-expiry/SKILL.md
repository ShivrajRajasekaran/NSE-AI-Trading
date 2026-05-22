# Weekly Expiry Strategy — KARTHIK

## Trigger
`/trade expiry`

## What To Do

Weekly expiry analysis for all NSE indices. Fetch live OI data from NSE.

## Output Must Include

1. **This Week's Expiry Schedule**:
   - Tuesday: FinNifty
   - Wednesday: BankNifty
   - Thursday: Nifty
   - Friday: Sensex

2. **Max Pain Strikes** — for all indices

3. **Straddle vs Strangle Premium**:
   - ATM Straddle price = Expected Move for the week
   - Compare with ATR — is market pricing too much or too little movement?

4. **Expected Move** — derived from ATM straddle:
   - Nifty: ±[X] points
   - BankNifty: ±[X] points

5. **PCR Across Indices** — bullish/bearish/neutral reading

6. **OI-Based Support/Resistance**:
   - Highest PE OI strike = support
   - Highest CE OI strike = resistance
   - Shifts from previous day

7. **Recommended Expiry Week Strategy**:
   - Non-directional (if range-bound expected): Iron Condor / Strangle
   - Directional (if trend expected): Debit spread / Ratio spread
   - Specific strikes, premium, max P&L, breakevens

8. **0DTE (Expiry Day) Guidance**:
   - High gamma risk warning
   - Pin risk at max pain
   - Preferred expiry day strategies
   - Time decay acceleration curve
   - Square-off timing

## Expiry Week Behavior Patterns
- Monday: positioning, slow build
- Tuesday: FinNifty expiry — can be volatile for banking stocks
- Wednesday: BankNifty expiry — big moves in banking space
- Thursday: Nifty expiry — max pain gravitation, gamma squeeze risk
- Friday: Sensex expiry — lower liquidity

## Risk Warning
0DTE trading is extremely risky. Gamma is highest, small moves cause large P&L swings. Never put more than 1% of capital at risk on expiry day plays.
