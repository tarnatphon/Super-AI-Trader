"""AI regime filter — protect the grid from strong trends.

Grids profit in ranges and lose money in strong trends (they buy into a fall or
sell into a rise). This gate reads trend strength and position inside the grid:

- RANGE      -> run the grid normally (this is where it makes steady wins).
- STRONG DOWN -> PAUSE new buys: price is breaking below the grid (risk of bags).
- STRONG UP   -> the grid sells inventory into the rally (good), no new buys; note
                 it may underperform buy-and-hold.
- TRANSITION  -> neutral/changing; allow light action.

Signals (no look-ahead; all from bars up to now):
- ADX (trend strength) >= adx_trend -> strong trend
- ±DI direction and price vs grid bounds
"""
from __future__ import annotations

from ..data.indicators import adx, closes


def regime_gate(bars, cfg, adx_trend: float = 25.0) -> dict:
    """Decide whether the grid should be active.

    cfg: a GridConfig (uses .lower / .upper). Returns a dict with status + plain text.
    """
    n = len(bars)
    price = closes(bars)[-1]
    if n < 40:
        return {"status": "range", "active": True, "adx": None,
                "reason": "warming up — treat as range", "action": "run normally"}
    adx_v, pdi, mdi = adx(bars, 14)
    a = adx_v[-1]
    strong = a is not None and a >= adx_trend
    trending_up = pdi[-1] is not None and mdi[-1] is not None and pdi[-1] > mdi[-1]
    trending_down = pdi[-1] is not None and mdi[-1] is not None and mdi[-1] > pdi[-1]

    # Distance to grid edges.
    near_lower = cfg.lower and price <= cfg.lower * 1.01
    near_upper = cfg.upper and price >= cfg.upper * 0.99

    if strong and trending_down and (near_lower or price < cfg.lower):
        status, active = "strong_down", False
        reason = "Strong DOWNTREND: price is breaking below the grid. Pause new buys."
        action = "PAUSE grid — protect capital from buying into a fall"
    elif strong and trending_down:
        status, active = "transition", False
        reason = "Downtrend strengthening. Hold off until price settles back into range."
        action = "stand by (no new buys)"
    elif strong and trending_up and (near_upper or price > cfg.upper):
        status, active = "strong_up", False
        reason = "Strong UPTREND: price above the grid. Existing sells capture gains; no new buys."
        action = "let sells take profit; wait for pullback"
    elif strong and trending_up:
        status, active = "strong_up", True
        reason = "Uptrend: grid is selling into strength (good for taking profit)."
        action = "run, but expect to underperform buy-and-hold"
    else:
        status, active = "range", True
        reason = "Range / calm market — the grid's best environment."
        action = "run normally (buy low, sell high)"

    return {
        "status": status, "active": active,
        "adx": round(a, 1) if a is not None else None,
        "plus_di": round(pdi[-1], 1) if pdi[-1] is not None else None,
        "minus_di": round(mdi[-1], 1) if mdi[-1] is not None else None,
        "price": round(price, 6),
        "lower": cfg.lower, "upper": cfg.upper,
        "reason": reason, "action": action,
    }
