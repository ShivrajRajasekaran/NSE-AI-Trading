"""
C4 Strategy Engine — Rules-Based S/R Reversal System for NSE/BSE

C4 = 4 Confirmations before entry:
  C1: Key Support/Resistance Zone identified (HTF)
  C2: Price Action Rejection (wick, engulfing, pin bar at zone)
  C3: Momentum Shift (RSI divergence or structure break on LTF)
  C4: Entry Trigger (candle close confirmation + volume)

Works on Nifty, BankNifty, individual stocks — any liquid NSE instrument.
"""


def identify_c4_setup(candles, zones, indicators=None):
    """
    Run complete C4 analysis.

    candles: list of dicts with keys: open, high, low, close, volume
    zones: list of dicts with keys: type ("support"/"resistance"), high, low, touches
    indicators: dict with optional keys: rsi (list), macd_hist (list)
    """
    if not candles or len(candles) < 20 or not zones:
        return {"setup": False, "reason": "Insufficient data"}

    if indicators is None:
        indicators = {}

    current = candles[-1]

    c1 = check_c1_zone_proximity(current, zones)
    if not c1["confirmed"]:
        return {"setup": False, "stage": "C1", "reason": "Price not at key S/R zone"}

    c2 = check_c2_price_rejection(candles[-5:], c1["zone"])
    if not c2["confirmed"]:
        return {"setup": False, "stage": "C2", "reason": "No rejection pattern at zone"}

    c3 = check_c3_momentum_shift(candles[-14:], indicators)
    if not c3["confirmed"]:
        return {"setup": False, "stage": "C3", "reason": "No momentum divergence/shift"}

    c4 = check_c4_entry_trigger(candles[-3:], c1["zone"]["type"], indicators)
    if not c4["confirmed"]:
        return {"setup": False, "stage": "C4", "reason": "No confirmed entry trigger yet"}

    direction = "BUY" if c1["zone"]["type"] == "support" else "SELL"
    entry = current["close"]
    stop_loss = calculate_stop(current, c1["zone"], direction)
    targets = calculate_targets(entry, stop_loss, direction)

    strength = calculate_setup_strength(c1, c2, c3, c4)

    return {
        "setup": True,
        "direction": direction,
        "confirmations": {"c1": c1, "c2": c2, "c3": c3, "c4": c4},
        "trade": {
            "entry": entry,
            "stop_loss": round(stop_loss, 2),
            "target_1": round(targets["t1"], 2),
            "target_2": round(targets["t2"], 2),
            "target_3": round(targets["t3"], 2),
            "risk_reward": targets["rr"],
        },
        "zone": c1["zone"],
        "strength": strength,
    }


def check_c1_zone_proximity(candle, zones, proximity_pct=0.3):
    """C1: Is price within 0.3% of a key S/R zone?"""
    for zone in zones:
        zone_center = (zone["high"] + zone["low"]) / 2
        distance = abs(candle["close"] - zone_center) / candle["close"] * 100

        if distance <= proximity_pct:
            touches = zone.get("touches", 1)
            strength = min(100, touches * 20 + (30 if zone.get("htf") else 0))

            return {
                "confirmed": True,
                "zone": zone,
                "distance_pct": round(distance, 3),
                "strength": strength,
                "description": f"Price at {zone['type']} zone ({zone['high']}-{zone['low']}), {touches} touches",
            }

    return {"confirmed": False}


