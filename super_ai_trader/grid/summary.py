"""Build a Binance-style 'Bot Details' summary for a running/finished grid.

Includes: ROI %, PNL, matched trades, price range, grids, mode, profit per grid,
a historical-profit equity curve, and a Bot Preview series (price + EMA 7/25/99
with buy levels below price and sell levels above).
"""
from __future__ import annotations

from ..data.indicators import closes, ema
from .engine import grid_lines
from .trailing_visual import trailing_from_bars


def bot_summary(cfg, res, bars, tail: int = 120) -> dict:
    c = closes(bars)
    e7, e25, e99 = ema(c, 7), ema(c, 25), ema(c, 99)
    n = len(bars)
    t = min(tail, n)

    def ser(vals):
        return [round(v, 4) if v is not None else None for v in vals[-t:]]

    price_now = c[-1]
    lines = grid_lines(cfg, c[0])
    # Preview ladder wraps around the CURRENT price: buys below, sells above,
    # using the grid's geometric/arithmetic spacing (like the exchange bot preview).
    lo_band, hi_band = price_now * 0.6, price_now * 1.6
    if cfg.mode == "geometric":
        step = (cfg.upper / cfg.lower) ** (1.0 / cfg.grids)
        buy_levels = [round(price_now / (step ** k), 4) for k in range(1, 20)]
        sell_levels = [round(price_now * (step ** k), 4) for k in range(1, 20)]
    else:
        step = (cfg.upper - cfg.lower) / cfg.grids
        buy_levels = [round(price_now - step * k, 4) for k in range(1, 20)]
        sell_levels = [round(price_now + step * k, 4) for k in range(1, 20)]
    # Keep levels near the current price (the visible ladder), most recent first.
    buy_levels = [p for p in buy_levels if p >= lo_band][-12:]
    sell_levels = [p for p in sell_levels if p <= hi_band][:12]

    roi = (res.final_equity / cfg.investment - 1) * 100
    pnl = res.final_equity - cfg.investment
    profit_per_grid = (
        (res.grid_profit / cfg.investment / max(1, res.filled_round_trips)) * 100
    )

    curve = res.equity_curve or [(b.date, cfg.investment) for b in bars]
    curve_vals = [round(v, 2) for _d, v in curve[-t:]]

    # Trailing behavior visual (climbing exit line + holding/locked state).
    trail = trailing_from_bars(bars, arm_pct=5.0, giveback_pct=1.0, tail=120)

    return {
        "symbol": cfg.symbol,
        "trail": trail,
        "mode": cfg.mode,
        "grids": cfg.grids,
        "lower": round(cfg.lower, 4),
        "upper": round(cfg.upper, 4),
        "price_now": round(price_now, 4),
        "roi_pct": round(roi, 2),
        "pnl": round(pnl, 2),
        "matched_trades_total": res.filled_round_trips,
        "fees": res.fees_paid,
        "grid_profit": res.grid_profit,
        "unrealized": res.unrealized_pnl,
        "stopped": res.stopped,
        "profit_per_grid_pct": round(profit_per_grid, 3),
        "runtime": "practice run",
        "profit_curve": curve_vals,
        "preview": {
            "dates": [b.date for b in bars[-t:]],
            "price": ser(c),
            "ema7": ser(e7),
            "ema25": ser(e25),
            "ema99": ser(e99),
            "buy_levels": buy_levels[-14:],
            "sell_levels": sell_levels[:14],
        },
    }
