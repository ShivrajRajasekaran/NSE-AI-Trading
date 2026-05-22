"""
IV Rank & IV Percentile Calculator
Determines whether current IV is high or low relative to history.
Critical for options strategy selection.
"""

import statistics


def iv_rank(current_iv, iv_high_52w, iv_low_52w):
    """
    IV Rank: Where is current IV relative to 52-week range?
    Formula: (Current IV - 52w Low) / (52w High - 52w Low) × 100

    current_iv: Current implied volatility
    iv_high_52w: 52-week IV high
    iv_low_52w: 52-week IV low
    """
    if iv_high_52w == iv_low_52w:
        return {"error": "IV high and low cannot be same"}

    rank = ((current_iv - iv_low_52w) / (iv_high_52w - iv_low_52w)) * 100
    rank = max(0, min(100, rank))

    return {
        "iv_rank": round(rank, 1),
        "current_iv": current_iv,
        "iv_high_52w": iv_high_52w,
        "iv_low_52w": iv_low_52w,
        "environment": classify_iv_environment(rank),
    }


def iv_percentile(current_iv, historical_ivs):
    """
    IV Percentile: % of days in past year where IV was BELOW current level.
    More robust than IV Rank (not affected by single spike).

    current_iv: Current IV
    historical_ivs: List of daily IV values (ideally 252 trading days)
    """
    if not historical_ivs:
        return {"error": "Need historical IV data"}

    days_below = sum(1 for iv in historical_ivs if iv < current_iv)
    percentile = (days_below / len(historical_ivs)) * 100

    return {
        "iv_percentile": round(percentile, 1),
        "current_iv": current_iv,
        "days_analyzed": len(historical_ivs),
        "days_below_current": days_below,
        "iv_mean": round(statistics.mean(historical_ivs), 4),
        "iv_median": round(statistics.median(historical_ivs), 4),
        "iv_std": round(statistics.stdev(historical_ivs), 4) if len(historical_ivs) > 1 else 0,
        "environment": classify_iv_environment(percentile),
    }


def classify_iv_environment(rank_or_percentile):
    """Classify IV environment and recommend strategy type."""
    val = rank_or_percentile

    if val >= 80:
        return {
            "level": "VERY HIGH",
            "bias": "SELL premium",
            "strategies": [
                "Iron Condor",
                "Short Straddle",
                "Short Strangle",
                "Credit Spreads",
                "Jade Lizard",
            ],
            "avoid": ["Long options", "Debit spreads", "Naked longs"],
            "rationale": "IV is expensive — mean reversion likely, sell premium",
        }
    elif val >= 60:
        return {
            "level": "HIGH",
            "bias": "SELL premium (with caution)",
            "strategies": [
                "Iron Condor",
                "Credit Spreads",
                "Covered Call",
                "Cash Secured Put",
            ],
            "avoid": ["Buying OTM options"],
            "rationale": "IV elevated — favor selling but manage risk tighter",
        }
    elif val >= 40:
        return {
            "level": "MODERATE",
            "bias": "NEUTRAL — directional plays",
            "strategies": [
                "Vertical Spreads",
                "Calendars",
                "Diagonals",
                "Butterflies",
            ],
            "avoid": ["Naked selling (low premium)"],
            "rationale": "IV fair — use spreads for defined risk",
        }
    elif val >= 20:
        return {
            "level": "LOW",
            "bias": "BUY premium",
            "strategies": [
                "Long Straddle",
                "Long Strangle",
                "Debit Spreads",
                "Calendar (long vega)",
            ],
            "avoid": ["Selling premium (low reward)"],
            "rationale": "IV is cheap — buy options for expansion",
        }
    else:
        return {
            "level": "VERY LOW",
            "bias": "BUY premium aggressively",
            "strategies": [
                "Long Straddle",
                "Long Strangle",
                "Long Calls/Puts",
                "Back Spreads",
            ],
            "avoid": ["Any premium selling"],
            "rationale": "IV crushed — mean reversion UP likely, buy cheap options",
        }


def iv_term_structure(near_iv, mid_iv, far_iv):
    """
    Analyze IV term structure (contango vs backwardation).

    near_iv: Near-month IV
    mid_iv: Mid-month IV
    far_iv: Far-month IV
    """
    if near_iv < mid_iv < far_iv:
        structure = "CONTANGO (normal)"
        interpretation = "Market calm — no event fear, calendars favorable"
    elif near_iv > mid_iv > far_iv:
        structure = "BACKWARDATION (inverted)"
        interpretation = "Near-term fear — event risk, avoid selling near-month"
    else:
        structure = "MIXED"
        interpretation = "Uneven — possible event between specific months"

    return {
        "near_iv": near_iv,
        "mid_iv": mid_iv,
        "far_iv": far_iv,
        "structure": structure,
        "interpretation": interpretation,
        "calendar_trade": "Favorable" if near_iv > mid_iv else "Unfavorable",
    }


def iv_skew(otm_put_iv, atm_iv, otm_call_iv):
    """
    Analyze IV skew (put skew vs call skew).
    """
    put_skew = otm_put_iv - atm_iv
    call_skew = otm_call_iv - atm_iv

    if put_skew > 5 and call_skew < 2:
        interpretation = "Heavy put skew — market fears downside, hedging active"
    elif call_skew > 5 and put_skew < 2:
        interpretation = "Call skew — unusual, possible short squeeze or event"
    elif put_skew > 3:
        interpretation = "Normal put skew — standard fear premium"
    else:
        interpretation = "Flat skew — balanced market expectations"

    return {
        "otm_put_iv": otm_put_iv,
        "atm_iv": atm_iv,
        "otm_call_iv": otm_call_iv,
        "put_skew": round(put_skew, 2),
        "call_skew": round(call_skew, 2),
        "interpretation": interpretation,
    }


if __name__ == "__main__":
    print("=== IV RANK & PERCENTILE ANALYSIS ===\n")

    rank_result = iv_rank(current_iv=0.18, iv_high_52w=0.35, iv_low_52w=0.10)
    print(f"IV Rank: {rank_result['iv_rank']}%")
    print(f"Environment: {rank_result['environment']['level']}")
    print(f"Bias: {rank_result['environment']['bias']}")
    print(f"Strategies: {', '.join(rank_result['environment']['strategies'][:3])}")
    print()

    import random
    random.seed(42)
    hist_ivs = [random.uniform(0.10, 0.30) for _ in range(252)]
    pct_result = iv_percentile(current_iv=0.22, historical_ivs=hist_ivs)
    print(f"IV Percentile: {pct_result['iv_percentile']}%")
    print(f"Mean IV: {pct_result['iv_mean']} | Median: {pct_result['iv_median']}")
    print(f"Environment: {pct_result['environment']['level']}")
    print()

    term = iv_term_structure(near_iv=15.5, mid_iv=17.2, far_iv=18.8)
    print(f"Term Structure: {term['structure']}")
    print(f"Calendar Trade: {term['calendar_trade']}")
    print()

    skew = iv_skew(otm_put_iv=20.5, atm_iv=15.0, otm_call_iv=13.5)
    print(f"Put Skew: +{skew['put_skew']}% | Call Skew: {skew['call_skew']}%")
    print(f"Interpretation: {skew['interpretation']}")
