"""
Stock Screener Engine for NSE/BSE
Filters stocks by momentum, value, volume, FII accumulation, VCP patterns.
Works with structured data input (JSON/dict format).
"""


def momentum_screen(stocks, min_rs=70, min_adx=25, above_200dma=True):
    """
    Momentum screener: Relative Strength + ADX + Moving Average filter.

    stocks: list of dicts with keys:
        - ticker, rs_rank (0-100), adx, price, dma_200, volume_avg, sector
    """
    results = []
    for s in stocks:
        if s.get("rs_rank", 0) < min_rs:
            continue
        if s.get("adx", 0) < min_adx:
            continue
        if above_200dma and s.get("price", 0) <= s.get("dma_200", float("inf")):
            continue

        score = 0
        score += min(30, s.get("rs_rank", 0) * 0.3)
        score += min(20, s.get("adx", 0) * 0.8)
        if s.get("price", 0) > s.get("dma_50", 0):
            score += 15
        if s.get("volume_ratio", 1) > 1.5:
            score += 15
        if s.get("price_change_1m", 0) > 5:
            score += 10
        if s.get("sector_rs", 0) > 60:
            score += 10

        results.append({**s, "momentum_score": round(score, 1)})

    return sorted(results, key=lambda x: x["momentum_score"], reverse=True)


def value_screen(stocks, max_pe=25, min_roe=15, max_debt_equity=1.0):
    """
    Value screener: P/E + ROE + Debt/Equity.

    stocks: list of dicts with keys:
        - ticker, pe, roe, debt_equity, roce, promoter_holding, dividend_yield
    """
    results = []
    for s in stocks:
        if s.get("pe", float("inf")) > max_pe:
            continue
        if s.get("roe", 0) < min_roe:
            continue
        if s.get("debt_equity", float("inf")) > max_debt_equity:
            continue

        score = 0
        pe = s.get("pe", 25)
        if pe < 10:
            score += 30
        elif pe < 15:
            score += 25
        elif pe < 20:
            score += 15
        else:
            score += 5

        roe = s.get("roe", 0)
        score += min(25, roe * 1.0)

        if s.get("roce", 0) > 20:
            score += 15
        if s.get("promoter_holding", 0) > 60:
            score += 10
        if s.get("dividend_yield", 0) > 2:
            score += 10
        if s.get("debt_equity", 1) < 0.3:
            score += 10

        results.append({**s, "value_score": round(score, 1)})

    return sorted(results, key=lambda x: x["value_score"], reverse=True)


def vcp_screen(stocks, max_contraction_pct=5, min_base_weeks=4):
    """
    VCP (Volatility Contraction Pattern) screener — Mark Minervini style.

    stocks: list of dicts with keys:
        - ticker, contraction_pct (current range as % of price),
        - base_weeks, volume_dry_up (bool), above_150dma (bool),
        - rs_rank, prev_uptrend (bool)
    """
    results = []
    for s in stocks:
        if s.get("contraction_pct", 100) > max_contraction_pct:
            continue
        if s.get("base_weeks", 0) < min_base_weeks:
            continue
        if not s.get("above_150dma", False):
            continue
        if not s.get("prev_uptrend", False):
            continue

        score = 0
        contraction = s.get("contraction_pct", 10)
        if contraction < 3:
            score += 30
        elif contraction < 5:
            score += 20
        else:
            score += 10

        if s.get("volume_dry_up", False):
            score += 25
        if s.get("rs_rank", 0) > 80:
            score += 20
        if s.get("base_weeks", 0) >= 8:
            score += 15
        if s.get("tight_closes", 0) >= 3:
            score += 10

        results.append({**s, "vcp_score": round(score, 1)})

    return sorted(results, key=lambda x: x["vcp_score"], reverse=True)


def fii_accumulation_screen(stocks, min_fii_change=1.0, min_quarters=2):
    """
    FII/DII accumulation screener.

    stocks: list of dicts with keys:
        - ticker, fii_holding_pct, fii_change_qoq, dii_holding_pct,
        - quarters_increasing, delivery_pct, bulk_deals_recent (bool)
    """
    results = []
    for s in stocks:
        if s.get("fii_change_qoq", 0) < min_fii_change:
            continue
        if s.get("quarters_increasing", 0) < min_quarters:
            continue

        score = 0
        fii_change = s.get("fii_change_qoq", 0)
        if fii_change > 3:
            score += 30
        elif fii_change > 2:
            score += 20
        else:
            score += 10

        if s.get("quarters_increasing", 0) >= 4:
            score += 25
        elif s.get("quarters_increasing", 0) >= 3:
            score += 15
        else:
            score += 5

        if s.get("delivery_pct", 0) > 60:
            score += 20
        if s.get("bulk_deals_recent", False):
            score += 15
        if s.get("fii_holding_pct", 0) > 20:
            score += 10

        results.append({**s, "accumulation_score": round(score, 1)})

    return sorted(results, key=lambda x: x["accumulation_score"], reverse=True)


