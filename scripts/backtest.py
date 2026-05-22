"""
Backtesting Engine for NSE/BSE
Tests trading strategies against historical data.
Generates performance metrics: win rate, profit factor, Sharpe, max drawdown, equity curve.
"""

import math
import json
import os


def backtest_strategy(candles, signals, config=None):
    """
    Run backtest on historical candles with given signals.

    candles: list of dicts with keys: open, high, low, close, volume, date
    signals: list of dicts with keys:
        - index: candle index for entry
        - direction: "BUY" or "SELL"
        - entry: entry price
        - stop_loss: stop loss price
        - target: target price (or list of targets for partial TP)
    config: dict with optional keys:
        - initial_capital: starting capital (default 500000)
        - risk_per_trade: risk % per trade (default 2)
        - commission_pct: commission per trade (default 0.05)
        - slippage_pct: slippage per trade (default 0.02)
    """
    if config is None:
        config = {}

    initial_capital = config.get("initial_capital", 500000)
    risk_pct = config.get("risk_per_trade", 2)
    commission_pct = config.get("commission_pct", 0.05)
    slippage_pct = config.get("slippage_pct", 0.02)

    capital = initial_capital
    trades = []
    equity_curve = [initial_capital]
    peak_equity = initial_capital
    max_drawdown = 0
    max_drawdown_pct = 0

    for signal in signals:
        idx = signal["index"]
        if idx >= len(candles):
            continue

        direction = signal["direction"]
        entry = signal["entry"]
        stop_loss = signal["stop_loss"]
        target = signal["target"]

        # Position sizing
        risk_per_share = abs(entry - stop_loss)
        if risk_per_share == 0:
            continue

        risk_amount = capital * (risk_pct / 100)
        quantity = int(risk_amount / risk_per_share)
        if quantity == 0:
            continue

        # Apply slippage to entry
        if direction == "BUY":
            actual_entry = entry * (1 + slippage_pct / 100)
        else:
            actual_entry = entry * (1 - slippage_pct / 100)

        # Simulate trade execution on subsequent candles
        exit_price = None
        exit_reason = None
        bars_held = 0

        for i in range(idx + 1, min(idx + 50, len(candles))):
            bar = candles[i]
            bars_held += 1

            if direction == "BUY":
                if bar["low"] <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = "STOP_LOSS"
                    break
                if bar["high"] >= target:
                    exit_price = target
                    exit_reason = "TARGET_HIT"
                    break
            else:
                if bar["high"] >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = "STOP_LOSS"
                    break
                if bar["low"] <= target:
                    exit_price = target
                    exit_reason = "TARGET_HIT"
                    break

        if exit_price is None:
            exit_price = candles[min(idx + 49, len(candles) - 1)]["close"]
            exit_reason = "TIME_EXIT"

        # Apply slippage to exit
        if direction == "BUY":
            actual_exit = exit_price * (1 - slippage_pct / 100)
            pnl = (actual_exit - actual_entry) * quantity
        else:
            actual_exit = exit_price * (1 + slippage_pct / 100)
            pnl = (actual_entry - actual_exit) * quantity

        # Commission
        commission = (actual_entry + actual_exit) * quantity * (commission_pct / 100)
        net_pnl = pnl - commission

        capital += net_pnl
        equity_curve.append(capital)

        # Drawdown tracking
        if capital > peak_equity:
            peak_equity = capital
        dd = peak_equity - capital
        dd_pct = (dd / peak_equity) * 100 if peak_equity > 0 else 0
        if dd_pct > max_drawdown_pct:
            max_drawdown_pct = dd_pct
            max_drawdown = dd

        trades.append({
            "direction": direction,
            "entry": round(actual_entry, 2),
            "exit": round(actual_exit, 2),
            "quantity": quantity,
            "pnl": round(net_pnl, 2),
            "pnl_pct": round((net_pnl / (actual_entry * quantity)) * 100, 2),
            "exit_reason": exit_reason,
            "bars_held": bars_held,
            "r_multiple": round(net_pnl / risk_amount, 2) if risk_amount > 0 else 0,
        })

    # Calculate statistics
    stats = calculate_statistics(trades, equity_curve, initial_capital)
    stats["max_drawdown"] = round(max_drawdown, 2)
    stats["max_drawdown_pct"] = round(max_drawdown_pct, 2)

    return {
        "config": {
            "initial_capital": initial_capital,
            "risk_per_trade": risk_pct,
            "commission_pct": commission_pct,
            "slippage_pct": slippage_pct,
        },
        "statistics": stats,
        "trades": trades,
        "equity_curve": equity_curve,
        "final_capital": round(capital, 2),
    }


