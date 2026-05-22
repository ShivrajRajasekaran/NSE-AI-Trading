"""
Position Sizing Calculator for Indian Markets
Fixed %, Kelly Criterion, ATR-based, and F&O lot-adjusted sizing.
"""

import math


def fixed_percent_size(capital, risk_percent, entry, stop_loss, lot_size=1):
    """
    Fixed percentage risk position sizing.

    capital: Total trading capital in ₹
    risk_percent: Max risk per trade (e.g., 2 for 2%)
    entry: Entry price
    stop_loss: Stop loss price
    lot_size: F&O lot size (1 for cash)
    """
    risk_amount = capital * (risk_percent / 100)
    risk_per_share = abs(entry - stop_loss)

    if risk_per_share == 0:
        return {"error": "Entry and stop loss cannot be same"}

    raw_qty = risk_amount / risk_per_share
    lots = math.floor(raw_qty / lot_size)
    qty = lots * lot_size

    actual_risk = qty * risk_per_share
    actual_risk_pct = (actual_risk / capital) * 100

    return {
        "method": "Fixed Percentage",
        "capital": capital,
        "risk_percent": risk_percent,
        "risk_amount": round(risk_amount, 2),
        "risk_per_share": round(risk_per_share, 2),
        "raw_quantity": int(raw_qty),
        "lots": lots,
        "lot_size": lot_size,
        "quantity": qty,
        "position_value": round(qty * entry, 2),
        "actual_risk": round(actual_risk, 2),
        "actual_risk_pct": round(actual_risk_pct, 2),
        "reward_1R": round(entry + risk_per_share if entry > stop_loss else entry - risk_per_share, 2),
        "reward_2R": round(entry + 2 * risk_per_share if entry > stop_loss else entry - 2 * risk_per_share, 2),
        "reward_3R": round(entry + 3 * risk_per_share if entry > stop_loss else entry - 3 * risk_per_share, 2),
    }


def kelly_criterion(win_rate, avg_win, avg_loss):
    """
    Kelly Criterion for optimal position sizing.

    win_rate: Historical win rate (0.0 to 1.0)
    avg_win: Average winning trade amount
    avg_loss: Average losing trade amount (positive number)
    """
    if avg_loss == 0:
        return {"error": "Average loss cannot be zero"}

    win_loss_ratio = avg_win / avg_loss
    kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

    half_kelly = kelly_pct / 2
    quarter_kelly = kelly_pct / 4

    return {
        "method": "Kelly Criterion",
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "win_loss_ratio": round(win_loss_ratio, 2),
        "full_kelly_pct": round(kelly_pct * 100, 2),
        "half_kelly_pct": round(half_kelly * 100, 2),
        "quarter_kelly_pct": round(quarter_kelly * 100, 2),
        "recommendation": f"Use Half Kelly ({round(half_kelly * 100, 1)}%) for safety",
        "interpretation": "Positive = edge exists" if kelly_pct > 0 else "Negative = no edge, don't trade",
    }


def atr_based_size(capital, risk_percent, entry, atr, atr_multiplier=1.5, lot_size=1):
    """
    ATR-based position sizing (volatility-adjusted).

    capital: Total capital
    risk_percent: Risk per trade
    entry: Entry price
    atr: Average True Range value
    atr_multiplier: Stop = entry ± (ATR × multiplier)
    lot_size: F&O lot size
    """
    stop_distance = atr * atr_multiplier
    risk_amount = capital * (risk_percent / 100)

    raw_qty = risk_amount / stop_distance
    lots = math.floor(raw_qty / lot_size)
    qty = lots * lot_size

    stop_loss = entry - stop_distance
    target_1 = entry + stop_distance
    target_2 = entry + 2 * stop_distance
    target_3 = entry + 3 * stop_distance

    return {
        "method": "ATR-Based",
        "capital": capital,
        "atr": atr,
        "atr_multiplier": atr_multiplier,
        "stop_distance": round(stop_distance, 2),
        "stop_loss": round(stop_loss, 2),
        "quantity": qty,
        "lots": lots,
        "position_value": round(qty * entry, 2),
        "actual_risk": round(qty * stop_distance, 2),
        "target_1R": round(target_1, 2),
        "target_2R": round(target_2, 2),
        "target_3R": round(target_3, 2),
    }