def volume_breakout_screen(stocks, min_volume_ratio=2.0, min_price_change=2.0):
    """
    Volume breakout screener — stocks with unusual volume and price movement.

    stocks: list of dicts with keys:
        - ticker, volume_today, volume_avg_20d, price_change_pct,
        - near_52w_high (bool), above_resistance (bool), sector
    """
    results = []
    for s in stocks:
        vol_ratio = s.get("volume_today", 0) / max(1, s.get("volume_avg_20d", 1))
        if vol_ratio < min_volume_ratio:
            continue
        if abs(s.get("price_change_pct", 0)) < min_price_change:
            continue

        score = 0
        if vol_ratio > 5:
            score += 30
        elif vol_ratio > 3:
            score += 20
        else:
            score += 10

        price_change = abs(s.get("price_change_pct", 0))
        if price_change > 5:
            score += 25
        elif price_change > 3:
            score += 15
        else:
            score += 5

        if s.get("near_52w_high", False):
            score += 20
        if s.get("above_resistance", False):
            score += 15
        if s.get("delivery_pct", 0) > 50:
            score += 10

        results.append({
            **s,
            "volume_ratio": round(vol_ratio, 1),
            "breakout_score": round(score, 1),
        })

    return sorted(results, key=lambda x: x["breakout_score"], reverse=True)


def composite_screen(stocks, weights=None):
    """
    Run all screeners and produce composite ranking.

    weights: dict with keys momentum, value, vcp, accumulation, volume
    """
    if weights is None:
        weights = {"momentum": 0.3, "value": 0.2, "vcp": 0.2, "accumulation": 0.2, "volume": 0.1}

    ticker_scores = {}

    momentum = momentum_screen(stocks)
    for i, s in enumerate(momentum):
        ticker_scores.setdefault(s["ticker"], {})["momentum_rank"] = i + 1

    value = value_screen(stocks)
    for i, s in enumerate(value):
        ticker_scores.setdefault(s["ticker"], {})["value_rank"] = i + 1

    vcp = vcp_screen(stocks)
    for i, s in enumerate(vcp):
        ticker_scores.setdefault(s["ticker"], {})["vcp_rank"] = i + 1

    fii = fii_accumulation_screen(stocks)
    for i, s in enumerate(fii):
        ticker_scores.setdefault(s["ticker"], {})["accumulation_rank"] = i + 1

    vol = volume_breakout_screen(stocks)
    for i, s in enumerate(vol):
        ticker_scores.setdefault(s["ticker"], {})["volume_rank"] = i + 1

    total_stocks = len(stocks)
    composite = []
    for ticker, ranks in ticker_scores.items():
        score = 0
        for key, weight in weights.items():
            rank = ranks.get(f"{key}_rank", total_stocks)
            normalized = (total_stocks - rank) / max(1, total_stocks - 1) * 100
            score += normalized * weight
        composite.append({"ticker": ticker, "composite_score": round(score, 1), "ranks": ranks})

    return sorted(composite, key=lambda x: x["composite_score"], reverse=True)