def calculate_statistics(trades, equity_curve, initial_capital):
    """Calculate performance statistics."""
    if not trades:
        return {"total_trades": 0, "error": "No trades executed"}

    winners = [t for t in trades if t["pnl"] > 0]
    losers = [t for t in trades if t["pnl"] < 0]
    breakeven = [t for t in trades if t["pnl"] == 0]

    total_trades = len(trades)
    win_rate = (len(winners) / total_trades) * 100 if total_trades > 0 else 0

    gross_profit = sum(t["pnl"] for t in winners)
    gross_loss = abs(sum(t["pnl"] for t in losers))
    net_profit = gross_profit - gross_loss
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    avg_win = gross_profit / len(winners) if winners else 0
    avg_loss = gross_loss / len(losers) if losers else 0
    avg_rr = avg_win / avg_loss if avg_loss > 0 else float("inf")

    # Expectancy
    expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)

    # Sharpe Ratio (simplified)
    returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
               for i in range(1, len(equity_curve))]
    if returns:
        avg_return = sum(returns) / len(returns)
        std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 0
        sharpe = (avg_return / std_return) * math.sqrt(252) if std_return > 0 else 0
    else:
        sharpe = 0

    # Consecutive wins/losses
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_wins = 0
    current_losses = 0

    for t in trades:
        if t["pnl"] > 0:
            current_wins += 1
            current_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_losses)

    # Average bars held
    avg_bars = sum(t["bars_held"] for t in trades) / total_trades

    # R-multiple stats
    r_multiples = [t["r_multiple"] for t in trades]
    avg_r = sum(r_multiples) / len(r_multiples) if r_multiples else 0

    total_return_pct = ((equity_curve[-1] - initial_capital) / initial_capital) * 100

    return {
        "total_trades": total_trades,
        "winners": len(winners),
        "losers": len(losers),
        "breakeven": len(breakeven),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "net_profit": round(net_profit, 2),
        "total_return_pct": round(total_return_pct, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "avg_rr": round(avg_rr, 2),
        "expectancy": round(expectancy, 2),
        "sharpe_ratio": round(sharpe, 2),
        "avg_bars_held": round(avg_bars, 1),
        "avg_r_multiple": round(avg_r, 2),
        "max_consecutive_wins": max_consecutive_wins,
        "max_consecutive_losses": max_consecutive_losses,
    }


def grade_strategy(stats):
    """Grade a strategy based on key metrics."""
    score = 0

    # Win rate (max 20)
    wr = stats.get("win_rate", 0)
    if wr >= 60:
        score += 20
    elif wr >= 50:
        score += 15
    elif wr >= 40:
        score += 10

    # Profit factor (max 25)
    pf = stats.get("profit_factor", 0)
    if pf >= 2.0:
        score += 25
    elif pf >= 1.5:
        score += 20
    elif pf >= 1.2:
        score += 10

    # Sharpe (max 20)
    sharpe = stats.get("sharpe_ratio", 0)
    if sharpe >= 2.0:
        score += 20
    elif sharpe >= 1.0:
        score += 15
    elif sharpe >= 0.5:
        score += 10

    # Drawdown (max 20)
    dd = stats.get("max_drawdown_pct", 100)
    if dd < 10:
        score += 20
    elif dd < 20:
        score += 15
    elif dd < 30:
        score += 10

    # Expectancy (max 15)
    exp = stats.get("expectancy", 0)
    if exp > 500:
        score += 15
    elif exp > 200:
        score += 10
    elif exp > 0:
        score += 5

    grade = "A+" if score >= 85 else "A" if score >= 70 else "B" if score >= 55 else "C" if score >= 40 else "D"

    return {
        "score": score,
        "grade": grade,
        "tradeable": score >= 55,
        "assessment": f"{'TRADEABLE' if score >= 55 else 'NEEDS IMPROVEMENT'} — "
                      f"WR {wr}%, PF {pf}, Sharpe {sharpe}, DD {dd}%",
    }


if __name__ == "__main__":
    import random
    random.seed(42)

    print("=== BACKTESTING ENGINE ===\n")

    # Generate sample candles (250 days of Nifty-like data)
    candles = []
    price = 24000
    for i in range(250):
        move = random.uniform(-80, 85)
        o = price
        c = price + move
        h = max(o, c) + random.uniform(10, 50)
        l = min(o, c) - random.uniform(10, 50)
        candles.append({"open": o, "high": h, "low": l, "close": c, "volume": random.randint(100000, 500000), "date": f"2025-{(i//30)+1:02d}-{(i%30)+1:02d}"})
        price = c

    # Generate sample signals (simple breakout signals)
    signals = []
    for i in range(20, len(candles) - 50, 12):
        recent_high = max(c["high"] for c in candles[i-10:i])
        if candles[i]["close"] > recent_high:
            atr = sum(candles[j]["high"] - candles[j]["low"] for j in range(i-14, i)) / 14
            signals.append({
                "index": i,
                "direction": "BUY",
                "entry": candles[i]["close"],
                "stop_loss": candles[i]["close"] - atr * 2,
                "target": candles[i]["close"] + atr * 3,
            })

    result = backtest_strategy(candles, signals)
    stats = result["statistics"]

    print(f"Trades: {stats['total_trades']} | Win Rate: {stats['win_rate']}%")
    print(f"Profit Factor: {stats['profit_factor']} | Net P&L: ₹{stats['net_profit']:,.0f}")
    print(f"Avg Win: ₹{stats['avg_win']:,.0f} | Avg Loss: ₹{stats['avg_loss']:,.0f}")
    print(f"Avg R:R: {stats['avg_rr']} | Expectancy: ₹{stats['expectancy']:,.0f}/trade")
    print(f"Sharpe: {stats['sharpe_ratio']} | Max DD: {stats['max_drawdown_pct']}%")
    print(f"Return: {stats['total_return_pct']}% | Final Capital: ₹{result['final_capital']:,.0f}")
    print(f"\nConsecutive: {stats['max_consecutive_wins']} wins / {stats['max_consecutive_losses']} losses")

    grade = grade_strategy(stats)
    print(f"\nGrade: {grade['grade']} ({grade['score']}/100)")
    print(f"Assessment: {grade['assessment']}")
