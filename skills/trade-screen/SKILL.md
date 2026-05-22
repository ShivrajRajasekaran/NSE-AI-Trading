# Stock Screener — KARTHIK

## Trigger
`/trade screen <CRITERIA>`

## Criteria Options
- `momentum breakout` — stocks breaking 52WH or multi-month resistance
- `value buy` — low P/E, high ROE, strong fundamentals
- `IV crush plays` — high IVR stocks post-event (sell premium)
- `pre-earnings` — stocks reporting this week with options setups
- `52-week high` — new highs with volume confirmation
- `VCP` — Volatility Contraction Patterns (Minervini)
- `oversold reversal` — RSI <30, at support, reversal candle
- `FII accumulation` — stocks with rising FII ownership
- `dividend yield` — high yield, sustainable payout
- `short squeeze` — high short interest + bullish trigger

## Output Format

For each stock (5-8 stocks per screen):

```
[RANK]. [TICKER] — [Company Name]
   Price: ₹[X] | Signal: [BUY/WATCH] | Score: [X]/100
   Key Metric: [The ONE reason this is on the list]
   Entry: ₹[X] | Stop: ₹[X] | Target: ₹[X]
   R:R: [X]:1 | Lot Size (F&O): [X]
```

Ranked by setup quality (best first).

## Rules
- Only include stocks with clear, actionable setups
- Every stock must have entry/stop/target
- Flag T2T and F&O ban stocks
- Include volume confirmation status
- Check for upcoming events that could impact the setup
