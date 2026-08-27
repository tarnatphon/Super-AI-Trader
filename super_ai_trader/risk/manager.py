"""Deterministic risk layer.

This module NEVER uses an LLM. It has absolute veto power over every order.
It implements the layered controls the practitioner community converged on
(see docs/RESEARCH-top-ai-traders-2026.md, section 5):

  1. per-trade position sizing from stop distance (risk a fixed % of equity)
  2. max position notional / max concurrent positions
  3. daily-loss kill switch (flatten + halt until manual reset)
  4. volatility / stale-data sanity checks before entry
  5. regime-based exposure scaling (bull / chop / bear)
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RiskConfig:
    risk_per_trade_pct: float = 0.75     # % of equity risked to the stop
    max_position_pct: float = 20.0       # max notional of equity in one position
    max_open_positions: int = 2
    daily_loss_limit_pct: float = 2.0    # kill-switch: stop trading for the day
    max_atr_pct: float = 6.0             # block entries in extreme volatility
    min_atr_pct: float = 0.05            # block dead/stale markets
    chop_size_scale: float = 0.4         # shrink size in choppy regimes
    bear_size_scale: float = 0.6         # shrink shorts in bear / longs reduced
    allow_shorts: bool = True
    take_profit_r_multiple: float = 1.5  # take profit at 1.5R (bank steady winners)
    take_profit_pct: float | None = None  # fixed % profit target (overrides R multiple)

    # Trailing profit (let winners run, lock gains on reversal):
    use_trailing_profit: bool = True      # once armed, trail the peak instead of fixed TP
    trailing_arm_pct: float = 5.0         # arm the trail after +5% in favour
    trailing_giveback_pct: float = 1.0    # exit if price retraces 1% from the best peak

    @classmethod
    def steady(cls):
        """Tuned for consistent, small 2-5%/month gains with tight drawdowns."""
        return cls(
            risk_per_trade_pct=0.5,
            max_position_pct=15.0,
            max_open_positions=2,
            daily_loss_limit_pct=1.5,
            max_atr_pct=5.0,
            chop_size_scale=0.35,
            bear_size_scale=0.5,
            take_profit_r_multiple=1.5,
        )

    @classmethod
    def aggressive(cls):
        """Higher risk / higher variance for comparison."""
        return cls(
            risk_per_trade_pct=1.5,
            max_position_pct=35.0,
            max_open_positions=4,
            daily_loss_limit_pct=4.0,
            max_atr_pct=9.0,
            chop_size_scale=0.6,
            bear_size_scale=0.8,
            take_profit_r_multiple=2.5,
        )


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    size_pct: float = 0.0                # % of equity to deploy (0 if blocked)


@dataclass
class RiskState:
    """Mutable account-level risk state tracked by the engine."""
    equity_start_of_day: float = 0.0
    open_positions: int = 0
    halted: bool = False
    halt_reason: str = ""
    day: str = ""

    def new_day(self, day: str, equity: float) -> None:
        self.day = day
        self.halted = False
        self.halt_reason = ""
        self.equity_start_of_day = equity


class RiskManager:
    def __init__(self, config: RiskConfig | None = None):
        self.cfg = config or RiskConfig()

    def check_entry(
        self,
        *,
        state: RiskState,
        side: str,                     # "BUY" or "SELL"
        price: float,
        stop_price: float | None,
        equity: float,
        regime: str,                   # "bull" | "chop" | "bear"
        atr_pct: float | None,
    ) -> RiskDecision:
        cfg = self.cfg

        if state.halted:
            return RiskDecision(False, f"kill-switch active ({state.halt_reason})", 0.0)

        if side == "SELL" and not cfg.allow_shorts:
            return RiskDecision(False, "shorts disabled", 0.0)

        if state.open_positions >= cfg.max_open_positions:
            return RiskDecision(False, "max open positions reached", 0.0)

        # Volatility / stale-data sanity checks.
        if atr_pct is not None:
            if atr_pct > cfg.max_atr_pct:
                return RiskDecision(False, f"volatility too high (ATR {atr_pct}%)", 0.0)
            if atr_pct < cfg.min_atr_pct:
                return RiskDecision(False, "market too thin/stale", 0.0)

        # Position size from stop distance (risk fixed % of equity).
        if stop_price and price != stop_price:
            stop_dist = abs(price - stop_price) / price
            base_size = cfg.risk_per_trade_pct / (stop_dist * 100) * 100
        else:
            base_size = cfg.risk_per_trade_pct  # fallback tiny size if no stop

        # Regime scaling.
        scale = 1.0
        if regime == "chop":
            scale = cfg.chop_size_scale
        elif regime == "bear":
            scale = cfg.bear_size_scale if side == "BUY" else 1.0
        elif regime == "bull" and side == "SELL":
            scale = cfg.bear_size_scale

        size_pct = min(base_size * scale, cfg.max_position_pct)
        if size_pct <= 0:
            return RiskDecision(False, "computed size zero", 0.0)

        return RiskDecision(True, "ok", round(size_pct, 2))

    def check_day(self, state: RiskState, equity: float) -> bool:
        """Return True if trading may continue; triggers kill-switch if not."""
        if state.equity_start_of_day <= 0:
            return True
        pnl_pct = (equity / state.equity_start_of_day - 1) * 100
        if pnl_pct <= -self.cfg.daily_loss_limit_pct:
            state.halted = True
            state.halt_reason = f"daily loss limit hit ({pnl_pct:.2f}%)"
            return False
        return True
