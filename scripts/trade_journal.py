"""
Trade Journal Engine for NSE/BSE
Persistent file-based trade logging, closing, and statistics.
Tracks all trades with entry/exit, P&L, R-multiples, and edge analysis.
"""

import json
import os
from datetime import datetime

JOURNAL_DIR = os.path.expanduser("~/.nse-trading")
JOURNAL_FILE = os.path.join(JOURNAL_DIR, "journal.json")


def _ensure_dir():
    os.makedirs(JOURNAL_DIR, exist_ok=True)


def _load_journal():
    _ensure_dir()
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, "r") as f:
            return json.load(f)
    return {"trades": [], "metadata": {"created": datetime.now().isoformat()}}


def _save_journal(data):
    _ensure_dir()
    with open(JOURNAL_FILE, "w") as f:
        json.dump(data, f, indent=2)


def log_trade(ticker, direction, entry, stop_loss, target, quantity, strategy="", notes=""):
    """
    Log a new trade entry.

    Returns trade ID for future reference.
    """
    journal = _load_journal()
    trade_id = len(journal["trades"]) + 1

    risk_per_share = abs(entry - stop_loss)
    risk_amount = risk_per_share * quantity

    trade = {
        "id": trade_id,
        "ticker": ticker.upper(),
        "direction": direction.upper(),
        "entry": entry,
        "stop_loss": stop_loss,
        "target": target,
        "quantity": quantity,
        "strategy": strategy,
        "notes": notes,
        "risk_per_share": round(risk_per_share, 2),
        "risk_amount": round(risk_amount, 2),
        "status": "OPEN",
        "entry_date": datetime.now().isoformat(),
        "exit_date": None,
        "exit_price": None,
        "pnl": None,
        "r_multiple": None,
    }

    journal["trades"].append(trade)
    _save_journal(journal)

    return {
        "trade_id": trade_id,
        "message": f"Trade #{trade_id} logged: {direction} {ticker} @ ₹{entry}",
        "risk": f"₹{risk_amount:,.0f} ({risk_per_share}/share × {quantity})",
    }


def close_trade(trade_id, exit_price, notes=""):
    """Close an open trade with exit price."""
    journal = _load_journal()

    trade = None
    for t in journal["trades"]:
        if t["id"] == trade_id and t["status"] == "OPEN":
            trade = t
            break

    if not trade:
        return {"error": f"Trade #{trade_id} not found or already closed"}

    if trade["direction"] == "BUY":
        pnl = (exit_price - trade["entry"]) * trade["quantity"]
    else:
        pnl = (trade["entry"] - exit_price) * trade["quantity"]

    r_multiple = pnl / trade["risk_amount"] if trade["risk_amount"] > 0 else 0

    trade["status"] = "CLOSED"
    trade["exit_price"] = exit_price
    trade["exit_date"] = datetime.now().isoformat()
    trade["pnl"] = round(pnl, 2)
    trade["r_multiple"] = round(r_multiple, 2)
    trade["exit_notes"] = notes

    _save_journal(journal)

    return {
        "trade_id": trade_id,
        "ticker": trade["ticker"],
        "pnl": round(pnl, 2),
        "r_multiple": round(r_multiple, 2),
        "result": "WIN" if pnl > 0 else "LOSS" if pnl < 0 else "BREAKEVEN",
        "message": f"Trade #{trade_id} closed: {'WIN' if pnl > 0 else 'LOSS'} ₹{pnl:,.0f} ({r_multiple:.1f}R)",
    }


def get_open_trades():
    """Get all currently open trades."""
    journal = _load_journal()
    open_trades = [t for t in journal["trades"] if t["status"] == "OPEN"]
    return {
        "count": len(open_trades),
        "trades": open_trades,
        "total_risk": round(sum(t["risk_amount"] for t in open_trades), 2),
    }


