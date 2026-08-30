"""AI daily market briefing — a plain-English summary.

Aggregates the live grid session(s), order-book pressure, and the tuned
settings into a few short sentences a beginner can understand. This is the
'daily briefing' feature most viral AI bots surface at the top of the app.
"""
from __future__ import annotations


def _word(pct: float) -> str:
    if pct <= -3:
        return "in a drawdown — the safety limits are doing their job"
    if pct <= -0.5:
        return "slightly down"
    if pct >= 1:
        return "in profit"
    return "roughly flat"


def build_briefing(multigrid: dict | None = None) -> dict:
    """multigrid = MultiGrid.summary()-like dict (optional)."""
    lines = []
    alerts = []
    multigrid = multigrid or {}
    coins = multigrid.get("coins") or []
    count = multigrid.get("count", 0)

    if count == 0:
        return {
            "headline": "No grids running right now.",
            "lines": [
                "Start a practice grid to watch the AI work — it pauses in "
                "crashes, trails winners, and reports every action.",
                "Tip: use a Balanced template and keep it in practice mode first.",
            ],
            "alerts": [],
        }

    total_pnl = multigrid.get("total_pnl", 0.0) or 0.0
    paused = multigrid.get("paused_coins", []) or []
    active = multigrid.get("active_coins", []) or []
    rt = multigrid.get("total_round_trips", 0) or 0

    lines.append(
        f"Your {count} grid(s) are {_word(total_pnl)} overall, "
        f"with a total P/L of {total_pnl:+.2f} across {rt} completed buy→sell cycles."
    )

    # per-coin summary
    for c in coins:
        coin = c.get("coin", "")
        roi = c.get("roi_pct", 0.0) or 0.0
        if c.get("paused"):
            lines.append(f"• {coin}: grid paused — strong trend detected, the AI stopped buying to protect you.")
        else:
            note = (c.get("status_note") or {}).get("label", "running")
            lines.append(f"• {coin}: {note.lower()} ({roi:+.1f}%).")

    if paused:
        lines.append("Protection is active on: " + ", ".join(paused) +
                     ". Grids resume automatically when the market settles back into a range.")
    elif active:
        lines.append("All active grids are running normally within their ranges.")

    if multigrid.get("kill_tripped"):
        alerts.append(multigrid.get("kill_reason", "Drawdown stop triggered."))

    headline = (f"Portfolio {_word(total_pnl)} ({total_pnl:+.2f})."
                f" {len(paused)} paused, {len(active)} active.")
    return {"headline": headline, "lines": lines, "alerts": alerts,
            "total_pnl": total_pnl, "round_trips": rt,
            "paused": paused, "active": active}
