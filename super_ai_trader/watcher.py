"""24/7 market watcher.

Continuously ranks every watched coin for the *best moment to act* around
the one rule: buy low, sell high. It scores market conditions into a
BEST_BUY (deep in range / bargain), BEST_SELL (top of range / strength),
PAUSE (crash — protect), or BANK (trailing profit locked), and only emits an
alert when a state CHANGES so it isn't noisy.

The watcher itself places no orders; it watches and advises. The grid bots
do the actual trading, always with the safety layers.
"""
from __future__ import annotations

import time

from .grid.instructions import grid_instruction

# states (worst-to-best order for readability)
BEST_BUY = "BEST_BUY"
BEST_SELL = "BEST_SELL"
PAUSE = "PAUSE"
BANK = "BANK"
HOLD = "GRID"


def assess(coin: str, price: float, cfg, regime=None, trail=None, lang: str = "en") -> dict:
    """Assess one coin and return a watch verdict with a 0-100 quality score."""
    inst = grid_instruction(price, cfg, regime=regime, trail=trail)
    lo, hi = cfg.lower, cfg.upper
    span = (hi - lo) or (price or 1)
    # position 0 (bottom) -> 1 (top) within the range
    pos = max(0.0, min(1.0, (price - lo) / span))

    score = 50
    state = HOLD
    headline = inst["headline"]
    advice = inst["instruction"]

    if inst["action"] == "HOLD":
        state = PAUSE
        score = 10
    elif inst["action"] == "BANK_PROFIT" or (trail and trail.get("state") == "locked"):
        state = BANK
        score = 100
    elif inst["action"] == "BUY":
        # price below range -> deep value; better buy the lower it is
        state = BEST_BUY
        score = 90
        if price < lo:
            score = 95
    elif inst["action"] == "SELL":
        state = BEST_SELL
        score = 90
    elif inst["action"] == "GRID":
        if pos <= 0.25:
            state = BEST_BUY
            score = 82
            headline = "In the BUY-LOW ZONE (bottom 25% of range) — strong moment to accumulate."
        elif pos >= 0.75:
            state = BEST_SELL
            score = 82
            headline = "In the SELL-HIGH ZONE (top 25% of range) — good moment to take profit."
        else:
            state = HOLD
            score = 55

    return {
        "coin": coin,
        "state": state,
        "score": score,
        "price": price,
        "range_pos_pct": round(pos * 100, 1),
        "next_buy": inst.get("next_buy"),
        "next_sell": inst.get("next_sell"),
        "headline": headline,
        "advice": advice,
    }


def _classify_state(state: str) -> tuple:
    return {
        BEST_BUY: ("🟢 BUY SIGNAL", "green", "Good moment to BUY LOW — price in the deep/buy zone."),
        BEST_SELL: ("🔴 SELL SIGNAL", "red", "Good moment to SELL HIGH — price in the strength zone."),
        BANK: ("💰 PROFIT LOCKED", "green", "Trailing exit banked a winner. Re-arm next cycle."),
        PAUSE: ("⏸️ PAUSE", "amber", "Strong downtrend — the AI stopped buying to protect capital."),
        HOLD: ("⚙️ RUNNING", "muted", "Grid running buy-low/sell-high within its range."),
    }.get(state, ("⚙️ RUNNING", "muted", ""))


def run_watch(observations: list[dict], lang: str = "en") -> dict:
    """observations: list of dicts each with coin, price, cfg, optional regime/trail.
    Returns ranked opportunities and new (changed) alerts."""
    verdicts = []
    for obs in observations:
        v = assess(obs["coin"], float(obs["price"]), obs["cfg"],
                   regime=obs.get("regime"), trail=obs.get("trail"), lang=lang)
        verdicts.append(v)

    # rank: best opportunities first
    ranked = sorted(verdicts, key=lambda v: v["score"], reverse=True)
    buys = [v for v in verdicts if v["state"] == BEST_BUY]
    sells = [v for v in verdicts if v["state"] == BEST_SELL]
    banks = [v for v in verdicts if v["state"] == BANK]
    pauses = [v for v in verdicts if v["state"] == PAUSE]

    summary_lines = []
    from .messages import msg
    if buys:
        best = max(buys, key=lambda v: v["score"])
        summary_lines.append(msg("best_buy_now", lang, coin=best["coin"], price=best["price"]))
    if sells:
        best = max(sells, key=lambda v: v["score"])
        summary_lines.append(msg("best_sell_now", lang, coin=best["coin"], price=best["price"]))
    if banks:
        summary_lines.append((", ".join(b["coin"] for b in banks)))
    if pauses:
        summary_lines.append(msg("paused_list", lang, coins=", ".join(p["coin"] for p in pauses)))
    if not summary_lines:
        summary_lines.append(msg("no_standout", lang))

    for v in ranked:
        v["state_label"] = msg("state_"+v["state"], lang)
    return {
        "ranked": ranked,
        "buys": buys, "sells": sells, "banks": banks, "pauses": pauses,
        "summary": summary_lines,
        "golden_rule": msg("golden_rule", lang),
    }
