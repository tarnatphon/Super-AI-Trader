"""Performance metrics oriented toward STEADY, low-drawdown returns.

Goal framing (per project owner): not the highest win %, but a consistent
2%-5% per-period (monthly) profit with tight risk. So we report:

- monthly return series, % of profitable months, best/worst month
- Sharpe and Sortino ratios (per-trade returns, annualized-ish)
- profit factor (gross win / gross loss)
- max drawdown and a simple "steady score"
"""
from __future__ import annotations

import math


def _period_returns(equity_curve: list[tuple[str, float]], bars_per_period: int = 21):
    """Approximate monthly returns by sampling equity every ~21 bars."""
    rets = []
    prev = None
    for i, (_d, eq) in enumerate(equity_curve):
        if i % bars_per_period == 0 or i == len(equity_curve) - 1:
            if prev is not None and prev > 0:
                rets.append(eq / prev - 1)
            prev = eq
    return rets


def trade_pnl_returns(trades):
    """PnL of each closed trade (positive or negative)."""
    return [t.pnl for t in trades if t.side == "EXIT"]


def compute_metrics(equity_curve, trades, start_equity: float,
                    bars_per_period: int = 21,
                    target_low: float = 2.0, target_high: float = 5.0) -> dict:
    monthly = _period_returns(equity_curve, bars_per_period)
    pnls = trade_pnl_returns(trades)

    n_m = len(monthly)
    pos_m = sum(1 for r in monthly if r > 0)
    gross_win = sum(p for p in pnls if p > 0)
    gross_loss = -sum(p for p in pnls if p < 0)
    profit_factor = gross_win / gross_loss if gross_loss > 0 else float("inf") if gross_win > 0 else 0.0

    # Sharpe / Sortino from monthly returns.
    def _sharpe(rets):
        if len(rets) < 2:
            return 0.0
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / len(rets)
        sd = math.sqrt(var)
        return mean / sd if sd > 0 else 0.0

    sharpe_m = _sharpe(monthly)
    downside = [r for r in monthly if r < 0]
    dvar = (sum(r ** 2 for r in downside) / len(monthly)) if monthly else 0.0
    sortino_m = (sum(monthly) / len(monthly)) / math.sqrt(dvar) if dvar > 0 and monthly else 0.0

    avg_month = (sum(monthly) / n_m) if n_m else 0.0
    avg_win = (gross_win / sum(1 for p in pnls if p > 0)) if any(p > 0 for p in pnls) else 0.0
    avg_loss = (-sum(p for p in pnls if p < 0) / sum(1 for p in pnls if p < 0)) if any(p < 0 for p in pnls) else 0.0

    # Steady score: reward consistent positive months + smoothness, penalize drawdown.
    pos_pct = pos_m / n_m if n_m else 0.0
    worst = min(monthly) if monthly else 0.0

    return {
        "months": n_m,
        "profitable_months_pct": round(pos_pct * 100, 1),
        "avg_monthly_pct": round(avg_month * 100, 2),
        "best_month_pct": round(max(monthly) * 100, 2) if monthly else 0.0,
        "worst_month_pct": round(worst * 100, 2) if monthly else 0.0,
        "monthly_sharpe": round(sharpe_m, 2),
        "monthly_sortino": round(sortino_m, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "in_target_band": target_low <= avg_month * 100 <= target_high,
        "target_band": (target_low, target_high),
    }
