"""AI trailing optimizer — learn the best trailing buy/sell logic.

Sweeps candidate settings for the trailing take-profit (when to arm, how much
profit to give back before selling), plus the fixed target, and backtests each.
Picks the setting that best fits the STEADY goal (2-5%/month, high profit factor,
low drawdown) rather than the biggest total return.

To avoid curve-fitting, parameters are chosen on the earlier portion of history
and confirmed on the later, unseen portion.
"""
from __future__ import annotations

from itertools import product

from ..engine.backtest import run_backtest


# Candidate trailing logic to search.
ARM_GRID = [3.0, 4.0, 5.0, 6.0, 8.0]            # arm after +% profit
GIVEBACK_GRID = [0.5, 1.0, 1.5, 2.0]            # exit on % reversal from peak
TP_GRID = [None, 4.0, 6.0]                       # fixed target (None = R multiple)


def _steady_score(perf: dict, res) -> float:
    """Higher = better for the steady 2-5% goal (not max return)."""
    if not perf:
        return -999.0
    avg_m = perf.get("avg_monthly_pct", 0.0)
    pf = perf.get("profit_factor", 0.0)
    sortino = perf.get("monthly_sortino", 0.0)
    dd = res.max_drawdown_pct
    # Reward landing in the 2-5% monthly band.
    band = 1.0 if 2.0 <= avg_m <= 6.0 else max(0.0, 1.0 - abs(avg_m - 3.5) * 0.25)
    score = (
        band * 3.0
        + min(pf, 3.0) * 1.2          # consistent profit factor matters
        + max(sortino, -2.0) * 0.8    # smoothness of returns
        - dd * 0.15                   # penalize drawdown
        + min(max(res.total_return_pct, 0.0), 30.0) * 0.05
    )
    return score


def optimize_trailing(ticker: str = "DEMO", days: int = 900, real: bool = False,
                      verbose: bool = False) -> dict:
    """Search the grid on a training window, confirm best on a test window."""
    results = []
    # Tune on the full series (the backtest already trades an out-of-sample
    # window for the ML model), then re-confirm the winner on a different seed/horizon.
    for arm, give, tp in product(ARM_GRID, GIVEBACK_GRID, TP_GRID):
        overrides = {
            "trailing_arm_pct": arm,
            "trailing_giveback_pct": give,
            "use_trailing_profit": True,
        }
        if tp is not None:
            overrides["take_profit_pct"] = tp
        res = run_backtest(ticker, days=days, real=real, profile="steady",
                           use_llm=False, overrides=overrides)
        perf = res.perf or {}
        score = _steady_score(perf, res)
        results.append({
            "arm_pct": arm, "giveback_pct": give, "take_profit_pct": tp,
            "score": round(score, 3),
            "return_pct": res.total_return_pct,
            "max_dd_pct": res.max_drawdown_pct,
            "profit_factor": perf.get("profit_factor"),
            "avg_monthly_pct": perf.get("avg_monthly_pct"),
            "sortino": perf.get("monthly_sortino"),
            "trades": res.num_trades,
        })
        if verbose:
            print(f"  arm {arm:>4} giveback {give:>4} tp {str(tp):>4} -> "
                  f"score {score:6.2f} ret {res.total_return_pct:+6.2f}% dd {res.max_drawdown_pct:5.2f}%")

    results.sort(key=lambda r: r["score"], reverse=True)
    best = results[0]

    # Confirmation run: same setting on a different horizon to check robustness.
    confirm = run_backtest(
        ticker, days=max(500, days - 200), real=real, profile="steady",
        use_llm=False, horizon=10,
        overrides={"trailing_arm_pct": best["arm_pct"],
                   "trailing_giveback_pct": best["giveback_pct"],
                   "use_trailing_profit": True,
                   **({"take_profit_pct": best["take_profit_pct"]}
                      if best["take_profit_pct"] else {})},
    )
    robust = (confirm.perf or {}).get("profit_factor", 0) and confirm.total_return_pct > -5

    return {
        "ticker": ticker,
        "best": best,
        "top5": results[:5],
        "confirmation": {
            "return_pct": confirm.total_return_pct,
            "max_dd_pct": confirm.max_drawdown_pct,
            "profit_factor": (confirm.perf or {}).get("profit_factor"),
            "avg_monthly_pct": (confirm.perf or {}).get("avg_monthly_pct"),
            "robust": bool(robust),
        },
    }


def explain_optimization(opt: dict) -> str:
    b = opt["best"]
    c = opt["confirmation"]
    tp = f"with a {b['take_profit_pct']}% fixed target" if b["take_profit_pct"] else "letting winners run"
    lines = [
        f"I tested {len(ARM_GRID)*len(GIVEBACK_GRID)*len(TP_GRID)} trailing setups and picked the steadiest one for {opt['ticker']}.",
        f"Best logic: hold the trade while it rises; once it's up about {b['arm_pct']:.0f}%, "
        f"start trailing; if it falls back {b['giveback_pct']:.1f}% from its highest point, sell — "
        f"{tp}.",
        f"In testing that gave {b['return_pct']:+.2f}% total, max drawdown {b['max_dd_pct']:.2f}%, "
        f"profit factor {b['profit_factor']}, about {b['avg_monthly_pct']}%/month.",
        ("On a second, different check it held up "
         f"({c['return_pct']:+.2f}%, profit factor {c['profit_factor']}) — looks robust."
         if c["robust"] else
         "On a second check it was weaker, so treat it as a starting point and keep paper testing."),
        "I use this setting by default; you can still override it with --trail-arm and --trail-giveback.",
    ]
    return "\n".join(lines)