def check_c2_price_rejection(recent_candles, zone):
    """C2: Price action rejection — pin bars, engulfing, long wicks."""
    patterns = []

    for i, c in enumerate(recent_candles[-3:]):
        body = abs(c["close"] - c["open"])
        full_range = c["high"] - c["low"]
        upper_wick = c["high"] - max(c["open"], c["close"])
        lower_wick = min(c["open"], c["close"]) - c["low"]

        if full_range == 0:
            continue

        # Bullish pin bar at support
        if zone["type"] == "support" and lower_wick > body * 2 and lower_wick > full_range * 0.6:
            patterns.append({"type": "PIN_BAR_BULLISH", "strength": 80})

        # Bearish pin bar at resistance
        if zone["type"] == "resistance" and upper_wick > body * 2 and upper_wick > full_range * 0.6:
            patterns.append({"type": "PIN_BAR_BEARISH", "strength": 80})

        # Bullish engulfing at support
        if i > 0 and zone["type"] == "support":
            prev = recent_candles[-3:][i - 1]
            if (prev["close"] < prev["open"] and c["close"] > c["open"] and
                    c["close"] > prev["open"] and c["open"] < prev["close"]):
                patterns.append({"type": "BULLISH_ENGULFING", "strength": 85})

        # Bearish engulfing at resistance
        if i > 0 and zone["type"] == "resistance":
            prev = recent_candles[-3:][i - 1]
            if (prev["close"] > prev["open"] and c["close"] < c["open"] and
                    c["close"] < prev["open"] and c["open"] > prev["close"]):
                patterns.append({"type": "BEARISH_ENGULFING", "strength": 85})

        # Doji at zone
        if body < full_range * 0.1:
            patterns.append({"type": "DOJI_AT_ZONE", "strength": 60})

    if not patterns:
        return {"confirmed": False}

    best = max(patterns, key=lambda p: p["strength"])
    return {
        "confirmed": True,
        "pattern": best["type"],
        "strength": best["strength"],
        "all_patterns": patterns,
        "description": f"{best['type']} at {zone['type']} zone",
    }


def check_c3_momentum_shift(candles, indicators):
    """C3: RSI divergence, MACD flip, or structure break."""
    signals = []

    # RSI divergence
    rsi = indicators.get("rsi", [])
    if len(rsi) >= 5:
        rsi_recent = rsi[-5:]
        prices = [c["close"] for c in candles[-5:]]

        # Bullish: price lower low, RSI higher low
        if prices[-1] < min(prices[:-1]) and rsi_recent[-1] > min(rsi_recent[:-1]):
            signals.append({"type": "BULLISH_RSI_DIVERGENCE", "strength": 75})

        # Bearish: price higher high, RSI lower high
        if prices[-1] > max(prices[:-1]) and rsi_recent[-1] < max(rsi_recent[:-1]):
            signals.append({"type": "BEARISH_RSI_DIVERGENCE", "strength": 75})

        # Oversold/overbought
        if rsi_recent[-1] < 30:
            signals.append({"type": "RSI_OVERSOLD", "strength": 60})
        if rsi_recent[-1] > 70:
            signals.append({"type": "RSI_OVERBOUGHT", "strength": 60})

    # MACD histogram flip
    macd_hist = indicators.get("macd_hist", [])
    if len(macd_hist) >= 3:
        h = macd_hist[-3:]
        if h[0] < 0 and h[1] < 0 and h[2] > 0:
            signals.append({"type": "MACD_BULLISH_FLIP", "strength": 70})
        if h[0] > 0 and h[1] > 0 and h[2] < 0:
            signals.append({"type": "MACD_BEARISH_FLIP", "strength": 70})

    # Structure break
    if len(candles) >= 5:
        highs = [c["high"] for c in candles[-5:]]
        lows = [c["low"] for c in candles[-5:]]
        last_close = candles[-1]["close"]

        if last_close > max(highs[:-1]):
            signals.append({"type": "BULLISH_STRUCTURE_BREAK", "strength": 80})
        if last_close < min(lows[:-1]):
            signals.append({"type": "BEARISH_STRUCTURE_BREAK", "strength": 80})

    if not signals:
        return {"confirmed": False}

    best = max(signals, key=lambda s: s["strength"])
    return {
        "confirmed": True,
        "signal": best["type"],
        "strength": best["strength"],
        "all_signals": signals,
        "description": f"Momentum shift: {best['type']}",
    }


