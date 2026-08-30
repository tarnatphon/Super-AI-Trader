"""AI grid instructions — the bot's live rulebook.

The core rule is simple: BUY LOW, SELL HIGH. This module turns the live
price + grid levels + regime + trailing state into a concrete INSTRUCTION
the bot follows (and that the user can read), so the AI is always telling
the bot what to do rather than just reporting numbers.

Instructions are safe/advisory: they describe what the engine already does
(buy below price, sell above, pause in crashes, trail winners) and surface
it as clear, plain-language commands.
"""
from __future__ import annotations


def grid_instruction(price: float, cfg, regime=None, trail=None) -> dict:
    """Return a single current instruction for the grid.

    - price: last live price
    - cfg:   GridConfig (lower/upper/grids/range)
    - regime: regime_gate result (status/active/reason) optional
    - trail:  trailing state (state/locked) optional
    """
    lo = cfg.lower
    hi = cfg.upper
    span = (hi - lo) if (hi and lo and hi > lo) else (price or 1)
    step = span / max(1, cfg.grids)

    # 1) Regime safety overrides everything.
    if regime is not None and not regime.get("active", True):
        st = regime.get("status", "trend")
        if "down" in st:
            return {
                "action": "HOLD",
                "tone": "amber",
                "headline": "PAUSE buying — strong downtrend.",
                "instruction": ("Stand down on new buys. Do NOT catch the falling "
                                "knife. Keep existing low buy orders and let the grid "
                                "resume when price settles back into range. Rule: protect "
                                "capital first, then buy low."),
                "next_buy": None, "next_sell": None,
            }
        return {
            "action": "HOLD",
            "tone": "amber",
            "headline": "PAUSE buying — strong uptrend/price above grid.",
            "instruction": ("Don't chase the move higher. Let existing low buys SELL "
                            "into the strength (sell high). Resume new buys when price "
                            "pulls back into the range."),
            "next_buy": None, "next_sell": None,
        }

    # 2) Trailing winner locked.
    if trail is not None and trail.get("state") == "locked":
        return {
            "action": "BANK_PROFIT",
            "tone": "green",
            "headline": "Trailing exit locked — profit banked. Sell high ✔",
            "instruction": ("Winner reached +target and reversed; the trail took the "
                            "profit. Reinstate the next high sell order and the next low "
                            "buy to restart the cycle."),
            "next_buy": round(price - step, 6),
            "next_sell": round(price + step, 6),
        }

    # 3) Normal grid: where is price in the range?
    if price <= lo:
        # below the whole grid -> bargain zone
        return {
            "action": "BUY",
            "tone": "green",
            "headline": "BELOW range — bargain / buy-low zone.",
            "instruction": ("Price is under the lowest grid line: this is the deepest "
                            "buy-low zone. Place the next buy order just above price and "
                            "wait for the bounce to sell high. Keep buy size small and staggered."),
            "next_buy": round(price, 6),
            "next_sell": round(price + step, 6),
        }
    if price >= hi:
        return {
            "action": "SELL",
            "tone": "green",
            "headline": "ABOVE range — sell-high zone.",
            "instruction": ("Price is over the highest grid line: take profit / let sells "
                            "fill into strength. Do not open new buys this high; wait for a "
                            "pullback to buy low again."),
            "next_buy": round(price - step, 6),
            "next_sell": round(hi, 6),
        }

    # inside the range — next grid levels
    pos = (price - lo) / span
    next_buy = price - step
    next_sell = price + step
    # simple trend hint
    zone = (
        "in the lower half of the range — buy-low bias, look to sell higher"
        if pos < 0.5 else
        "in the upper half of the range — sell-high bias, wait to rebuy lower"
    )
    return {
        "action": "GRID",
        "tone": "green",
        "headline": "Running the buy-low / sell-high grid.",
        "instruction": (f"Price is {zone}. Hold a buy ladder below and a sell ladder above; "
                        f"each cycle buys low at ~{next_buy:g} and sells high at ~{next_sell:g}. "
                        "Trail any runner past +5% and bank it on reversal."),
        "next_buy": round(next_buy, 6),
        "next_sell": round(next_sell, 6),
        "position_in_range": round(pos, 2),
    }


def rule_reminder() -> str:
    return ("Golden rule: BUY LOW, SELL HIGH. The grid staggers buy orders below price "
            "and sell orders above; the AI pauses buying in crashes and trails runners to "
            "lock profit — it never chases price upward with new buys.")
