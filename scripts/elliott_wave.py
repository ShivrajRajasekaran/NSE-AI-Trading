"""
Elliott Wave Engine for NSE/BSE
Counts 5-wave impulse structures and ABC corrections.
Identifies current wave position for entry/exit timing.

Rules:
- Wave 2 never retraces more than 100% of Wave 1
- Wave 3 is never the shortest impulse wave
- Wave 4 never overlaps Wave 1 price territory
"""


def analyze_elliott_wave(candles, config=None):
    """
    Complete Elliott Wave analysis.

    candles: list of dicts with keys: open, high, low, close
    config: dict with optional keys: min_swing_size, lookback
    """
    if config is None:
        config = {}

    min_swing_size = config.get("min_swing_size", 0.005)
    lookback = config.get("lookback", 100)

    if not candles or len(candles) < 30:
        return {"wave": None, "reason": "Insufficient data"}

    relevant = candles[-lookback:]
    swings = detect_swing_points(relevant, min_swing_size)

    if len(swings) < 5:
        return {"wave": None, "reason": "Not enough swing points", "swings_found": len(swings)}

    impulse = fit_impulse_wave(swings)
    correction = fit_correction_wave(swings)

    if impulse["valid"] and (not correction["valid"] or impulse["confidence"] > correction["confidence"]):
        result = impulse
    elif correction["valid"]:
        result = correction
    else:
        return {
            "wave": None,
            "reason": "No clear Elliott Wave pattern",
            "swings_found": len(swings),
            "hint": "Market may be in complex correction or early stage",
        }

    trade = get_wave_trade_plan(result, relevant)
    result["trade"] = trade
    result["swing_count"] = len(swings)
    return result


def detect_swing_points(bars, min_swing_pct):
    """Detect swing highs and lows with minimum size filter."""
    swings = []
    look = 3

    for i in range(look, len(bars) - look):
        is_high = all(bars[i]["high"] > bars[i-j]["high"] for j in range(1, look+1)) and \
                  all(bars[i]["high"] > bars[i+j]["high"] for j in range(1, look+1))
        is_low = all(bars[i]["low"] < bars[i-j]["low"] for j in range(1, look+1)) and \
                 all(bars[i]["low"] < bars[i+j]["low"] for j in range(1, look+1))

        if is_high:
            if swings and abs(bars[i]["high"] - swings[-1]["price"]) / swings[-1]["price"] < min_swing_pct:
                continue
            swings.append({"type": "HIGH", "price": bars[i]["high"], "index": i})

        if is_low:
            if swings and abs(bars[i]["low"] - swings[-1]["price"]) / swings[-1]["price"] < min_swing_pct:
                continue
            swings.append({"type": "LOW", "price": bars[i]["low"], "index": i})

    # Remove consecutive same-type (keep extremes)
    filtered = []
    for s in swings:
        if not filtered:
            filtered.append(s)
            continue
        if filtered[-1]["type"] == s["type"]:
            if s["type"] == "HIGH" and s["price"] > filtered[-1]["price"]:
                filtered[-1] = s
            elif s["type"] == "LOW" and s["price"] < filtered[-1]["price"]:
                filtered[-1] = s
        else:
            filtered.append(s)

    return filtered


def fit_impulse_wave(swings):
    """Try to fit a 5-wave impulse pattern (bullish and bearish)."""
    bullish = _try_bullish_impulse(swings)
    bearish = _try_bearish_impulse(swings)

    if bullish["valid"] and bearish["valid"]:
        return bullish if bullish["confidence"] > bearish["confidence"] else bearish
    return bullish if bullish["valid"] else bearish


def _try_bullish_impulse(swings):
    """Fit bullish impulse: LOW-HIGH-LOW-HIGH-LOW-HIGH pattern."""
    for start in range(max(0, len(swings) - 10), len(swings) - 5):
        if swings[start]["type"] != "LOW":
            continue

        candidates = [swings[start]]
        expected = "HIGH"

        for i in range(start + 1, len(swings)):
            if len(candidates) >= 6:
                break
            if swings[i]["type"] == expected:
                candidates.append(swings[i])
                expected = "LOW" if expected == "HIGH" else "HIGH"

        if len(candidates) < 6:
            continue

        w0, w1, w2, w3, w4, w5 = candidates

        wave1 = w1["price"] - w0["price"]
        wave2ret = w1["price"] - w2["price"]
        wave3 = w3["price"] - w2["price"]
        wave4ret = w3["price"] - w4["price"]
        wave5 = w5["price"] - w4["price"]

        if wave1 <= 0 or wave3 <= 0 or wave5 <= 0:
            continue
        if wave2ret >= wave1:
            continue
        if wave3 < wave1 and wave3 < wave5:
            continue
        if w4["price"] < w1["price"]:
            continue

        w2fib = wave2ret / wave1
        w3fib = wave3 / wave1
        w4fib = wave4ret / wave3 if wave3 > 0 else 0

        confidence = 50
        if 0.5 < w2fib < 0.786:
            confidence += 15
        if 1.5 < w3fib < 2.618:
            confidence += 15
        if 0.236 < w4fib < 0.5:
            confidence += 10
        if wave3 > wave1 and wave3 > wave5:
            confidence += 10

        current_wave = _determine_current_wave(candidates, swings)

        return {
            "valid": True,
            "pattern": "IMPULSE",
            "direction": "BULLISH",
            "confidence": min(100, confidence),
            "waves": {
                "wave1": {"start": w0["price"], "end": w1["price"], "size": round(wave1, 2)},
                "wave2": {"start": w1["price"], "end": w2["price"], "retracement": f"{round(w2fib*100, 1)}%"},
                "wave3": {"start": w2["price"], "end": w3["price"], "extension": f"{round(w3fib*100, 1)}%"},
                "wave4": {"start": w3["price"], "end": w4["price"], "retracement": f"{round(w4fib*100, 1)}%"},
                "wave5": {"start": w4["price"], "end": w5["price"], "size": round(wave5, 2)},
            },
            "current_wave": current_wave,
            "fib_levels": {
                "wave2_retrace": f"{round(w2fib*100, 1)}%",
                "wave3_extension": f"{round(w3fib*100, 1)}%",
                "wave4_retrace": f"{round(w4fib*100, 1)}%",
            },
        }

    return {"valid": False}


