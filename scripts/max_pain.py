"""
Max Pain Calculator for NSE Options
Finds the strike price where option writers (sellers) have minimum loss.
Price tends to gravitate toward max pain near expiry.
"""

import json
import sys


def calculate_max_pain(oi_data):
    """
    Calculate max pain from OI data.

    oi_data: list of dicts with keys: strike, call_oi, put_oi
    Returns: max pain strike and pain at each strike
    """
    strikes = [d["strike"] for d in oi_data]
    pain_map = {}

    for expiry_price in strikes:
        total_pain = 0
        for row in oi_data:
            call_itm = max(0, expiry_price - row["strike"])
            put_itm = max(0, row["strike"] - expiry_price)
            total_pain += call_itm * row["call_oi"]
            total_pain += put_itm * row["put_oi"]
        pain_map[expiry_price] = total_pain

    max_pain_strike = min(pain_map, key=pain_map.get)
    return {
        "max_pain": max_pain_strike,
        "pain_at_max_pain": pain_map[max_pain_strike],
        "top_5_strikes": sorted(pain_map.items(), key=lambda x: x[1])[:5],
        "interpretation": f"Price likely gravitates toward {max_pain_strike} by expiry",
    }


def calculate_pcr(oi_data):
    """Put-Call Ratio from OI data."""
    total_put_oi = sum(d["put_oi"] for d in oi_data)
    total_call_oi = sum(d["call_oi"] for d in oi_data)

    pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0

    if pcr > 1.2:
        interpretation = "BULLISH — heavy put writing = support below"
    elif pcr > 0.9:
        interpretation = "NEUTRAL — balanced OI"
    elif pcr > 0.7:
        interpretation = "SLIGHTLY BEARISH — more call writing"
    else:
        interpretation = "BEARISH — heavy call writing = resistance above"

    return {
        "pcr": round(pcr, 3),
        "total_put_oi": total_put_oi,
        "total_call_oi": total_call_oi,
        "interpretation": interpretation,
    }


def find_oi_walls(oi_data, top_n=3):
    """Find strikes with highest OI (support/resistance walls)."""
    call_sorted = sorted(oi_data, key=lambda x: x["call_oi"], reverse=True)[:top_n]
    put_sorted = sorted(oi_data, key=lambda x: x["put_oi"], reverse=True)[:top_n]

    return {
        "resistance_walls": [{"strike": d["strike"], "call_oi": d["call_oi"]} for d in call_sorted],
        "support_walls": [{"strike": d["strike"], "put_oi": d["put_oi"]} for d in put_sorted],
        "interpretation": f"Resistance at {call_sorted[0]['strike']}, Support at {put_sorted[0]['strike']}",
    }


if __name__ == "__main__":
    sample_oi = [
        {"strike": 24000, "call_oi": 500000, "put_oi": 1200000},
        {"strike": 24100, "call_oi": 600000, "put_oi": 1000000},
        {"strike": 24200, "call_oi": 800000, "put_oi": 900000},
        {"strike": 24300, "call_oi": 1000000, "put_oi": 800000},
        {"strike": 24400, "call_oi": 1200000, "put_oi": 700000},
        {"strike": 24500, "call_oi": 1500000, "put_oi": 1500000},
        {"strike": 24600, "call_oi": 1300000, "put_oi": 600000},
        {"strike": 24700, "call_oi": 1100000, "put_oi": 500000},
        {"strike": 24800, "call_oi": 900000, "put_oi": 400000},
        {"strike": 24900, "call_oi": 700000, "put_oi": 300000},
        {"strike": 25000, "call_oi": 1400000, "put_oi": 200000},
    ]

    print("=== NIFTY MAX PAIN ANALYSIS ===\n")

    mp = calculate_max_pain(sample_oi)
    print(f"Max Pain: {mp['max_pain']}")
    print(f"Interpretation: {mp['interpretation']}")
    print()

    pcr = calculate_pcr(sample_oi)
    print(f"PCR: {pcr['pcr']} — {pcr['interpretation']}")
    print()

    walls = find_oi_walls(sample_oi)
    print(f"Resistance: {[w['strike'] for w in walls['resistance_walls']]}")
    print(f"Support: {[w['strike'] for w in walls['support_walls']]}")
