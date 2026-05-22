"""
Range Trading Engine for NSE/BSE
Detects sideways consolidation and trades mean reversion at S/R boundaries.
Buy at support, sell at resistance — exit if range breaks.
"""


def analyze_range_trading(candles, config=None):
    """
    Complete range trading analysis.

    candles: list of dicts with keys: open, high, low, close, volume
    config: dict with optional keys: lookback, adx_threshold
    """
    if config is None:
        config = {}

    lookback = config.get("lookback", 50)
    adx_threshold = config.get("adx_threshold", 25)
    atr_period = config.get("atr_period", 14)

    if not candles or len(candles) < lookback:
        return {"signal": "WAIT", "reason": "Insufficient data"}

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    # Step 1: Is market ranging? (ADX < threshold)
    adx = compute_adx_simple(highs, lows, closes, 14)

    if adx >= adx_threshold:
        return {
            "signal": "WAIT",
            "reason": f"ADX = {round(adx)} — Market is trending, use Trend Following instead",
            "adx": round(adx),
            "market_state": "TRENDING",
        }

    # Step 2: Define the range
    range_data = detect_range(candles[-lookback:])

    if not range_data["valid"]:
        return {"signal": "WAIT", "reason": "No clear range detected", "adx": round(adx)}

    # Step 3: Price position within range
    current_price = closes[-1]
    position = price_position_in_range(current_price, range_data)

    # Step 4: Bounce confirmation
    bounce = detect_bounce(candles[-5:], range_data, position)

    # Step 5: ATR for stops
    atr = compute_atr_simple(highs[-atr_period:], lows[-atr_period:], closes[-atr_period:])

    # Signal
    signal = "WAIT"
    trade = None

    if position["zone"] == "SUPPORT" and bounce["bouncing"]:
        signal = "BUY"
        entry = current_price
        stop_loss = range_data["support"] - atr * 1.0
        trade = {
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "target_1": round(range_data["midpoint"], 2),
            "target_2": round(range_data["resistance"], 2),
            "risk_reward": round((range_data["midpoint"] - entry) / (entry - stop_loss), 2) if entry > stop_loss else 0,
            "invalidation": f"Close below ₹{round(range_data['support'] - atr * 0.5, 2)} = range broken, EXIT",
        }
    elif position["zone"] == "RESISTANCE" and bounce["bouncing"]:
        signal = "SELL"
        entry = current_price
        stop_loss = range_data["resistance"] + atr * 1.0
        trade = {
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "target_1": round(range_data["midpoint"], 2),
            "target_2": round(range_data["support"], 2),
            "risk_reward": round((entry - range_data["midpoint"]) / (stop_loss - entry), 2) if stop_loss > entry else 0,
            "invalidation": f"Close above ₹{round(range_data['resistance'] + atr * 0.5, 2)} = range broken, EXIT",
        }

    # Score
    score = 0
    if adx < adx_threshold:
        score += 20
    if range_data["valid"]:
        score += 20
    if range_data["touches"] >= 4:
        score += 15
    if position["zone"] in ("SUPPORT", "RESISTANCE"):
        score += 20
    if bounce["bouncing"]:
        score += 15
    if range_data["width"] / current_price * 100 > 1:
        score += 10

    return {
        "signal": signal,
        "score": min(100, score),
        "market_state": "RANGING",
        "adx": round(adx),
        "range": {
            "resistance": round(range_data["resistance"], 2),
            "support": round(range_data["support"], 2),
            "midpoint": round(range_data["midpoint"], 2),
            "width": round(range_data["width"], 2),
            "width_pct": round((range_data["width"] / current_price) * 100, 2),
            "touches": range_data["touches"],
        },
        "price_position": position,
        "bounce": bounce,
        "trade": trade,
        "rules": {
            "entry": "Only at range boundaries with rejection candle",
            "stop": "Beyond boundary + 1 ATR buffer",
            "target": "Midpoint (conservative) or opposite boundary (aggressive)",
            "breakout_exit": "If price closes beyond range + 0.5 ATR → EXIT immediately",
            "max_trades": "Max 3 round-trips per range before expecting breakout",
        },
    }


def detect_range(candles):
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    sorted_highs = sorted(highs, reverse=True)[:5]
    resistance = sum(sorted_highs) / len(sorted_highs)

    sorted_lows = sorted(lows)[:5]
    support = sum(sorted_lows) / len(sorted_lows)

    width = resistance - support
    midpoint = (resistance + support) / 2
    touch_zone = width * 0.1

    res_touches = sum(1 for c in candles if c["high"] >= resistance - touch_zone)
    sup_touches = sum(1 for c in candles if c["low"] <= support + touch_zone)

    contained = sum(1 for c in candles if support <= c["close"] <= resistance)
    containment_pct = contained / len(candles)

    valid = containment_pct > 0.7 and res_touches >= 2 and sup_touches >= 2 and width > 0

    return {
        "valid": valid,
        "resistance": resistance,
        "support": support,
        "midpoint": midpoint,
        "width": width,
        "touches": res_touches + sup_touches,
        "containment_pct": round(containment_pct * 100),
    }


