"""
Options Strategy Payoff Calculator
Computes P&L at expiry for any combination of options legs.
Supports all common strategies: spreads, straddles, condors, butterflies.
"""

import json


def leg_payoff(spot, strike, premium, qty, option_type, position):
    """
    Calculate P&L for a single option leg at expiry.

    spot: Expiry price
    strike: Strike price
    premium: Premium paid/received per unit
    qty: Number of lots (positive)
    option_type: "call" or "put"
    position: "long" or "short"
    """
    if option_type == "call":
        intrinsic = max(0, spot - strike)
    else:
        intrinsic = max(0, strike - spot)

    if position == "long":
        pnl = (intrinsic - premium) * qty
    else:
        pnl = (premium - intrinsic) * qty

    return pnl


def strategy_payoff(legs, spot_range=None, lot_size=1):
    """
    Calculate payoff for a multi-leg options strategy.

    legs: list of dicts with keys:
        - strike: Strike price
        - premium: Premium per unit
        - qty: Number of lots
        - option_type: "call" or "put"
        - position: "long" or "short"
    spot_range: tuple (low, high) for payoff calculation
    lot_size: Contract multiplier
    """
    strikes = [leg["strike"] for leg in legs]
    if spot_range is None:
        min_strike = min(strikes)
        max_strike = max(strikes)
        margin = (max_strike - min_strike) * 0.5 if max_strike != min_strike else min_strike * 0.05
        spot_range = (min_strike - margin, max_strike + margin)

    step = max(1, (spot_range[1] - spot_range[0]) / 200)
    payoff_data = []

    spot = spot_range[0]
    while spot <= spot_range[1]:
        total_pnl = 0
        for leg in legs:
            pnl = leg_payoff(
                spot=spot,
                strike=leg["strike"],
                premium=leg["premium"],
                qty=leg["qty"] * lot_size,
                option_type=leg["option_type"],
                position=leg["position"],
            )
            total_pnl += pnl
        payoff_data.append({"spot": round(spot, 2), "pnl": round(total_pnl, 2)})
        spot += step

    max_profit = max(p["pnl"] for p in payoff_data)
    max_loss = min(p["pnl"] for p in payoff_data)

    breakevens = find_breakevens(payoff_data)

    net_premium = sum(
        leg["premium"] * leg["qty"] * lot_size * (1 if leg["position"] == "short" else -1)
        for leg in legs
    )

    return {
        "payoff_data": payoff_data,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "breakevens": breakevens,
        "net_premium": round(net_premium, 2),
        "risk_reward": round(abs(max_profit / max_loss), 2) if max_loss != 0 else float("inf"),
        "strategy_type": "Credit" if net_premium > 0 else "Debit",
        "premium_type": f"{'Received' if net_premium > 0 else 'Paid'} ₹{abs(net_premium):,.0f}",
    }


def find_breakevens(payoff_data):
    """Find breakeven points where P&L crosses zero."""
    breakevens = []
    for i in range(1, len(payoff_data)):
        if payoff_data[i - 1]["pnl"] * payoff_data[i]["pnl"] < 0:
            p1 = payoff_data[i - 1]
            p2 = payoff_data[i]
            be = p1["spot"] + (0 - p1["pnl"]) * (p2["spot"] - p1["spot"]) / (p2["pnl"] - p1["pnl"])
            breakevens.append(round(be, 2))
    return breakevens


def bull_call_spread(spot, lower_strike, upper_strike, lower_premium, upper_premium, lot_size=25):
    """Pre-built Bull Call Spread."""
    legs = [
        {"strike": lower_strike, "premium": lower_premium, "qty": 1, "option_type": "call", "position": "long"},
        {"strike": upper_strike, "premium": upper_premium, "qty": 1, "option_type": "call", "position": "short"},
    ]
    result = strategy_payoff(legs, lot_size=lot_size)
    result["strategy_name"] = "Bull Call Spread"
    result["legs"] = legs
    return result


def bear_put_spread(spot, upper_strike, lower_strike, upper_premium, lower_premium, lot_size=25):
    """Pre-built Bear Put Spread."""
    legs = [
        {"strike": upper_strike, "premium": upper_premium, "qty": 1, "option_type": "put", "position": "long"},
        {"strike": lower_strike, "premium": lower_premium, "qty": 1, "option_type": "put", "position": "short"},
    ]
    result = strategy_payoff(legs, lot_size=lot_size)
    result["strategy_name"] = "Bear Put Spread"
    result["legs"] = legs
    return result