if __name__ == "__main__":
    print("=== NSE STOCK SCREENER ===\n")

    sample_stocks = [
        {"ticker": "RELIANCE", "rs_rank": 82, "adx": 30, "price": 2850, "dma_200": 2700, "dma_50": 2800,
         "pe": 28, "roe": 12, "debt_equity": 0.5, "roce": 14, "promoter_holding": 50,
         "volume_ratio": 1.8, "price_change_1m": 6, "sector_rs": 70, "sector": "Energy",
         "fii_holding_pct": 25, "fii_change_qoq": 1.5, "quarters_increasing": 3,
         "delivery_pct": 55, "contraction_pct": 4, "base_weeks": 6,
         "above_150dma": True, "prev_uptrend": True, "volume_dry_up": True,
         "volume_today": 5000000, "volume_avg_20d": 2000000, "price_change_pct": 3.2,
         "near_52w_high": True, "above_resistance": True},
        {"ticker": "TCS", "rs_rank": 75, "adx": 28, "price": 3800, "dma_200": 3600, "dma_50": 3750,
         "pe": 30, "roe": 45, "debt_equity": 0.1, "roce": 55, "promoter_holding": 72,
         "volume_ratio": 1.2, "price_change_1m": 4, "sector_rs": 65, "sector": "IT",
         "fii_holding_pct": 12, "fii_change_qoq": 0.5, "quarters_increasing": 1,
         "delivery_pct": 45, "contraction_pct": 3, "base_weeks": 5,
         "above_150dma": True, "prev_uptrend": True, "volume_dry_up": False,
         "volume_today": 1500000, "volume_avg_20d": 1200000, "price_change_pct": 1.5,
         "near_52w_high": False, "above_resistance": False},
        {"ticker": "TATAMOTORS", "rs_rank": 88, "adx": 35, "price": 950, "dma_200": 800, "dma_50": 900,
         "pe": 18, "roe": 22, "debt_equity": 0.8, "roce": 18, "promoter_holding": 46,
         "volume_ratio": 2.5, "price_change_1m": 12, "sector_rs": 80, "sector": "Auto",
         "fii_holding_pct": 18, "fii_change_qoq": 2.5, "quarters_increasing": 4,
         "delivery_pct": 62, "contraction_pct": 6, "base_weeks": 3,
         "above_150dma": True, "prev_uptrend": True, "volume_dry_up": False,
         "volume_today": 8000000, "volume_avg_20d": 3000000, "price_change_pct": 5.5,
         "near_52w_high": True, "above_resistance": True},
        {"ticker": "HDFCBANK", "rs_rank": 60, "adx": 22, "price": 1650, "dma_200": 1600, "dma_50": 1640,
         "pe": 19, "roe": 17, "debt_equity": 0.9, "roce": 3, "promoter_holding": 26,
         "volume_ratio": 1.0, "price_change_1m": 2, "sector_rs": 50, "sector": "Banking",
         "fii_holding_pct": 32, "fii_change_qoq": 1.2, "quarters_increasing": 2,
         "delivery_pct": 48, "contraction_pct": 2, "base_weeks": 10,
         "above_150dma": True, "prev_uptrend": False, "volume_dry_up": True,
         "volume_today": 4000000, "volume_avg_20d": 4500000, "price_change_pct": 0.8,
         "near_52w_high": False, "above_resistance": False},
        {"ticker": "BAJFINANCE", "rs_rank": 90, "adx": 40, "price": 7500, "dma_200": 6800, "dma_50": 7200,
         "pe": 35, "roe": 20, "debt_equity": 3.5, "roce": 4, "promoter_holding": 56,
         "volume_ratio": 2.0, "price_change_1m": 15, "sector_rs": 85, "sector": "NBFC",
         "fii_holding_pct": 22, "fii_change_qoq": 3.0, "quarters_increasing": 5,
         "delivery_pct": 70, "contraction_pct": 3.5, "base_weeks": 7,
         "above_150dma": True, "prev_uptrend": True, "volume_dry_up": True,
         "volume_today": 3000000, "volume_avg_20d": 1500000, "price_change_pct": 4.0,
         "near_52w_high": True, "above_resistance": True},
    ]

    print("--- Momentum Leaders ---")
    momentum = momentum_screen(sample_stocks)
    for s in momentum[:3]:
        print(f"  {s['ticker']}: Score {s['momentum_score']} | RS={s['rs_rank']} ADX={s['adx']}")

    print("\n--- Value Picks ---")
    value = value_screen(sample_stocks)
    for s in value[:3]:
        print(f"  {s['ticker']}: Score {s['value_score']} | PE={s['pe']} ROE={s['roe']}")

    print("\n--- FII Accumulation ---")
    fii = fii_accumulation_screen(sample_stocks)
    for s in fii[:3]:
        print(f"  {s['ticker']}: Score {s['accumulation_score']} | FII Δ={s['fii_change_qoq']}%")

    print("\n--- Volume Breakouts ---")
    vol = volume_breakout_screen(sample_stocks)
    for s in vol[:3]:
        print(f"  {s['ticker']}: Score {s['breakout_score']} | Vol={s['volume_ratio']}x")

    print("\n--- Composite Ranking ---")
    comp = composite_screen(sample_stocks)
    for i, s in enumerate(comp[:5], 1):
        print(f"  #{i} {s['ticker']}: Composite {s['composite_score']}")