def check_c4_entry_trigger(recent_candles, zone_type, indicators=None):
    """C4: Final confirmation candle + optional volume."""
    if len(recent_candles) < 2:
        return {"confirmed": False}

    current = recent_candles[-1]
    prev = recent_candles[-2]

    confirmed = False
    trigger_type = ""

    if zone_type == "support":
        if current["close"] > current["open"] and current["close"] > prev["high"]:
            confirmed = True
            trigger_type = "BULLISH_CLOSE_ABOVE_PREV_HIGH"
        elif current["close"] > current["open"] and current["close"] > prev["close"]:
            confirmed = True
            trigger_type = "BULLISH_CONTINUATION_CLOSE"
    else:
        if current["close"] < current["open"] and current["close"] < prev["low"]:
            confirmed = True
            trigger_type = "BEARISH_CLOSE_BELOW_PREV_LOW"
        elif current["close"] < current["open"] and current["close"] < prev["close"]:
            confirmed = True
            trigger_type = "BEARISH_CONTINUATION_CLOSE"

    # Volume check
    volume_confirmed = False
    if indicators and "volume" in indicators and len(indicators["volume"]) >= 2:
        avg_vol = sum(indicators["volume"][:-1]) / len(indicators["volume"][:-1])
        volume_confirmed = indicators["volume"][-1] > avg_vol * 1.2

    if not confirmed:
        return {"confirmed": False}

    return {
        "confirmed": True,
        "trigger": trigger_type,
        "volume_confirmed": volume_confirmed,
        "strength": 90 if volume_confirmed else 70,
        "description": f"Entry: {trigger_type}{' + volume' if volume_confirmed else ''}",
    }


def calculate_stop(candle, zone, direction):
    """Stop loss beyond the zone with buffer."""
    buffer = (zone["high"] - zone["low"]) * 0.3
    if direction == "BUY":
        return zone["low"] - buffer
    else:
        return zone["high"] + buffer


def calculate_targets(entry, stop_loss, direction):
    """R-multiple targets: 1.5R, 2.5R, 3.5R."""
    risk = abs(entry - stop_loss)
    if direction == "BUY":
        t1 = entry + risk * 1.5
        t2 = entry + risk * 2.5
        t3 = entry + risk * 3.5
    else:
        t1 = entry - risk * 1.5
        t2 = entry - risk * 2.5
        t3 = entry - risk * 3.5

    return {"t1": t1, "t2": t2, "t3": t3, "rr": "1:1.5 / 1:2.5 / 1:3.5"}


def calculate_setup_strength(c1, c2, c3, c4):
    """Weighted strength score across all 4 confirmations."""
    weights = {"c1": 0.2, "c2": 0.3, "c3": 0.25, "c4": 0.25}
    score = (
        c1.get("strength", 50) * weights["c1"] +
        c2.get("strength", 50) * weights["c2"] +
        c3.get("strength", 50) * weights["c3"] +
        c4.get("strength", 50) * weights["c4"]
    )

    if score >= 80:
        grade = "A+ (HIGH CONVICTION)"
    elif score >= 65:
        grade = "A (GOOD SETUP)"
    elif score >= 50:
        grade = "B (ACCEPTABLE)"
    else:
        grade = "C (WEAK — SKIP)"

    return {"score": round(score, 1), "grade": grade}


def detect_sr_zones(candles, lookback=50, min_touches=2):
    """Auto-detect S/R zones from swing highs and lows."""
    if len(candles) < lookback:
        lookback = len(candles)

    relevant = candles[-lookback:]
    zones = []
    tolerance = 0.002

    for i in range(2, len(relevant) - 2):
        c = relevant[i]

        # Swing high
        if (c["high"] > relevant[i-1]["high"] and c["high"] > relevant[i-2]["high"] and
                c["high"] > relevant[i+1]["high"] and c["high"] > relevant[i+2]["high"]):
            _add_or_merge_zone(zones, c["high"], "resistance", tolerance)

        # Swing low
        if (c["low"] < relevant[i-1]["low"] and c["low"] < relevant[i-2]["low"] and
                c["low"] < relevant[i+1]["low"] and c["low"] < relevant[i+2]["low"]):
            _add_or_merge_zone(zones, c["low"], "support", tolerance)

    return sorted(
        [z for z in zones if z["touches"] >= min_touches],
        key=lambda z: z["touches"],
        reverse=True,
    )


def _add_or_merge_zone(zones, price, zone_type, tolerance):
    """Merge nearby price levels into single zone."""
    for zone in zones:
        if abs(zone["center"] - price) / price < tolerance and zone["type"] == zone_type:
            zone["touches"] += 1
            zone["high"] = max(zone["high"], price)
            zone["low"] = min(zone["low"], price)
            zone["center"] = (zone["high"] + zone["low"]) / 2
            return

    spread = price * 0.001
    zones.append({
        "type": zone_type,
        "high": price + spread,
        "low": price - spread,
        "center": price,
        "touches": 1,
    })


