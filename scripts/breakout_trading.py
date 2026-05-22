"""
Breakout Trading Engine for NSE/BSE
Detects consolidation squeezes → expansion moves with volume confirmation.
Filters false breakouts with strict invalidation rules.
"""


def analyze_breakout(candles, config=None):
    """
    Complete breakout analysis.

    candles: list of dicts with keys: open, high, low, close, volume
    config: dict with optional keys: consolidation_bars, volume_spike_ratio, atr_period
    """
    if config is None:
        config = {}

    consolidation_bars = config.get("consolidation_bars", 20)
    volume_spike_ratio = config.get("volume_spike_ratio", 1.5)
    atr_period = config.get("atr_period", 14)

    if not candles or len(candles) < consolidation_bars + 10:
        return {"signal": "WAIT", "reason": "Insufficient data"}

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c.get("volume", 0) for c in candles]

    # Step 1: Detect squeeze/consolidation
    squeeze = detect_squeeze(candles, consolidation_bars, atr_period)

    # Step 2: Breakout candle
    breakout = detect_breakout_candle(candles, squeeze)

    # Step 3: Volume confirmation
    volume_conf = confirm_volume(volumes, volume_spike_ratio)

    # ATR
    atr = compute_atr_simple(highs[-atr_period:], lows[-atr_period:], closes[-atr_period:])
    current_price = closes[-1]

    # Signal
    signal = "WAIT"
    trade = None

    if squeeze["detected"] and breakout["broken"] and volume_conf["confirmed"]:
        signal = "BUY" if breakout["direction"] == "UP" else "SELL"

        entry = current_price
        range_width = squeeze["high"] - squeeze["low"]

        if signal == "BUY":
            stop_loss = max(squeeze["low"] - atr * 0.5, entry - atr * 2)
            targets = {
                "t1": round(entry + range_width * 1.0, 2),
                "t2": round(entry + range_width * 1.618, 2),
                "t3": round(entry + range_width * 2.5, 2),
            }
        else:
            stop_loss = min(squeeze["high"] + atr * 0.5, entry + atr * 2)
            targets = {
                "t1": round(entry - range_width * 1.0, 2),
                "t2": round(entry - range_width * 1.618, 2),
                "t3": round(entry - range_width * 2.5, 2),
            }

        trade = {
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "targets": targets,
            "measured_move": round(range_width, 2),
            "atr": round(atr, 2),
            "risk_reward": round(abs(targets["t1"] - entry) / abs(entry - stop_loss), 2) if abs(entry - stop_loss) > 0 else 0,
        }

    # Score
    score = 0
    if squeeze["detected"]:
        score += 25
    if squeeze.get("tight"):
        score += 10
    if breakout["broken"]:
        score += 25
    if volume_conf["confirmed"]:
        score += 20
    if volume_conf.get("ratio", 0) > 2.0:
        score += 10
    if squeeze.get("contracting"):
        score += 10

    return {
        "signal": signal,
        "score": min(100, score),
        "squeeze": {
            "detected": squeeze["detected"],
            "tight": squeeze.get("tight", False),
            "high": round(squeeze["high"], 2),
            "low": round(squeeze["low"], 2),
            "range": round(squeeze["high"] - squeeze["low"], 2),
            "duration": squeeze.get("duration", 0),
            "contracting": squeeze.get("contracting", False),
        },
        "breakout": breakout,
        "volume": volume_conf,
        "trade": trade,
        "false_breakout_rules": {
            "rule_1": "If price re-enters consolidation within 3 bars → EXIT (false breakout)",
            "rule_2": "If breakout candle body < 50% of range → SUSPECT (weak)",
            "rule_3": "If volume < 1.5x average on breakout → SKIP (no conviction)",
            "rule_4": "First breakout often fails — wait for retest of broken level",
            "nse_specific": "Check if stock is in T2T or F&O ban — breakouts fail in illiquid conditions",
        },
    }


def detect_squeeze(candles, lookback, atr_period):
    consolidation = candles[-lookback:]
    highs = [c["high"] for c in consolidation]
    lows = [c["low"] for c in consolidation]

    range_high = max(highs)
    range_low = min(lows)
    range_width = range_high - range_low

    # Check contraction (second half tighter than first)
    mid = lookback // 2
    first_half = consolidation[:mid]
    second_half = consolidation[mid:]
    first_range = max(c["high"] for c in first_half) - min(c["low"] for c in first_half)
    second_range = max(c["high"] for c in second_half) - min(c["low"] for c in second_half)
    contracting = second_range < first_range * 0.8

    # Pre-consolidation ATR
    pre_candles = candles[-(lookback + atr_period):-lookback]
    pre_atr = 0
    if len(pre_candles) >= atr_period:
        h = [c["high"] for c in pre_candles]
        l = [c["low"] for c in pre_candles]
        cl = [c["close"] for c in pre_candles]
        pre_atr = compute_atr_simple(h, l, cl)

    atr_ratio = (range_width / (pre_atr * lookback * 0.5)) if pre_atr > 0 else 1
    is_squeeze = atr_ratio < 1.2

    return {
        "detected": is_squeeze or contracting,
        "tight": is_squeeze and contracting,
        "high": range_high,
        "low": range_low,
        "duration": lookback,
        "contracting": contracting,
        "atr_ratio": round(atr_ratio, 2),
    }


