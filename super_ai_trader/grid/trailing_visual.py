"""Visualize the trailing take-profit over a series.

Produces, over recent bars:
- the price line
- the climbing exit (trailing stop) line once the runner arms
- markers: ENTRY, ARMED (hit +arm%), LOCKED (exit on reversal)

This is the data behind the Bot Details "holding for more / locked profit"
chart. It mirrors the engine's trailing rule:
  arm once gain >= arm_pct; then the exit target = peak*(1-giveback_pct);
  exit when price crosses that target.
"""
from __future__ import annotations

from ..data.indicators import closes


def simulate_trailing(closes_list: list[float], arm_pct: float = 5.0,
                      giveback_pct: float = 1.0) -> dict:
    """Walk forward from the first close; return lines and state labels."""
    n = len(closes_list)
    price_line = [round(p, 6) for p in closes_list]
    exit_line: list[float | None] = [None] * n
    state_line: list[str] = [""] * n

    entry = closes_list[0]
    armed = False
    peak = entry
    exit_target = None
    locked = False
    locked_price = None

    for i in range(n):
        p = closes_list[i]
        if locked:
            state_line[i] = "LOCKED"
            exit_line[i] = exit_target
            continue
        if armed:
            peak = max(peak, p)
            candidate = peak * (1 - giveback_pct / 100)
            exit_target = candidate
            exit_line[i] = round(candidate, 6)
            if p <= candidate:
                locked = True
                locked_price = candidate
                state_line[i] = "LOCKED"
                continue
            state_line[i] = "HOLDING_PEAK"
            continue
        # not armed yet
        if p >= entry * (1 + arm_pct / 100):
            armed = True
            peak = p
            state_line[i] = "ARMED"
            exit_target = peak * (1 - giveback_pct / 100)
            exit_line[i] = round(exit_target, 6)
            if p <= exit_target:
                locked = True
                locked_price = exit_target
                state_line[i] = "LOCKED"
        else:
            state_line[i] = "HOLDING"
            exit_line[i] = None

    final_gain = None
    current_gain = round((closes_list[-1] / entry - 1) * 100, 2)
    if locked_price is not None:
        final_gain = round((locked_price / entry - 1) * 100, 2)
        current_gain = final_gain  # after exit, the position is closed

    state = "locked" if locked else "holding" if armed else "watching"
    return {
        "entry": round(entry, 6),
        "arm_pct": arm_pct,
        "giveback_pct": giveback_pct,
        "armed_at": round(entry * (1 + arm_pct / 100), 6),
        "peak": round(peak, 6) if armed else None,
        "price": price_line,
        "exit_line": exit_line,
        "state": state,
        "locked_gain_pct": final_gain,
        "current_gain_pct": current_gain,
    }


def trailing_from_bars(bars, arm_pct: float = 5.0, giveback_pct: float = 1.0,
                       tail: int = 120) -> dict:
    c = closes(bars)[-tail:]
    sim = simulate_trailing(c, arm_pct, giveback_pct)
    return sim
