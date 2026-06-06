# NSE-AI-Trading — Indian Master Trading Analyst

[![Skills](https://img.shields.io/badge/Skills-14-purple)]()
[![Market](https://img.shields.io/badge/Market-NSE%2FBSE%2FCrypto-orange)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blue)]()

**KARTHIK** — a 15+ year veteran trader persona for [Claude Code](https://claude.ai/code). Full Indian market analysis: NSE/BSE stocks, Nifty/BankNifty options, F&O strategies, intraday/swing setups, crypto, and sector rotation. 13 commands, one install.

---

## One-Click Install

### Windows (PowerShell)

```powershell
git clone https://github.com/ShivrajRajasekaran/NSE-AI-Trading.git && cd NSE-AI-Trading && powershell -ExecutionPolicy Bypass -File install.ps1
```

### Mac / Linux

```bash
git clone https://github.com/ShivrajRajasekaran/NSE-AI-Trading.git && cd NSE-AI-Trading && bash install.sh
```

---

## All 13 Commands

### Analysis & Research

| Command | What It Does |
|---------|-------------|
| `/trade analyze <ticker>` | Full 5-dimension analysis with Trade Score (0-100) |
| `/trade quick <ticker>` | 60-second snapshot — price, signal, top setup |
| `/trade intraday <ticker>` | Intraday setups: ORB, VWAP, levels, time-based plan |
| `/trade swing <ticker>` | Swing analysis (5-30 day holds) with staged entries |

### Options & Derivatives

| Command | What It Does |
|---------|-------------|
| `/trade options <ticker> <bias>` | Full options strategy: IV, PCR, OI, Greeks, 3 strategies ranked |
| `/trade expiry` | Weekly expiry: max pain, expected move, 0DTE strategies |

### Market Context

| Command | What It Does |
|---------|-------------|
| `/trade macro` | India macro: VIX, FII/DII, INR, crude, bonds, global context |
| `/trade sector <sector>` | Sector rotation: RS, flows, top picks, options plays |
| `/trade crypto <coin>` | Crypto: on-chain, funding rates, liquidations, trade plan |

### Research & Screening

| Command | What It Does |
|---------|-------------|
| `/trade screen <criteria>` | Stock screener: momentum, value, VCP, FII accumulation |
| `/trade compare <t1> <t2>` | Head-to-head comparison with clear winner |
| `/trade thesis <ticker>` | Investment thesis: bull/bear cases, catalysts, entry/exit |
| `/trade risk <ticker>` | Risk-only: drawdown, sizing, scenarios, circuit risk |

---

## Who Is KARTHIK?

A hardcoded master trader persona with 15+ years experience:
- Prop desk trader → ₹50 crore hedge fund PMS → 3 algo systems on NSE
- CFA Level 3, CMT, FRM certified
- Traded every cycle: 2008 crash, 2020 COVID, 2021 crypto bull, 2022 crypto winter
- Direct, brutally honest — every call has specific entry, stop, target
- Speaks in R-multiples, probability, and confluence

---

## Scoring System

| Score | Grade | Signal | Meaning |
|-------|-------|--------|---------|
| 85-100 | A+ | STRONG BUY | Highest conviction — full size |
| 70-84 | A | BUY | High probability — standard size |
| 55-69 | B | WATCH | Mixed — wait for trigger |
| 40-54 | C | NEUTRAL | No edge — stay flat |
| 25-39 | D | CAUTION | Risk > reward |
| 0-24 | F | AVOID | Major red flags |

---

## Coverage

### Indian Stocks (NSE/BSE)
- Technical: Price action, SMC/ICT, Wyckoff, Elliott Wave, harmonics, indicators
- Fundamental: P/E, ROE, ROCE, debt, promoter holding, FII/DII
- Options: Full Greeks, IV analysis, OI interpretation, 20+ strategies
- Intraday: ORB, VWAP, gap fills, sector momentum, power hour
- Swing: VCP, cup & handle, breakouts, relative strength, staged entries

### Options Mastery
- Weekly expiry for Nifty (Thu), BankNifty (Wed), FinNifty (Tue), Sensex (Fri)
- IV Rank/Percentile strategy selection
- PCR, Max Pain, OI walls
- Full strategies: Iron Condor, Straddle, Strangle, Spreads, Calendars, Ratio Spreads
- 0DTE guidance with gamma/pin risk awareness
- SEBI margin rules, lot sizes, F&O ban detection

### Crypto
- BTC dominance, altcoin seasons
- On-chain: exchange flows, whale alerts
- Derivatives: funding rates, OI, liquidation clusters
- India tax: 30% + 1% TDS reminder
- Exchange availability: CoinDCX, WazirX, Binance, Bybit

### Risk Management
- Position sizing (fixed %, Kelly, ATR-based)
- Portfolio heat max 6%
- Drawdown rules: -5% reduce, -10% flat, -15% stop
- Sector concentration limits
- F&O ban and T2T stock detection

---

## India-Specific Intelligence

| Factor | How KARTHIK Uses It |
|--------|-------------------|
| India VIX | Fear gauge — adjusts strategy selection |
| FII/DII Data | Institutional flow direction for Nifty bias |
| RBI MPC | Impact on banking, NBFC, real estate |
| Budget (Feb 1) | Theme identification: infra, defence, PSU |
| INR/USD | Export vs import sector rotation |
| Brent Crude | Energy, paints, airlines, logistics impact |
| 10Y Gsec | Rate-sensitive sector impact |
| SEBI Rules | F&O margins, circuit limits, ban periods |
| Expiry Cycles | Gamma, max pain, pin risk awareness |

---

## KARTHIK's Golden Rules

1. The trend is your employer — never fight it
2. Never risk more than 2% per trade
3. Cut losers fast, let winners run
4. Volume confirms everything — breakout without volume is a lie
5. IV rank decides the strategy
6. Check the weekly chart first
7. F&O expiry week is different
8. The market is not your friend on expiry day
9. In crypto, leverage kills — 3x max
10. No setup = no trade — waiting is a position

---

## Project Structure

```
NSE-AI-Trading/
├── trade/
│   └── SKILL.md              Main orchestrator (KARTHIK persona + routing)
├── skills/
│   ├── trade-analyze/        Full 5-dimension analysis
│   ├── trade-intraday/       Intraday setups & levels
│   ├── trade-options/        Options strategy (Greeks, IV, OI)
│   ├── trade-swing/          Swing trade analysis
│   ├── trade-crypto/         Crypto analysis
│   ├── trade-quick/          60-second snapshot
│   ├── trade-sector/         Sector rotation
│   ├── trade-risk/           Risk assessment
│   ├── trade-screen/         Stock screener
│   ├── trade-compare/        Head-to-head comparison
│   ├── trade-thesis/         Investment thesis
│   ├── trade-macro/          Market macro view
│   └── trade-expiry/         Weekly expiry strategy
├── scripts/
│   └── generate_trade_pdf.py PDF report generation
├── install.sh                Mac/Linux installer
├── install.ps1               Windows installer
├── uninstall.sh              Uninstaller
├── requirements.txt          Python deps (reportlab)
└── README.md
```

---

## Disclaimer

This tool is for educational and research purposes only. It does NOT constitute financial advice, a solicitation, or a recommendation to trade. All trading involves substantial risk of loss. SEBI regulations govern trading in Indian markets — ensure compliance. Crypto assets are highly volatile and largely unregulated in India; tax obligations apply (30% + 1% TDS). Always consult a SEBI-registered investment advisor before making financial decisions.

---

## Support

If this project helps your trading, consider supporting development:

<a href="https://buymeachai.ezee.li/ShivrajR369" target="_blank" rel="noopener noreferrer"><img src="https://buymeachai.ezee.li/assets/images/buymeachai-button.png" alt="Buy Me A Chai" width="200"></a>

---

## License

MIT

---

Built by [ShivrajRajasekaran](https://github.com/ShivrajRajasekaran) — Indian market mastery with KARTHIK persona.