def _try_bearish_impulse(swings):
    """Fit bearish impulse: HIGH-LOW-HIGH-LOW-HIGH-LOW pattern."""
    for start in range(max(0, len(swings) - 10), len(swings) - 5):
        if swings[start]["type"] != "HIGH":
            continue

        candidates = [swings[start]]
        expected = "LOW"

        for i in range(start + 1, len(swings)):
            if len(candidates) >= 6:
                break
            if swings[i]["type"] == expected:
                candidates.append(swings[i])
                expected = "HIGH" if expected == "LOW" else "LOW"

        if len(candidates) < 6:
            continue

        w0, w1, w2, w3, w4, w5 = candidates

        wave1 = w0["price"] - w1["price"]
        wave2ret = w2["price"] - w1["price"]
        wave3 = w2["price"] - w3["price"]
        wave4ret = w4["price"] - w3["price"]
        wave5 = w4["price"] - w5["price"]

        if wave1 <= 0 or wave3 <= 0 or wave5 <= 0:
            continue
        if wave2ret >= wave1:
            continue
        if wave3 < wave1 and wave3 < wave5:
            continue
        if w4["price"] > w1["price"]:
            continue

        w2fib = wave2ret / wave1
        w3fib = wave3 / wave1
        w4fib = wave4ret / wave3 if wave3 > 0 else 0

        confidence = 50
        if 0.5 < w2fib < 0.786:
            confidence += 15
        if 1.5 < w3fib < 2.618:
            confidence += 15
        if 0.236 < w4fib < 0.5:
            confidence += 10
        if wave3 > wave1 and wave3 > wave5:
            confidence += 10

        current_wave = _determine_current_wave(candidates, swings)

        return {
            "valid": True,
            "pattern": "IMPULSE",
            "direction": "BEARISH",
            "confidence": min(100, confidence),
            "waves": {
                "wave1": {"start": w0["price"], "end": w1["price"], "size": round(wave1, 2)},
                "wave2": {"start": w1["price"], "end": w2["price"], "retracement": f"{round(w2fib*100, 1)}%"},
                "wave3": {"start": w2["price"], "end": w3["price"], "extension": f"{round(w3fib*100, 1)}%"},
                "wave4": {"start": w3["price"], "end": w4["price"], "retracement": f"{round(w4fib*100, 1)}%"},
                "wave5": {"start": w4["price"], "end": w5["price"], "size": round(wave5, 2)},
            },
            "current_wave": current_wave,
            "fib_levels": {
                "wave2_retrace": f"{round(w2fib*100, 1)}%",
                "wave3_extension": f"{round(w3fib*100, 1)}%",
                "wave4_retrace": f"{round(w4fib*100, 1)}%",
            },
        }

    return {"valid": False}


