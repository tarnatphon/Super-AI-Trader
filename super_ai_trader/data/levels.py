"""Support / resistance (demand & supply zones).

Identifies swing highs/lows that were *confirmed* (a pivot at index i only uses bars
up to i+lookback), so there is no look-ahead in backtesting. Returns:

- nearest SUPPORT below price  -> demand zone (where buyers step in / BUY area)
- nearest RESISTANCE above     -> supply zone (where sellers step in / SELL area)
- a suggested stop price on the far side of the level.
"""
from __future__ import annotations

from .orderflow import flow_snapshot  # noqa: F401  (kept for API symmetry)


def pivot_levels(bars, lookback: int = 3, tol_pct: float = 0.01, idx: int | None = None):
    """Return (supports, resistances) confirmed up to bar `idx`.

    A swing low at i needs `lookback` bars on each side with higher lows and the bar
    at i being the minimum; swings are clustered within `tol_pct`.
    """
    end = len(bars) if idx is None else min(idx + 1, len(bars))
    supports: list[float] = []
    resistances: list[float] = []

    def cluster(levels: list[float], price: float):
        for j, lv in enumerate(levels):
            if abs(price - lv) / lv <= tol_pct:
                levels[j] = (levels[j] + price) / 2
                return
        levels.append(price)

    # A pivot at i is only knowable once bars through i+lookback have printed.
    last_known = end - 1 - lookback
    for i in range(lookback, max(lookback, last_known + 1)):
        window = bars[i - lookback : i + lookback + 1]
        low_i = bars[i].low
        high_i = bars[i].high
        if low_i <= min(b.low for b in window):
            cluster(supports, low_i)
        if high_i >= max(b.high for b in window):
            cluster(resistances, high_i)
    return sorted(supports), sorted(resistances)


def level_setup(bars, idx: int, flow: dict | None = None,
                lookback: int = 3, atr_pct: float | None = None) -> dict:
    """Where to buy/sell around the current price, plus a stop.

    Returns a dict with nearest support/resistance, zone status, and order prices.
    """
    price = bars[idx].close
    supports, resistances = pivot_levels(bars, lookback=lookback, idx=idx)
    supports_below = [s for s in supports if s < price]
    resist_above = [r for r in resistances if r > price]

    support = supports_below[-1] if supports_below else None
    resistance = resist_above[0] if resist_above else None

    # Proximity (in %) to the zones — inside ~0.5 ATR we treat as "at the zone".
    prox = max((atr_pct or 1.0) * 0.6, 0.4)
    at_support = support is not None and (price / support - 1) * 100 <= prox
    at_resistance = resistance is not None and (resistance / price - 1) * 100 <= prox

    # Suggested orders.
    buy_zone = support if at_support else None
    sell_zone = resistance if at_resistance else None
    stop_long = support * (1 - max((atr_pct or 1.0) * 0.5, 0.5) / 100) if support else None
    stop_short = resistance * (1 + max((atr_pct or 1.0) * 0.5, 0.5) / 100) if resistance else None

    return {
        "price": round(price, 4),
        "support": round(support, 4) if support else None,       # demand / BUY area
        "resistance": round(resistance, 4) if resistance else None,  # supply / SELL area
        "at_support": bool(at_support),
        "at_resistance": bool(at_resistance),
        "buy_zone": round(buy_zone, 4) if buy_zone else None,
        "sell_zone": round(sell_zone, 4) if sell_zone else None,
        "stop_below": round(stop_long, 4) if stop_long else None,
        "stop_above": round(stop_short, 4) if stop_short else None,
        "dist_to_support_pct": round((price / support - 1) * 100, 2) if support else None,
        "dist_to_resist_pct": round((resistance / price - 1) * 100, 2) if resistance else None,
    }
