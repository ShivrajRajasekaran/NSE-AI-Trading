"""
Trend Following Engine for NSE/BSE
EMA stack alignment + ADX strength + pullback entry + momentum resumption.
Enters WITH the trend — never counter-trend.
"""

import math


def analyze_trend_following(candles, config=None):
    """
    Complete trend following analysis.

    candles: list of dicts with keys: open, high, low, close, volume
    config: dict with optional keys: ema_fast, ema_mid, ema_slow, adx_threshold, atr_multiplier
    """
    if config is None:
        config = {}

    ema_fast = config.get("ema_fast", 9)
    ema_mid = config.get("ema_mid", 21)
    ema_slow = config.get("ema_slow", 50)
    ema_200 = config.get("ema_200", 200)
    adx_threshold = config.get("adx_threshold", 25)
    atr_period = config.get("atr_period", 14)
    atr_multiplier = config.get("atr_multiplier", 2.0)

    if not candles or len(candles) < max(ema_200, 60):
        return {"signal": "WAIT", "reason": "Insufficient data for trend analysis"}

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    ema_fast_line = compute_ema(closes, ema_fast)
    ema_mid_line = compute_ema(closes, ema_mid)
    ema_slow_line = compute_ema(closes, ema_slow)
    ema_200_line = compute_ema(closes, ema_200)
    adx_value = compute_adx(highs, lows, closes, 14)
    atr_values = compute_atr(highs, lows, closes, atr_period)

    current_price = closes[-1]
    current_atr = atr_values[-1] if atr_values else 0

    # EMA Stack
    ema_stack = classify_ema_stack(
        ema_fast_line[-1], ema_mid_line[-1], ema_slow_line[-1], ema_200_line[-1]
    )

    # ADX Strength
    if adx_value >= 40:
        trend_strength = "STRONG"
    elif adx_value >= adx_threshold:
        trend_strength = "MODERATE"
    else:
        trend_strength = "WEAK"

    # Pullback detection
    pullback = detect_pullback(candles[-10:], ema_fast_line[-10:], ema_mid_line[-10:], ema_stack["direction"])

    # Momentum resumption
    momentum = detect_momentum_resumption(candles[-5:], ema_stack["direction"])

    # Signal
    signal = "WAIT"
    trade = None

    if ema_stack["aligned"] and trend_strength != "WEAK" and pullback["detected"] and momentum["resuming"]:
        signal = "BUY" if ema_stack["direction"] == "BULLISH" else "SELL"

        entry = current_price
        if signal == "BUY":
            stop_loss = entry - current_atr * atr_multiplier
            targets = {
                "t1": round(entry + current_atr * 1.5, 2),
                "t2": round(entry + current_atr * 3.0, 2),
                "t3": round(entry + current_atr * 5.0, 2),
            }
        else:
            stop_loss = entry + current_atr * atr_multiplier
            targets = {
                "t1": round(entry - current_atr * 1.5, 2),
                "t2": round(entry - current_atr * 3.0, 2),
                "t3": round(entry - current_atr * 5.0, 2),
            }

        trade = {
            "entry": entry,
            "stop_loss": round(stop_loss, 2),
            "targets": targets,
            "atr": round(current_atr, 2),
            "risk_reward": "1:1.5 / 1:3 / 1:5",
        }

    # Score
    score = 0
    if ema_stack["aligned"]:
        score += 30
    if trend_strength == "STRONG":
        score += 25
    elif trend_strength == "MODERATE":
        score += 15
    if pullback["detected"]:
        score += 20
    if momentum["resuming"]:
        score += 15
    if current_price > ema_200_line[-1]:
        score += 10

    return {
        "signal": signal,
        "direction": ema_stack["direction"],
        "score": min(100, score),
        "trend": {
            "ema_stack": ema_stack,
            "adx": round(adx_value, 2),
            "strength": trend_strength,
            "above_200ema": current_price > ema_200_line[-1],
        },
        "pullback": pullback,
        "momentum": momentum,
        "trade": trade,
        "management": {
            "trail_method": "ATR trailing — move stop to breakeven at +1R, trail 2×ATR after +2R",
            "partial_tp": "30% at T1, 40% at T2, 30% runner to T3",
            "exit_signal": "Close below EMA21 (bull) or above EMA21 (bear) = exit",
        },
    }


def classify_ema_stack(fast, mid, slow, ema200):
    bullish = fast > mid > slow > ema200
    bearish = fast < mid < slow < ema200

    return {
        "aligned": bullish or bearish,
        "direction": "BULLISH" if bullish else "BEARISH" if bearish else "MIXED",
        "order": "9 > 21 > 50 > 200" if bullish else "9 < 21 < 50 < 200" if bearish else "MIXED",
    }


