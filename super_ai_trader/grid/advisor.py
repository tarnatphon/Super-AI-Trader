"""Grid 'Auto-Set' advisor — picks safe, sensible grid parameters for you.

Combines the best ideas from the Binance and Gate.io grid UIs but with our own
plain-language logic:
- Binance:  "Fill AI parameters" / AI-suggested range from recent volatility.
- Gate.io:  arithmetic (fixed step) for calm markets vs geometric (fixed %) for
            volatile markets, plus recommended grid counts by condition.

Everything is computed from the price data; no external service, no keys.
"""
from __future__ import annotations

from statistics import pstdev

from .engine import GridConfig, simulate_on_bars


def _recent_volatility_pct(bars, lookback: int = 60) -> float:
    """Average daily range (high-low)/close over recent bars, as a %."""
    window = bars[-lookback:] if len(bars) >= lookback else bars
    if len(window) < 2:
        return 2.0
    daily_ranges = [abs(b.high - b.low) / b.close * 100 for b in window]
    return sum(daily_ranges) / len(daily_ranges)


def advise(bars, investment: float = 10_000.0, grids: int | None = None,
           risk_mode: str = "steady") -> dict:
    """Return a suggested GridConfig + a plain-language explanation.

    risk_mode: 'steady' (small, safe default) or 'wide' (bigger range).
    """
    price = bars[-1].close
    vol = _recent_volatility_pct(bars)

    # Geometric spacing when price swings a lot (vol%), arithmetic when calm.
    mode = "geometric" if vol >= 3.0 else "arithmetic"

    # Range width from volatility: calm -> tighter, wild -> wider.
    width_pct = max(6.0, min(30.0, vol * 4.0))
    if risk_mode == "wide":
        width_pct = min(40.0, width_pct * 1.4)

    n_grids = grids or (25 if vol < 4 else 35)

    lower = price * (1 - width_pct / 100)
    upper = price * (1 + width_pct / 100)
    # Protections sit OUTSIDE the grid (Gate.io rule).
    stop_loss = lower * (1 - width_pct / 100)
    take_profit = upper * (1 + width_pct / 100)

    # Fee profile: Binance 0.1% maker (0.075 w/ BNB); Gate ~0.1-0.15%.
    fee = 0.1

    cfg = GridConfig(
        symbol="AUTO/USDT",
        lower=round(lower, 6), upper=round(upper, 6),
        grids=n_grids, mode=mode, investment=investment,
        fee_pct=fee, range_pct=width_pct,
        stop_loss_price=round(stop_loss, 6),
        take_profit_price=round(take_profit, 6),
    )

    # Prove the settings on recent history (a backtest) before recommending.
    res = simulate_on_bars(cfg, bars)

    spacing = width_pct / n_grids
    explanation = {
        "market_calm": vol < 3.0,
        "volatility_pct": round(vol, 2),
        "grid_type": mode,
        "grid_type_reason": (
            "Prices have been calm, so even price steps work best." if mode == "arithmetic"
            else "Prices have been swinging, so even % steps protect you at low prices."),
        "range_width_pct": round(width_pct, 1),
        "grid_count": n_grids,
        "spacing_pct": round(spacing, 2),
        "spacing_ok": spacing >= 0.4,
        "stop_loss": cfg.stop_loss_price,
        "take_profit": cfg.take_profit_price,
        "projected_round_trips": res.filled_round_trips,
        "projected_fees": res.fees_paid,
        "projected_end_equity": res.final_equity,
        "projected_return_pct": round((res.final_equity / investment - 1) * 100, 2),
        "warning_inventory": res.unrealized_pnl < 0,
    }
    return {"config": cfg, "why": explanation, "result": res}


def plain_language(adv: dict) -> list[str]:
    """One-line, jargon-free sentences suitable for a 10-year-old / 70-year-old."""
    w = adv["why"]
    lines = [
        f"Recent price swings are about {w['volatility_pct']}% a day "
        f"({'calm' if w['market_calm'] else 'bouncy'}).",
        f"I chose a {'flat-step' if w['grid_type'] == 'arithmetic' else 'percentage-step'} "
        f"grid because {w['grid_type_reason'].lower()}",
        f"The bot buys from {w['range_width_pct']}% below now up to {w['range_width_pct']}% above, "
        f"split into {w['grid_count']} little steps.",
        ("The steps are comfortably bigger than the fees — good." if w["spacing_ok"]
         else "The steps are too close together; fees could eat profits. Use fewer grids."),
        f"If price drops to {w['stop_loss']} the bot STOPS to protect your money; "
        f"if it reaches {w['take_profit']} it cashes out the gain.",
    ]
    if w["warning_inventory"]:
        lines.append("Heads up: in this test the price fell hard and the bot was still "
                     "holding coins. That's why the stop-loss is ON.")
    return lines
