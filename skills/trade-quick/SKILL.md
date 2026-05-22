# 60-Second Quick Snapshot — KARTHIK

## Trigger
`/trade quick <TICKER>`

## What To Do

Fast assessment. Do NOT launch subagents. Use WebSearch for live data. Keep output under 40 lines.

## Output Format

```
⚡ KARTHIK'S SNAPSHOT — [TICKER] ([Company Name])

  Score: [X]/100 ([Grade]) — [SIGNAL]
  Price: ₹[X] ([+/-X%] today)
  Trend: [One-line trend assessment]

  ✓ [Bull point 1]
  ✓ [Bull point 2]
  ✓ [Bull point 3]

  ✗ [Bear point 1]
  ✗ [Bear point 2]
  ✗ [Bear point 3]

  KARTHIK: "[One-line verdict — direct, honest, specific]"

  Top Setup: [Intraday or Swing setup in one line]
  Entry: ₹[X] | Stop: ₹[X] | Target: ₹[X] | R:R [X]:1

  Run /trade analyze [TICKER] for the full multi-dimension analysis
```

## Rules
- MAX 40 lines output
- No paragraphs — bullet points only
- Must include specific price levels (entry/stop/target)
- Fetch live price before responding
- Include India VIX if relevant