def get_journal_stats(period="all"):
    """
    Get trading statistics.
    period: "all", "today", "week", "month"
    """
    journal = _load_journal()
    closed = [t for t in journal["trades"] if t["status"] == "CLOSED"]

    if not closed:
        return {"total_trades": 0, "message": "No closed trades yet"}

    # Filter by period
    now = datetime.now()
    if period == "today":
        closed = [t for t in closed if t.get("exit_date", "")[:10] == now.strftime("%Y-%m-%d")]
    elif period == "week":
        week_ago = (now.timestamp() - 7 * 86400)
        closed = [t for t in closed if t.get("exit_date") and datetime.fromisoformat(t["exit_date"]).timestamp() > week_ago]
    elif period == "month":
        month_ago = (now.timestamp() - 30 * 86400)
        closed = [t for t in closed if t.get("exit_date") and datetime.fromisoformat(t["exit_date"]).timestamp() > month_ago]

    if not closed:
        return {"total_trades": 0, "message": f"No closed trades in {period}"}

    winners = [t for t in closed if t["pnl"] > 0]
    losers = [t for t in closed if t["pnl"] < 0]

    total_pnl = sum(t["pnl"] for t in closed)
    gross_profit = sum(t["pnl"] for t in winners)
    gross_loss = abs(sum(t["pnl"] for t in losers))
    win_rate = (len(winners) / len(closed)) * 100
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    avg_win = gross_profit / len(winners) if winners else 0
    avg_loss = gross_loss / len(losers) if losers else 0
    expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)

    r_multiples = [t["r_multiple"] for t in closed if t["r_multiple"] is not None]
    avg_r = sum(r_multiples) / len(r_multiples) if r_multiples else 0

    # Best/worst trades
    best_trade = max(closed, key=lambda t: t["pnl"])
    worst_trade = min(closed, key=lambda t: t["pnl"])

    # By strategy
    strategy_stats = {}
    for t in closed:
        strat = t.get("strategy", "Unknown") or "Unknown"
        if strat not in strategy_stats:
            strategy_stats[strat] = {"trades": 0, "wins": 0, "pnl": 0}
        strategy_stats[strat]["trades"] += 1
        if t["pnl"] > 0:
            strategy_stats[strat]["wins"] += 1
        strategy_stats[strat]["pnl"] += t["pnl"]

    for strat in strategy_stats:
        s = strategy_stats[strat]
        s["win_rate"] = round((s["wins"] / s["trades"]) * 100, 1) if s["trades"] > 0 else 0
        s["pnl"] = round(s["pnl"], 2)

    # By ticker
    ticker_stats = {}
    for t in closed:
        ticker = t["ticker"]
        if ticker not in ticker_stats:
            ticker_stats[ticker] = {"trades": 0, "pnl": 0}
        ticker_stats[ticker]["trades"] += 1
        ticker_stats[ticker]["pnl"] += t["pnl"]

    return {
        "period": period,
        "total_trades": len(closed),
        "winners": len(winners),
        "losers": len(losers),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "net_pnl": round(total_pnl, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "avg_rr": round(avg_win / avg_loss, 2) if avg_loss > 0 else 0,
        "expectancy": round(expectancy, 2),
        "avg_r_multiple": round(avg_r, 2),
        "best_trade": {"ticker": best_trade["ticker"], "pnl": best_trade["pnl"], "r": best_trade["r_multiple"]},
        "worst_trade": {"ticker": worst_trade["ticker"], "pnl": worst_trade["pnl"], "r": worst_trade["r_multiple"]},
        "by_strategy": strategy_stats,
        "by_ticker": {k: round(v["pnl"], 2) for k, v in sorted(ticker_stats.items(), key=lambda x: x[1]["pnl"], reverse=True)[:5]},
    }


def get_edge_analysis():
    """Analyze where your edge comes from."""
    journal = _load_journal()
    closed = [t for t in journal["trades"] if t["status"] == "CLOSED"]

    if len(closed) < 10:
        return {"message": "Need at least 10 closed trades for edge analysis"}

    # Time-based edge
    by_hour = {}
    for t in closed:
        if t.get("entry_date"):
            hour = datetime.fromisoformat(t["entry_date"]).hour
            if hour not in by_hour:
                by_hour[hour] = {"trades": 0, "wins": 0}
            by_hour[hour]["trades"] += 1
            if t["pnl"] > 0:
                by_hour[hour]["wins"] += 1

    best_hour = max(by_hour.items(), key=lambda x: x[1]["wins"] / max(1, x[1]["trades"])) if by_hour else None

    # Direction edge
    buys = [t for t in closed if t["direction"] == "BUY"]
    sells = [t for t in closed if t["direction"] == "SELL"]
    buy_wr = (sum(1 for t in buys if t["pnl"] > 0) / len(buys) * 100) if buys else 0
    sell_wr = (sum(1 for t in sells if t["pnl"] > 0) / len(sells) * 100) if sells else 0

    # R-multiple distribution
    r_mults = [t["r_multiple"] for t in closed if t["r_multiple"] is not None]
    big_wins = [r for r in r_mults if r >= 2]
    small_wins = [r for r in r_mults if 0 < r < 2]
    small_losses = [r for r in r_mults if -1 <= r < 0]
    big_losses = [r for r in r_mults if r < -1]

    return {
        "direction_edge": {
            "buy_win_rate": round(buy_wr, 1),
            "sell_win_rate": round(sell_wr, 1),
            "stronger": "BUY" if buy_wr > sell_wr else "SELL",
        },
        "best_hour": {"hour": best_hour[0] if best_hour else None, "win_rate": round(best_hour[1]["wins"] / best_hour[1]["trades"] * 100, 1) if best_hour else 0} if best_hour else None,
        "r_distribution": {
            "big_wins_2R+": len(big_wins),
            "small_wins": len(small_wins),
            "small_losses": len(small_losses),
            "big_losses_1R+": len(big_losses),
        },
        "rule_compliance": f"{'GOOD' if not big_losses else 'NEEDS WORK'} — {len(big_losses)} trades exceeded 1R loss",
    }


if __name__ == "__main__":
    print("=== TRADE JOURNAL ENGINE ===\n")

    # Demo (uses temp file to not pollute real journal)
    import tempfile
    global JOURNAL_FILE
    JOURNAL_FILE = os.path.join(tempfile.gettempdir(), "demo_journal.json")

    # Log some trades
    print("--- Logging Trades ---")
    r1 = log_trade("NIFTY", "BUY", 24500, 24400, 24700, 50, strategy="Breakout", notes="ORB breakout")
    print(f"  {r1['message']}")

    r2 = log_trade("RELIANCE", "BUY", 2850, 2800, 2950, 100, strategy="Trend Following")
    print(f"  {r2['message']}")

    r3 = log_trade("BANKNIFTY", "SELL", 52000, 52300, 51500, 15, strategy="Range")
    print(f"  {r3['message']}")

    # Check open trades
    print(f"\n--- Open Trades ---")
    open_trades = get_open_trades()
    print(f"  {open_trades['count']} open | Total risk: ₹{open_trades['total_risk']:,.0f}")

    # Close trades
    print(f"\n--- Closing Trades ---")
    c1 = close_trade(1, 24680)
    print(f"  {c1['message']}")

    c2 = close_trade(2, 2920)
    print(f"  {c2['message']}")

    c3 = close_trade(3, 52250, notes="Stopped out - trend reversal")
    print(f"  {c3['message']}")

    # Stats
    print(f"\n--- Statistics ---")
    stats = get_journal_stats()
    print(f"  Trades: {stats['total_trades']} | Win Rate: {stats['win_rate']}%")
    print(f"  Net P&L: ₹{stats['net_pnl']:,.0f} | PF: {stats['profit_factor']}")
    print(f"  Avg Win: ₹{stats['avg_win']:,.0f} | Avg Loss: ₹{stats['avg_loss']:,.0f}")
    print(f"  Expectancy: ₹{stats['expectancy']:,.0f}/trade")
    print(f"  Best: {stats['best_trade']['ticker']} +₹{stats['best_trade']['pnl']:,.0f}")
    print(f"  Worst: {stats['worst_trade']['ticker']} ₹{stats['worst_trade']['pnl']:,.0f}")

    # Cleanup demo
    os.remove(JOURNAL_FILE)
