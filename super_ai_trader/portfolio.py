"""Portfolio aggregation (like the 'Hi Monday' dashboard).

Aggregates every running paper grid into: total portfolio value, cash,
allocated holdings (coin value), per-asset allocation %, and top
winners/losers. Built purely from the live session state — no extra keys.
"""
from __future__ import annotations

DONUT_COLORS = ["#f7931a", "#627eea", "#f0b90b", "#26a7df", "#e84393",
                "#8e44ad", "#16c784", "#ea3943", "#f6c945", "#4aa3ff"]


def build_portfolio(multigrid: dict | None = None) -> dict:
    """multigrid = MultiGrid.summary() / overview-like dict. Accepts the
    overview (has per-coin rows with cash/base_held/price) — we use that."""
    coins = (multigrid or {}).get("coins") or []

    holdings = []
    total_coin_value = 0.0
    total_cash = 0.0
    total_invested = 0.0

    for c in coins:
        price = float(c.get("price") or 0)
        base = float(c.get("base_held") or 0)
        cash = float(c.get("cash") if c.get("cash") is not None else 0)
        invested = float(c.get("invested") or c.get("investment") or 0)
        coin_value = base * price
        total_coin_value += coin_value
        total_cash += cash
        total_invested += invested or 0
        pnl = float(c.get("pnl") or 0)
        roi = float(c.get("roi_pct") or 0)
        holdings.append({
            "coin": c.get("coin"),
            "price": price,
            "amount": round(base, 8),
            "value": round(coin_value, 2),
            "cash": round(cash, 2),
            "pnl": round(pnl, 2),
            "roi_pct": roi,
            "paused": c.get("paused"),
        })

    total_value = total_coin_value + total_cash
    total_pnl = sum(h["pnl"] for h in holdings)

    # allocation % of total value (cash + each coin)
    alloc = []
    if total_value > 0:
        for i, h in enumerate(holdings):
            if h["value"] > 0:
                alloc.append({
                    "label": h["coin"],
                    "value": round(h["value"], 2),
                    "pct": round(h["value"] / total_value * 100, 1),
                    "color": DONUT_COLORS[i % len(DONUT_COLORS)],
                })
        if total_cash > 0:
            alloc.append({
                "label": "USD (cash)",
                "value": round(total_cash, 2),
                "pct": round(total_cash / total_value * 100, 1),
                "color": "#5b6a86",
            })

    by_roi = sorted(holdings, key=lambda h: h["roi_pct"], reverse=True)
    winners = [{"coin": h["coin"], "roi_pct": h["roi_pct"], "pnl": h["pnl"]}
               for h in by_roi if h["roi_pct"] > 0][:5]
    losers = [{"coin": h["coin"], "roi_pct": h["roi_pct"], "pnl": h["pnl"]}
              for h in reversed(by_roi) if h["roi_pct"] < 0][:5]

    total_pct = (total_pnl / total_invested * 100) if total_invested else 0.0

    return {
        "total_value": round(total_value, 2),
        "cash": round(total_cash, 2),
        "allocated": round(total_coin_value, 2),
        "invested": round(total_invested, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pct, 2),
        "holdings": holdings,
        "allocation": sorted(alloc, key=lambda a: a["value"], reverse=True),
        "winners": winners,
        "losers": losers,
        "count": len(coins),
    }