if __name__ == "__main__":
    print("=== C4 STRATEGY — S/R REVERSAL SYSTEM ===\n")

    # Simulate Nifty approaching a support zone
    sample_candles = [
        {"open": 24600, "high": 24650, "low": 24580, "close": 24620, "volume": 500000},
        {"open": 24620, "high": 24630, "low": 24550, "close": 24560, "volume": 600000},
        {"open": 24560, "high": 24570, "low": 24490, "close": 24510, "volume": 700000},
        {"open": 24510, "high": 24520, "low": 24480, "close": 24485, "volume": 800000},
        {"open": 24485, "high": 24490, "low": 24450, "close": 24460, "volume": 900000},
        # Pin bar at support (long lower wick)
        {"open": 24460, "high": 24470, "low": 24400, "close": 24465, "volume": 1200000},
        # Momentum shift candle
        {"open": 24465, "high": 24530, "low": 24460, "close": 24520, "volume": 1100000},
        # Entry trigger — closes above prev high
        {"open": 24520, "high": 24560, "low": 24510, "close": 24555, "volume": 1300000},
    ]

    # Pad with more candles for minimum requirement
    padding = [{"open": 24700 - i*5, "high": 24710 - i*5, "low": 24690 - i*5,
                "close": 24695 - i*5, "volume": 400000} for i in range(15)]
    all_candles = padding + sample_candles

    zones = [
        {"type": "support", "high": 24470, "low": 24440, "center": 24455, "touches": 4, "htf": True},
        {"type": "resistance", "high": 24800, "low": 24780, "center": 24790, "touches": 3, "htf": True},
    ]

    indicators = {
        "rsi": [45, 42, 38, 35, 32, 28, 33, 42, 48, 52, 55, 58, 60, 62, 55, 50, 45, 40, 35, 30, 35, 42, 50],
        "macd_hist": [-5, -4, -3, -2, -1, -0.5, 0.5, 1.5, 2.5],
        "volume": [v["volume"] for v in all_candles],
    }

    print("Testing C4 Setup Detection...")
    result = identify_c4_setup(all_candles, zones, indicators)

    if result["setup"]:
        print(f"\n✅ C4 SETUP CONFIRMED — {result['direction']}")
        print(f"   Strength: {result['strength']['score']}/100 ({result['strength']['grade']})")
        print(f"\n   Trade Plan:")
        print(f"   Entry:   ₹{result['trade']['entry']}")
        print(f"   Stop:    ₹{result['trade']['stop_loss']}")
        print(f"   T1:      ₹{result['trade']['target_1']} (1.5R)")
        print(f"   T2:      ₹{result['trade']['target_2']} (2.5R)")
        print(f"   T3:      ₹{result['trade']['target_3']} (3.5R)")
        print(f"\n   Confirmations:")
        for key in ["c1", "c2", "c3", "c4"]:
            conf = result["confirmations"][key]
            print(f"   {key.upper()}: ✅ {conf.get('description', 'Confirmed')}")
    else:
        print(f"\n❌ No C4 setup — failed at {result.get('stage', '?')}")
        print(f"   Reason: {result['reason']}")

    print("\n\n--- Auto S/R Zone Detection ---")
    import random
    random.seed(42)
    price = 24500
    synthetic_candles = []
    for i in range(60):
        move = random.uniform(-30, 30)
        o = price
        c = price + move
        h = max(o, c) + random.uniform(0, 15)
        l = min(o, c) - random.uniform(0, 15)
        synthetic_candles.append({"open": o, "high": h, "low": l, "close": c, "volume": random.randint(100000, 500000)})
        price = c

    detected = detect_sr_zones(synthetic_candles, lookback=60, min_touches=1)
    print(f"  Found {len(detected)} zones:")
    for z in detected[:5]:
        print(f"    {z['type'].upper()}: ₹{z['low']:.0f} — ₹{z['high']:.0f} ({z['touches']} touches)")