def iron_condor(spot, put_buy, put_sell, call_sell, call_buy, put_buy_p, put_sell_p, call_sell_p, call_buy_p, lot_size=25):
    """Pre-built Iron Condor."""
    legs = [
        {"strike": put_buy, "premium": put_buy_p, "qty": 1, "option_type": "put", "position": "long"},
        {"strike": put_sell, "premium": put_sell_p, "qty": 1, "option_type": "put", "position": "short"},
        {"strike": call_sell, "premium": call_sell_p, "qty": 1, "option_type": "call", "position": "short"},
        {"strike": call_buy, "premium": call_buy_p, "qty": 1, "option_type": "call", "position": "long"},
    ]
    result = strategy_payoff(legs, lot_size=lot_size)
    result["strategy_name"] = "Iron Condor"
    result["legs"] = legs
    return result


def straddle(strike, call_premium, put_premium, position="long", lot_size=25):
    """Pre-built Straddle (long or short)."""
    legs = [
        {"strike": strike, "premium": call_premium, "qty": 1, "option_type": "call", "position": position},
        {"strike": strike, "premium": put_premium, "qty": 1, "option_type": "put", "position": position},
    ]
    result = strategy_payoff(legs, lot_size=lot_size)
    result["strategy_name"] = f"{'Long' if position == 'long' else 'Short'} Straddle"
    result["legs"] = legs
    return result


def strangle(call_strike, put_strike, call_premium, put_premium, position="long", lot_size=25):
    """Pre-built Strangle (long or short)."""
    legs = [
        {"strike": call_strike, "premium": call_premium, "qty": 1, "option_type": "call", "position": position},
        {"strike": put_strike, "premium": put_premium, "qty": 1, "option_type": "put", "position": position},
    ]
    result = strategy_payoff(legs, lot_size=lot_size)
    result["strategy_name"] = f"{'Long' if position == 'long' else 'Short'} Strangle"
    result["legs"] = legs
    return result


def print_payoff_ascii(result, width=60):
    """Print ASCII payoff diagram."""
    data = result["payoff_data"]
    sample_size = min(width, len(data))
    step = max(1, len(data) // sample_size)
    sampled = data[::step][:sample_size]

    max_pnl = max(p["pnl"] for p in sampled)
    min_pnl = min(p["pnl"] for p in sampled)
    pnl_range = max_pnl - min_pnl if max_pnl != min_pnl else 1

    chart_height = 20
    print(f"\n{'─' * 50}")
    print(f"  {result.get('strategy_name', 'Strategy')} Payoff")
    print(f"{'─' * 50}")

    for row in range(chart_height, -1, -1):
        threshold = min_pnl + (row / chart_height) * pnl_range
        line = ""
        for p in sampled:
            if abs(p["pnl"] - threshold) < pnl_range / chart_height:
                line += "█"
            elif row == chart_height // 2 and min_pnl <= 0 <= max_pnl:
                zero_row = int((-min_pnl / pnl_range) * chart_height)
                if row == zero_row:
                    line += "─"
                else:
                    line += " "
            else:
                line += " "

        pnl_label = f"₹{threshold:>8,.0f}" if row in (0, chart_height // 2, chart_height) else " " * 10
        print(f"{pnl_label} │{line}")

    print(f"{'─' * 50}")
    print(f"  Max Profit: ₹{result['max_profit']:,.0f}")
    print(f"  Max Loss:   ₹{result['max_loss']:,.0f}")
    print(f"  Breakevens: {result['breakevens']}")
    print(f"  R:R Ratio:  {result['risk_reward']}")
    print(f"  {result['premium_type']}")


if __name__ == "__main__":
    print("=== OPTIONS PAYOFF CALCULATOR ===\n")

    print("--- Iron Condor on NIFTY (Lot: 25) ---")
    ic = iron_condor(
        spot=24500,
        put_buy=24100, put_sell=24200, call_sell=24800, call_buy=24900,
        put_buy_p=30, put_sell_p=55, call_sell_p=50, call_buy_p=25,
        lot_size=25,
    )
    print_payoff_ascii(ic)
    print()

    print("--- Short Straddle on NIFTY 24500 ---")
    sd = straddle(strike=24500, call_premium=150, put_premium=140, position="short", lot_size=25)
    print(f"Max Profit: ₹{sd['max_profit']:,.0f}")
    print(f"Max Loss: ₹{sd['max_loss']:,.0f}")
    print(f"Breakevens: {sd['breakevens']}")
    print(f"Net Premium: {sd['premium_type']}")