def portfolio_heat(positions, capital):
    """
    Calculate total portfolio heat (total risk exposure).

    positions: list of dicts with keys: ticker, qty, entry, stop_loss
    capital: Total capital
    """
    total_risk = 0
    details = []

    for pos in positions:
        risk = abs(pos["entry"] - pos["stop_loss"]) * pos["qty"]
        risk_pct = (risk / capital) * 100
        total_risk += risk
        details.append({
            "ticker": pos["ticker"],
            "risk_amount": round(risk, 2),
            "risk_pct": round(risk_pct, 2),
        })

    heat_pct = (total_risk / capital) * 100

    if heat_pct > 10:
        status = "DANGER — reduce positions immediately"
    elif heat_pct > 6:
        status = "HIGH — no new trades until heat drops"
    elif heat_pct > 4:
        status = "MODERATE — one more trade max"
    else:
        status = "SAFE — can add positions"

    return {
        "total_risk": round(total_risk, 2),
        "heat_pct": round(heat_pct, 2),
        "status": status,
        "positions": details,
        "max_heat_rule": "6% portfolio heat maximum (KARTHIK rule)",
    }


NSE_LOT_SIZES = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 25,
    "SENSEX": 10,
    "MIDCPNIFTY": 50,
    "RELIANCE": 250,
    "TCS": 150,
    "INFY": 300,
    "HDFCBANK": 550,
    "ICICIBANK": 700,
    "SBIN": 750,
    "TATAMOTORS": 575,
    "ITC": 1600,
    "WIPRO": 1500,
    "BAJFINANCE": 125,
}


if __name__ == "__main__":
    print("=== POSITION SIZING CALCULATOR ===\n")

    print("--- Fixed 2% Risk ---")
    result = fixed_percent_size(
        capital=500000, risk_percent=2, entry=24500, stop_loss=24400, lot_size=25
    )
    print(f"Capital: ₹{result['capital']:,}")
    print(f"Risk: {result['risk_percent']}% = ₹{result['risk_amount']:,}")
    print(f"Quantity: {result['quantity']} ({result['lots']} lots × {result['lot_size']})")
    print(f"Position Value: ₹{result['position_value']:,}")
    print(f"Targets: 1R={result['reward_1R']} | 2R={result['reward_2R']} | 3R={result['reward_3R']}")
    print()

    print("--- Kelly Criterion ---")
    kelly = kelly_criterion(win_rate=0.55, avg_win=5000, avg_loss=3000)
    print(f"Win Rate: {kelly['win_rate']*100}% | W:L Ratio: {kelly['win_loss_ratio']}")
    print(f"Full Kelly: {kelly['full_kelly_pct']}% | Half Kelly: {kelly['half_kelly_pct']}%")
    print(f"Recommendation: {kelly['recommendation']}")
    print()

    print("--- ATR-Based ---")
    atr_result = atr_based_size(
        capital=500000, risk_percent=2, entry=24500, atr=150, atr_multiplier=1.5, lot_size=25
    )
    print(f"ATR: {atr_result['atr']} × {atr_result['atr_multiplier']} = Stop at {atr_result['stop_loss']}")
    print(f"Quantity: {atr_result['quantity']} lots")
    print(f"Targets: 1R={atr_result['target_1R']} | 2R={atr_result['target_2R']} | 3R={atr_result['target_3R']}")
    print()

    print("--- Portfolio Heat ---")
    positions = [
        {"ticker": "NIFTY CE", "qty": 50, "entry": 200, "stop_loss": 150},
        {"ticker": "RELIANCE", "qty": 250, "entry": 2800, "stop_loss": 2750},
        {"ticker": "BANKNIFTY PE", "qty": 15, "entry": 400, "stop_loss": 300},
    ]
    heat = portfolio_heat(positions, 500000)
    print(f"Portfolio Heat: {heat['heat_pct']}% — {heat['status']}")
    for p in heat["positions"]:
        print(f"  {p['ticker']}: ₹{p['risk_amount']:,} ({p['risk_pct']}%)")
