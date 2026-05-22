"""
Pre-Earnings Analysis Engine for NSE
Calculates implied moves, IV crush expectations, historical earnings reactions,
and recommends options strategies around results announcements.
"""

import math


def pre_earnings_analysis(spot, atm_iv, historical_moves, dte, strike_data=None):
    """
    Complete pre-earnings analysis.

    spot: Current stock price
    atm_iv: Current ATM implied volatility (e.g., 0.35 for 35%)
    historical_moves: list of past earnings moves as % (e.g., [3.5, -2.1, 5.0, ...])
    dte: Days to expiry (from earnings date)
    strike_data: optional list of dicts with keys: strike, call_iv, put_iv
    """
    implied_move = calculate_implied_move(spot, atm_iv, dte)
    historical = analyze_historical_moves(historical_moves)
    iv_crush = estimate_iv_crush(atm_iv, historical_moves, dte)
    strategies = recommend_earnings_strategies(implied_move, historical, iv_crush, spot, atm_iv)

    skew = None
    if strike_data:
        skew = analyze_earnings_skew(strike_data, spot)

    return {
        "spot": spot,
        "atm_iv": atm_iv,
        "dte": dte,
        "implied_move": implied_move,
        "historical": historical,
        "iv_crush": iv_crush,
        "strategies": strategies,
        "skew": skew,
        "verdict": generate_verdict(implied_move, historical, iv_crush),
    }


def calculate_implied_move(spot, iv, dte):
    """
    Expected move priced by options market.
    Formula: Spot × IV × sqrt(DTE/365) × 0.85 (straddle approximation)
    """
    expected = spot * iv * math.sqrt(dte / 365)
    straddle_move = expected * 0.85  # Straddle approximation

    return {
        "expected_move_pts": round(expected, 2),
        "expected_move_pct": round((expected / spot) * 100, 2),
        "straddle_move_pts": round(straddle_move, 2),
        "straddle_move_pct": round((straddle_move / spot) * 100, 2),
        "upper_range": round(spot + straddle_move, 2),
        "lower_range": round(spot - straddle_move, 2),
        "interpretation": f"Market expects ±{round((straddle_move/spot)*100, 1)}% move on results",
    }


def analyze_historical_moves(moves):
    """Analyze past earnings day reactions."""
    if not moves:
        return {"error": "No historical data"}

    abs_moves = [abs(m) for m in moves]
    positive = [m for m in moves if m > 0]
    negative = [m for m in moves if m < 0]

    avg_move = sum(abs_moves) / len(abs_moves)
    max_up = max(moves) if moves else 0
    max_down = min(moves) if moves else 0
    up_pct = (len(positive) / len(moves)) * 100

    # Recent trend (last 4 quarters)
    recent = moves[-4:] if len(moves) >= 4 else moves
    recent_avg = sum(abs(m) for m in recent) / len(recent)
    recent_bias = sum(recent) / len(recent)

    return {
        "quarters_analyzed": len(moves),
        "avg_absolute_move": round(avg_move, 2),
        "max_up": round(max_up, 2),
        "max_down": round(max_down, 2),
        "up_probability": round(up_pct, 1),
        "down_probability": round(100 - up_pct, 1),
        "recent_4q_avg": round(recent_avg, 2),
        "recent_bias": "BULLISH" if recent_bias > 0.5 else "BEARISH" if recent_bias < -0.5 else "NEUTRAL",
        "last_4_moves": recent,
    }