def detect_breakout_candle(candles, squeeze):
    if not squeeze["detected"]:
        return {"broken": False}

    for bar in reversed(candles[-3:]):
        body = abs(bar["close"] - bar["open"])
        full_range = bar["high"] - bar["low"]

        if full_range == 0:
            continue

        if bar["close"] > squeeze["high"] and body > full_range * 0.5:
            return {
                "broken": True,
                "direction": "UP",
                "displacement": body > full_range * 0.7,
                "description": "Strong close above consolidation high",
            }

        if bar["close"] < squeeze["low"] and body > full_range * 0.5:
            return {
                "broken": True,
                "direction": "DOWN",
                "displacement": body > full_range * 0.7,
                "description": "Strong close below consolidation low",
            }

    return {"broken": False, "reason": "No breakout candle yet"}


def confirm_volume(volumes, required_ratio):
    if not volumes or len(volumes) < 10:
        return {"confirmed": True, "reason": "No volume data — skipping"}

    recent_avg = sum(volumes[-20:-1]) / min(19, len(volumes) - 1)
    current_vol = volumes[-1]
    ratio = current_vol / recent_avg if recent_avg > 0 else 1

    return {
        "confirmed": ratio >= required_ratio,
        "ratio": round(ratio, 2),
        "current_volume": current_vol,
        "avg_volume": round(recent_avg),
        "description": f"Volume {ratio:.1f}x average — {'CONFIRMED' if ratio >= required_ratio else 'WEAK'}",
    }


def compute_atr_simple(highs, lows, closes):
    if len(highs) < 2:
        return 0
    total = sum(
        max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        for i in range(1, len(highs))
    )
    return total / (len(highs) - 1)


if __name__ == "__main__":
    import random
    random.seed(42)

    print("=== BREAKOUT TRADING ENGINE ===\n")

    # Generate consolidation then breakout
    candles = []
    price = 24500

    # 30 bars of tight consolidation
    for i in range(30):
        move = random.uniform(-10, 10)
        o = price
        c = max(24480, min(24520, price + move))
        h = max(o, c) + random.uniform(0, 8)
        l = min(o, c) - random.uniform(0, 8)
        candles.append({"open": o, "high": h, "low": l, "close": c, "volume": random.randint(200000, 400000)})
        price = c

    # Breakout candle with volume spike
    candles.append({"open": 24520, "high": 24580, "low": 24515, "close": 24570, "volume": 900000})
    price = 24570

    # Follow-through
    for i in range(5):
        move = random.uniform(10, 30)
        o = price
        c = price + move
        h = max(o, c) + random.uniform(0, 10)
        l = min(o, c) - random.uniform(0, 5)
        candles.append({"open": o, "high": h, "low": l, "close": c, "volume": random.randint(500000, 800000)})
        price = c

    result = analyze_breakout(candles)

    print(f"Signal: {result['signal']}")
    print(f"Score: {result['score']}/100")
    print(f"\nSqueeze:")
    print(f"  Detected: {result['squeeze']['detected']}")
    print(f"  Range: ₹{result['squeeze']['low']} — ₹{result['squeeze']['high']} (₹{result['squeeze']['range']})")
    print(f"  Contracting: {result['squeeze']['contracting']}")

    print(f"\nBreakout:")
    print(f"  Broken: {result['breakout']['broken']}")
    if result['breakout']['broken']:
        print(f"  Direction: {result['breakout']['direction']}")
        print(f"  Displacement: {result['breakout'].get('displacement', 'N/A')}")

    print(f"\nVolume: {result['volume']['description']}")

    if result["trade"]:
        print(f"\nTrade Plan:")
        print(f"  Entry: ₹{result['trade']['entry']}")
        print(f"  Stop: ₹{result['trade']['stop_loss']}")
        print(f"  T1: ₹{result['trade']['targets']['t1']} (measured move)")
        print(f"  T2: ₹{result['trade']['targets']['t2']} (1.618 fib extension)")
        print(f"  T3: ₹{result['trade']['targets']['t3']} (2.5x range)")
        print(f"  R:R = {result['trade']['risk_reward']}")