def detect_pullback(recent_candles, ema_fast, ema_mid, direction):
    for i in range(max(0, len(recent_candles) - 3), len(recent_candles)):
        bar = recent_candles[i]
        if direction == "BULLISH":
            if bar["low"] <= ema_mid[i] * 1.002 and bar["close"] > ema_mid[i] * 0.998:
                depth = ((ema_fast[i] - bar["low"]) / ema_fast[i]) * 100
                return {"detected": True, "depth": round(abs(depth), 2), "level": "EMA21", "type": "HEALTHY_PULLBACK"}
        else:
            if bar["high"] >= ema_mid[i] * 0.998 and bar["close"] < ema_mid[i] * 1.002:
                depth = ((bar["high"] - ema_fast[i]) / ema_fast[i]) * 100
                return {"detected": True, "depth": round(abs(depth), 2), "level": "EMA21", "type": "HEALTHY_PULLBACK"}

    return {"detected": False, "reason": "No pullback to EMA detected"}


def detect_momentum_resumption(recent_candles, direction):
    if len(recent_candles) < 3:
        return {"resuming": False}

    last = recent_candles[-1]
    prev = recent_candles[-2]

    if direction == "BULLISH":
        if last["close"] > last["open"] and last["close"] > prev["high"]:
            return {"resuming": True, "type": "BULLISH_MOMENTUM_CANDLE"}
        if last["close"] > last["open"] and last["close"] > prev["close"]:
            return {"resuming": True, "type": "CONTINUATION"}
    else:
        if last["close"] < last["open"] and last["close"] < prev["low"]:
            return {"resuming": True, "type": "BEARISH_MOMENTUM_CANDLE"}
        if last["close"] < last["open"] and last["close"] < prev["close"]:
            return {"resuming": True, "type": "CONTINUATION"}

    return {"resuming": False, "reason": "No momentum candle yet"}


def compute_ema(data, period):
    ema = [data[0]]
    k = 2 / (period + 1)
    for i in range(1, len(data)):
        ema.append(data[i] * k + ema[-1] * (1 - k))
    return ema


def compute_atr(highs, lows, closes, period):
    tr = [highs[0] - lows[0]]
    for i in range(1, len(highs)):
        tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])))

    atr = [0] * len(tr)
    s = sum(tr[:period])
    atr[period - 1] = s / period
    for i in range(period, len(tr)):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    return atr


def compute_adx(highs, lows, closes, period):
    if len(highs) < period * 3:
        return 0

    plus_dm = []
    minus_dm = []
    tr = []

    for i in range(1, len(highs)):
        up = highs[i] - highs[i-1]
        down = lows[i-1] - lows[i]
        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)
        tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])))

    def smooth(arr, p):
        if len(arr) < p:
            return []
        result = [sum(arr[:p])]
        for i in range(p, len(arr)):
            result.append(result[-1] - result[-1] / p + arr[i])
        return result

    sm_tr = smooth(tr, period)
    sm_plus = smooth(plus_dm, period)
    sm_minus = smooth(minus_dm, period)

    dx = []
    for i in range(len(sm_tr)):
        if sm_tr[i] == 0:
            dx.append(0)
            continue
        plus_di = (sm_plus[i] / sm_tr[i]) * 100
        minus_di = (sm_minus[i] / sm_tr[i]) * 100
        di_sum = plus_di + minus_di
        dx.append((abs(plus_di - minus_di) / di_sum * 100) if di_sum > 0 else 0)

    adx_smoothed = smooth(dx, period)
    return adx_smoothed[-1] if adx_smoothed else 0


if __name__ == "__main__":
    import random
    random.seed(42)

    print("=== TREND FOLLOWING ENGINE ===\n")

    # Generate uptrend data
    candles = []
    price = 24000
    for i in range(250):
        move = random.uniform(-20, 35)  # Bullish bias
        o = price
        c = price + move
        h = max(o, c) + random.uniform(0, 20)
        l = min(o, c) - random.uniform(0, 15)
        candles.append({"open": o, "high": h, "low": l, "close": c, "volume": random.randint(100000, 500000)})
        price = c

    result = analyze_trend_following(candles)

    print(f"Signal: {result['signal']}")
    print(f"Direction: {result['direction']}")
    print(f"Score: {result['score']}/100")
    print(f"ADX: {result['trend']['adx']} ({result['trend']['strength']})")
    print(f"EMA Stack: {result['trend']['ema_stack']['order']}")
    print(f"Pullback: {result['pullback']}")
    print(f"Momentum: {result['momentum']}")

    if result["trade"]:
        print(f"\nTrade Plan:")
        print(f"  Entry: ₹{result['trade']['entry']:.2f}")
        print(f"  Stop: ₹{result['trade']['stop_loss']}")
        print(f"  T1: ₹{result['trade']['targets']['t1']}")
        print(f"  T2: ₹{result['trade']['targets']['t2']}")
        print(f"  T3: ₹{result['trade']['targets']['t3']}")