def estimate_iv_crush(current_iv, historical_moves, dte):
    """
    Estimate post-earnings IV crush.
    IV typically drops 30-60% after earnings depending on pre-event inflation.
    """
    avg_hist_move = sum(abs(m) for m in historical_moves) / len(historical_moves) if historical_moves else 3

    # IV crush estimate based on how inflated IV is vs realized moves
    realized_vol = (avg_hist_move / 100) * math.sqrt(252)  # Annualized from daily
    iv_premium = current_iv / realized_vol if realized_vol > 0 else 1

    if iv_premium > 2.0:
        crush_pct = 55
        crush_rating = "SEVERE"
    elif iv_premium > 1.5:
        crush_pct = 40
        crush_rating = "HIGH"
    elif iv_premium > 1.2:
        crush_pct = 30
        crush_rating = "MODERATE"
    else:
        crush_pct = 20
        crush_rating = "LOW"

    post_earnings_iv = current_iv * (1 - crush_pct / 100)

    return {
        "current_iv": round(current_iv * 100, 1),
        "estimated_post_iv": round(post_earnings_iv * 100, 1),
        "crush_pct": crush_pct,
        "crush_rating": crush_rating,
        "iv_premium_ratio": round(iv_premium, 2),
        "interpretation": f"IV likely drops ~{crush_pct}% post-earnings ({crush_rating} crush)",
    }


def recommend_earnings_strategies(implied_move, historical, iv_crush, spot, iv):
    """Recommend options strategies based on earnings analysis."""
    strategies = []

    hist_avg = historical.get("avg_absolute_move", 3)
    impl_move_pct = implied_move["straddle_move_pct"]

    # Case 1: Implied move > historical — options are overpriced → SELL
    if impl_move_pct > hist_avg * 1.2:
        strategies.append({
            "strategy": "Short Straddle / Iron Butterfly",
            "bias": "NEUTRAL",
            "logic": f"Implied {impl_move_pct}% > Historical {hist_avg}% — options overpriced, sell premium",
            "risk": "Uncapped risk on straddle; use butterfly for defined risk",
            "breakeven": f"±₹{implied_move['straddle_move_pts']} from {spot}",
            "edge": "IV CRUSH",
            "confidence": "HIGH" if impl_move_pct > hist_avg * 1.5 else "MODERATE",
        })
        strategies.append({
            "strategy": "Iron Condor (wide wings)",
            "bias": "NEUTRAL",
            "logic": "Collect premium, expect stock to stay within implied range",
            "risk": "Defined — max loss is wing width minus premium",
            "confidence": "HIGH",
        })

    # Case 2: Implied move < historical — options are cheap → BUY
    if impl_move_pct < hist_avg * 0.8:
        strategies.append({
            "strategy": "Long Straddle / Strangle",
            "bias": "NEUTRAL (volatility play)",
            "logic": f"Implied {impl_move_pct}% < Historical {hist_avg}% — options underpriced",
            "risk": "Premium paid = max loss",
            "edge": "REALIZED VOL > IMPLIED VOL",
            "confidence": "MODERATE",
        })

    # Case 3: Directional bias from history
    if historical.get("up_probability", 50) > 65:
        strategies.append({
            "strategy": "Bull Call Spread (post-earnings)",
            "bias": "BULLISH",
            "logic": f"{historical['up_probability']}% of past earnings were positive",
            "risk": "Premium paid = max loss",
            "confidence": "MODERATE",
        })
    elif historical.get("down_probability", 50) > 65:
        strategies.append({
            "strategy": "Bear Put Spread (post-earnings)",
            "bias": "BEARISH",
            "logic": f"{historical['down_probability']}% of past earnings were negative",
            "risk": "Premium paid = max loss",
            "confidence": "MODERATE",
        })

    # Case 4: IV crush play
    if iv_crush["crush_rating"] in ("SEVERE", "HIGH"):
        strategies.append({
            "strategy": "Calendar Spread (sell near, buy far)",
            "bias": "NEUTRAL",
            "logic": f"Near-month IV will crush {iv_crush['crush_pct']}% — far month holds value",
            "risk": "Defined risk (debit paid)",
            "edge": "TERM STRUCTURE COLLAPSE",
            "confidence": "HIGH" if iv_crush["crush_rating"] == "SEVERE" else "MODERATE",
        })

    return strategies