def price_position_in_range(price, range_data):
    pct = ((price - range_data["support"]) / range_data["width"]) * 100 if range_data["width"] > 0 else 50

    if pct <= 20:
        zone = "SUPPORT"
        desc = "Near range bottom — look for BUY"
    elif pct >= 80:
        zone = "RESISTANCE"
        desc = "Near range top — look for SELL"
    elif 40 <= pct <= 60:
        zone = "MIDPOINT"
        desc = "At midpoint — no trade (bad R:R)"
    else:
        zone = "NO_MANS_LAND"
        desc = "Between levels — wait for boundary"

    return {"pct_from_support": round(pct), "zone": zone, "description": desc}


def detect_bounce(recent_candles, range_data, position):
    if len(recent_candles) < 2:
        return {"bouncing": False}

    last = recent_candles[-1]
    prev = recent_candles[-2]

    if position["zone"] == "SUPPORT":
        lower_wick = min(last["open"], last["close"]) - last["low"]
        body = abs(last["close"] - last["open"])
        bullish = last["close"] > last["open"]

        if bullish and lower_wick > body * 1.5:
            return {"bouncing": True, "type": "PIN_BAR_BOUNCE", "strength": 80}
        if bullish and last["close"] > prev["high"]:
            return {"bouncing": True, "type": "ENGULFING_BOUNCE", "strength": 85}
        if bullish:
            return {"bouncing": True, "type": "GREEN_CLOSE_AT_SUPPORT", "strength": 60}

    if position["zone"] == "RESISTANCE":
        upper_wick = last["high"] - max(last["open"], last["close"])
        body = abs(last["close"] - last["open"])
        bearish = last["close"] < last["open"]

        if bearish and upper_wick > body * 1.5:
            return {"bouncing": True, "type": "PIN_BAR_REJECTION", "strength": 80}
        if bearish and last["close"] < prev["low"]:
            return {"bouncing": True, "type": "ENGULFING_REJECTION", "strength": 85}
        if bearish:
            return {"bouncing": True, "type": "RED_CLOSE_AT_RESISTANCE", "strength": 60}

    return {"bouncing": False, "reason": "No confirmation candle"}


def compute_adx_simple(highs, lows, closes, period):
    if len(highs) < period * 3:
        return 0

    sum_tr = 0
    sum_plus = 0
    sum_minus = 0
    dx_values = []

    for i in range(1, len(highs)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        up = highs[i] - highs[i-1]
        down = lows[i-1] - lows[i]
        plus_dm = up if up > down and up > 0 else 0
        minus_dm = down if down > up and down > 0 else 0

        if i <= period:
            sum_tr += tr
            sum_plus += plus_dm
            sum_minus += minus_dm
        else:
            sum_tr = sum_tr - sum_tr / period + tr
            sum_plus = sum_plus - sum_plus / period + plus_dm
            sum_minus = sum_minus - sum_minus / period + minus_dm

        if i >= period:
            plus_di = (sum_plus / sum_tr * 100) if sum_tr > 0 else 0
            minus_di = (sum_minus / sum_tr * 100) if sum_tr > 0 else 0
            di_sum = plus_di + minus_di
            dx = (abs(plus_di - minus_di) / di_sum * 100) if di_sum > 0 else 0
            dx_values.append(dx)

    if len(dx_values) < period:
        return 0
    return sum(dx_values[-period:]) / period


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

    print("=== RANGE TRADING ENGINE ===\n")

    # Generate ranging data (oscillate between 24400-24600)
    candles = []
    price = 24500
    for i in range(60):
        direction = -1 if price > 24580 else 1 if price < 24420 else (1 if random.random() > 0.5 else -1)
        move = random.uniform(5, 25) * direction
        o = price
        c = max(24400, min(24600, price + move))
        h = max(o, c) + random.uniform(0, 10)
        l = min(o, c) - random.uniform(0, 10)
        candles.append({"open": o, "high": h, "low": l, "close": c, "volume": random.randint(200000, 500000)})
        price = c

    result = analyze_range_trading(candles)

    print(f"Signal: {result['signal']}")
    print(f"Market State: {result.get('market_state', 'N/A')}")
    print(f"ADX: {result['adx']}")

    if "range" in result:
        print(f"\nRange Detected:")
        print(f"  Resistance: ₹{result['range']['resistance']}")
        print(f"  Support: ₹{result['range']['support']}")
        print(f"  Width: ₹{result['range']['width']} ({result['range']['width_pct']}%)")
        print(f"  Touches: {result['range']['touches']}")

    if "price_position" in result:
        print(f"\nPrice Position: {result['price_position']['description']}")

    if result.get("trade"):
        print(f"\nTrade Plan:")
        print(f"  Entry: ₹{result['trade']['entry']}")
        print(f"  Stop: ₹{result['trade']['stop_loss']}")
        print(f"  T1: ₹{result['trade']['target_1']}")
        print(f"  T2: ₹{result['trade']['target_2']}")
        print(f"  R:R = {result['trade']['risk_reward']}")
        print(f"  ⚠️  {result['trade']['invalidation']}")