def fit_correction_wave(swings):
    """Try to fit ABC correction pattern."""
    if len(swings) < 3:
        return {"valid": False}

    last3 = swings[-3:]

    # Bearish correction: HIGH-LOW-HIGH (after bullish impulse)
    if last3[0]["type"] == "HIGH" and last3[1]["type"] == "LOW" and last3[2]["type"] == "HIGH":
        leg_a = last3[0]["price"] - last3[1]["price"]
        leg_b = last3[2]["price"] - last3[1]["price"]
        if leg_a <= 0:
            return {"valid": False}
        b_retrace = leg_b / leg_a

        if 0.382 < b_retrace < 0.786:
            return {
                "valid": True,
                "pattern": "CORRECTION_ABC",
                "direction": "BEARISH_CORRECTION",
                "confidence": 60 + (15 if b_retrace > 0.5 else 0),
                "waves": {
                    "wave_a": {"start": last3[0]["price"], "end": last3[1]["price"]},
                    "wave_b": {"start": last3[1]["price"], "end": last3[2]["price"], "retracement": f"{round(b_retrace*100, 1)}%"},
                    "wave_c_projected": round(last3[2]["price"] - leg_a, 2),
                },
                "current_wave": "In Wave C or complete",
                "interpretation": "Correction ending — look for reversal to resume bull trend",
            }

    # Bullish correction: LOW-HIGH-LOW (after bearish impulse)
    if last3[0]["type"] == "LOW" and last3[1]["type"] == "HIGH" and last3[2]["type"] == "LOW":
        leg_a = last3[1]["price"] - last3[0]["price"]
        leg_b = last3[1]["price"] - last3[2]["price"]
        if leg_a <= 0:
            return {"valid": False}
        b_retrace = leg_b / leg_a

        if 0.382 < b_retrace < 0.786:
            return {
                "valid": True,
                "pattern": "CORRECTION_ABC",
                "direction": "BULLISH_CORRECTION",
                "confidence": 60 + (15 if b_retrace > 0.5 else 0),
                "waves": {
                    "wave_a": {"start": last3[0]["price"], "end": last3[1]["price"]},
                    "wave_b": {"start": last3[1]["price"], "end": last3[2]["price"], "retracement": f"{round(b_retrace*100, 1)}%"},
                    "wave_c_projected": round(last3[2]["price"] + leg_a, 2),
                },
                "current_wave": "In Wave C or complete",
                "interpretation": "Correction ending — look for reversal to resume bear trend",
            }

    return {"valid": False}


def _determine_current_wave(wave_points, all_swings):
    last_wave = wave_points[-1]
    last_swing = all_swings[-1]

    if last_swing["index"] > last_wave["index"]:
        return "Post Wave 5 — expect ABC correction"

    return "Wave 5 area — trail stops tight"


def get_wave_trade_plan(wave_result, bars):
    """Generate trade plan based on wave position."""
    current_wave = wave_result.get("current_wave", "")
    direction = wave_result.get("direction", "")
    pattern = wave_result.get("pattern", "")

    if pattern == "IMPULSE":
        if "Wave 3" in current_wave:
            return {
                "action": "BUY" if direction == "BULLISH" else "SELL",
                "reason": "Wave 3 is strongest — ride the momentum",
                "risk": "Trail stop below Wave 2 low",
                "target": "Wave 3 extends 1.618× Wave 1",
            }
        if "Wave 4" in current_wave:
            return {
                "action": "PREPARE",
                "reason": "Wave 4 correction — wait for completion, enter Wave 5",
                "entry": "Buy at 38.2%-50% retracement of Wave 3",
                "risk": "Stop beyond Wave 1 territory (invalidation)",
            }
        if "Wave 5" in current_wave or "reversal" in current_wave:
            return {
                "action": "EXIT / REVERSE",
                "reason": "Wave 5 complete — ABC correction starting",
                "risk": "Don't hold — trend exhaustion",
                "target": "Wait for Wave C completion for new entry",
            }

    if pattern == "CORRECTION_ABC":
        return {
            "action": "BUY" if "BEARISH" in direction else "SELL",
            "reason": "ABC correction ending — trend resumption expected",
            "entry": "Enter at Wave C completion with reversal candle",
            "target": "New impulse Wave 1-2-3",
            "risk": "Stop beyond Wave C extension (1.618× Wave A)",
        }

    return {"action": "WAIT", "reason": "No clear wave-based setup"}


if __name__ == "__main__":
    import random
    random.seed(42)

    print("=== ELLIOTT WAVE ANALYSIS ===\n")

    # Generate impulse-like data (trending with pullbacks)
    candles = []
    price = 24000
    wave_moves = [500, -250, 900, -300, 400]  # Simulated 5-wave bullish

    for wave_size in wave_moves:
        steps = 15
        step_size = wave_size / steps
        for i in range(steps):
            noise = random.uniform(-20, 20)
            o = price
            c = price + step_size + noise
            h = max(o, c) + random.uniform(5, 25)
            l = min(o, c) - random.uniform(5, 25)
            candles.append({"open": o, "high": h, "low": l, "close": c})
            price = c

    result = analyze_elliott_wave(candles)

    if result.get("valid"):
        print(f"Pattern: {result['pattern']} ({result['direction']})")
        print(f"Confidence: {result['confidence']}%")
        print(f"Current Position: {result['current_wave']}")
        print(f"\nWave Structure:")
        for name, wave in result["waves"].items():
            if "size" in wave:
                print(f"  {name}: ₹{wave['start']:.0f} → ₹{wave['end']:.0f} (size: ₹{wave['size']})")
            elif "retracement" in wave:
                print(f"  {name}: ₹{wave['start']:.0f} → ₹{wave['end']:.0f} (retrace: {wave['retracement']})")
            elif "extension" in wave:
                print(f"  {name}: ₹{wave['start']:.0f} → ₹{wave['end']:.0f} (ext: {wave['extension']})")
        print(f"\nTrade Plan:")
        for k, v in result["trade"].items():
            print(f"  {k}: {v}")
    else:
        print(f"No pattern: {result.get('reason', 'Unknown')}")
        print(f"Swings found: {result.get('swings_found', result.get('swing_count', 0))}")