def analyze_earnings_skew(strike_data, spot):
    """Analyze put/call IV skew around earnings."""
    otm_puts = [s for s in strike_data if s["strike"] < spot * 0.97]
    otm_calls = [s for s in strike_data if s["strike"] > spot * 1.03]
    atm = [s for s in strike_data if spot * 0.97 <= s["strike"] <= spot * 1.03]

    if not atm:
        return None

    atm_iv_avg = sum(s.get("call_iv", 0) + s.get("put_iv", 0) for s in atm) / (len(atm) * 2)
    put_iv_avg = sum(s.get("put_iv", 0) for s in otm_puts) / len(otm_puts) if otm_puts else 0
    call_iv_avg = sum(s.get("call_iv", 0) for s in otm_calls) / len(otm_calls) if otm_calls else 0

    put_skew = put_iv_avg - atm_iv_avg
    call_skew = call_iv_avg - atm_iv_avg

    if put_skew > 0.05:
        bias = "MARKET HEDGING DOWNSIDE — bearish sentiment"
    elif call_skew > 0.03:
        bias = "CALL BUYING — bullish positioning"
    else:
        bias = "BALANCED — no strong directional bet"

    return {
        "atm_iv": round(atm_iv_avg * 100, 1),
        "otm_put_iv": round(put_iv_avg * 100, 1),
        "otm_call_iv": round(call_iv_avg * 100, 1),
        "put_skew": round(put_skew * 100, 2),
        "call_skew": round(call_skew * 100, 2),
        "bias": bias,
    }


def generate_verdict(implied_move, historical, iv_crush):
    """One-line trade verdict."""
    impl = implied_move["straddle_move_pct"]
    hist = historical.get("avg_absolute_move", 3)
    crush = iv_crush["crush_rating"]

    if impl > hist * 1.3 and crush in ("SEVERE", "HIGH"):
        return f"SELL PREMIUM — Options overpriced by {round((impl/hist - 1)*100)}%, expect {crush} IV crush"
    elif impl < hist * 0.8:
        return f"BUY VOLATILITY — Options underpriced, historical moves {hist}% > implied {impl}%"
    elif historical.get("up_probability", 50) > 70:
        return f"BULLISH BIAS — {historical['up_probability']}% positive earnings history"
    elif historical.get("down_probability", 50) > 70:
        return f"BEARISH BIAS — {historical['down_probability']}% negative earnings history"
    else:
        return "NEUTRAL — No clear edge, skip or use defined-risk spreads"


if __name__ == "__main__":
    print("=== PRE-EARNINGS ANALYSIS ===\n")
    print("Example: INFY before Q4 results\n")

    result = pre_earnings_analysis(
        spot=1580,
        atm_iv=0.38,
        historical_moves=[4.2, -2.8, 3.5, 1.2, -5.1, 6.3, -1.8, 2.9],
        dte=3,
    )

    print(f"Spot: ₹{result['spot']} | IV: {result['atm_iv']*100}% | DTE: {result['dte']}")
    print(f"\nImplied Move: ±₹{result['implied_move']['straddle_move_pts']} ({result['implied_move']['straddle_move_pct']}%)")
    print(f"Range: ₹{result['implied_move']['lower_range']} — ₹{result['implied_move']['upper_range']}")
    print(f"\nHistorical ({result['historical']['quarters_analyzed']}Q):")
    print(f"  Avg Move: {result['historical']['avg_absolute_move']}%")
    print(f"  Up Prob: {result['historical']['up_probability']}% | Max Up: +{result['historical']['max_up']}%")
    print(f"  Recent Bias: {result['historical']['recent_bias']}")
    print(f"\nIV Crush: {result['iv_crush']['crush_rating']} (~{result['iv_crush']['crush_pct']}% drop expected)")
    print(f"  Post-earnings IV estimate: {result['iv_crush']['estimated_post_iv']}%")
    print(f"\n{'='*50}")
    print(f"VERDICT: {result['verdict']}")
    print(f"{'='*50}")
    print(f"\nRecommended Strategies:")
    for i, s in enumerate(result['strategies'], 1):
        print(f"  {i}. {s['strategy']} ({s['bias']})")
        print(f"     Logic: {s['logic']}")
        print(f"     Confidence: {s.get('confidence', 'N/A')}")
