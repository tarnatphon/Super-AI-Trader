"""Event-driven backtesting engine.

Runs the trading firm bar-by-bar, but the RiskManager has veto power over every
order. Positions use ATR-based stops; equity is marked to market each bar; a
daily-loss kill switch can halt trading. Long/short, long-only configurable, no
leverage (notional capped by equity).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..data.market import Bar, get_series
from ..data.indicators import snapshot
from ..agents.trading_firm import TradingFirm
from ..risk.manager import RiskManager, RiskConfig, RiskState


@dataclass
class Position:
    side: str               # "LONG" | "SHORT"
    qty: float
    entry: float
    stop: float
    entry_date: str


@dataclass
class Trade:
    date: str
    side: str
    qty: float
    price: float
    pnl: float
    reason: str


@dataclass
class BacktestResult:
    ticker: str
    final_equity: float
    start_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    num_trades: int
    wins: int
    win_rate_pct: float
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[tuple[str, float]] = field(default_factory=list)
    blocks: int = 0

    def summary(self) -> str:
        return (
            f"--- {self.ticker} backtest ---\n"
            f"  Start equity : {self.start_equity:,.2f}\n"
            f"  Final equity : {self.final_equity:,.2f}\n"
            f"  Total return : {self.total_return_pct:+.2f}%\n"
            f"  Max drawdown : {self.max_drawdown_pct:.2f}%\n"
            f"  Trades       : {self.num_trades} (win rate {self.win_rate_pct:.1f}%)\n"
            f"  Risk blocks  : {self.blocks}\n"
        )


def run_backtest(
    ticker: str = "DEMO",
    days: int = 750,
    real: bool = False,
    start_equity: float = 100_000,
    risk_config: RiskConfig | None = None,
    use_llm: bool = False,
    warmup: int = 210,
    verbose: bool = False,
) -> BacktestResult:
    bars = get_series(ticker, days=days, real=real)
    firm = TradingFirm(use_llm=use_llm)
    risk = RiskManager(risk_config or RiskConfig())
    state = RiskState()

    cash = start_equity
    position: Position | None = None
    trades: list[Trade] = []
    equity_curve: list[tuple[str, float]] = []
    peak = start_equity
    max_dd = 0.0
    blocks = 0
    current_day = ""

    for i in range(warmup, len(bars)):
        bar = bars[i]
        day = bar.date
        if day != current_day:
            current_day = day
            # equity at open approximation = cash + open position mark
            state.new_day(day, cash)

        price = bar.close

        # Mark to market.
        equity = cash
        if position:
            if position.side == "LONG":
                equity = cash + position.qty * price
            else:
                equity = cash + position.qty * (2 * position.entry - price)

        equity_curve.append((day, round(equity, 2)))
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak * 100)

        # Daily kill switch check.
        risk.check_day(state, equity)

        # Manage open position: stop-out or exit signal.
        if position:
            hit_stop = (
                (position.side == "LONG" and bar.low <= position.stop)
                or (position.side == "SHORT" and bar.high >= position.stop)
            )
            if hit_stop:
                exit_price = position.stop
                if position.side == "LONG":
                    pnl = (exit_price - position.entry) * position.qty
                    cash += position.qty * exit_price
                else:
                    # Release reserved margin and settle PnL.
                    pnl = (position.entry - exit_price) * position.qty
                    cash += position.qty * (2 * position.entry - exit_price)
                trades.append(Trade(day, "EXIT", position.qty, exit_price, pnl, "stop-out"))
                position = None
                state.open_positions -= 1

        # Ask the firm for a decision.
        snap = snapshot(bars, i)
        decision = firm.analyze(snap)
        raw_action = decision["action"]
        conviction = decision["conviction"]
        regime = decision["regime"]
        atr_pct = snap.get("atr14_pct")

        # Conviction hysteresis: weak signals are HOLD. Opposing signals need
        # to be even stronger to flip an open position (avoid churn/overtrade).
        ENTRY_MIN = 55
        FLIP_MIN = 70
        if conviction < ENTRY_MIN:
            action = "HOLD"
        else:
            action = raw_action
        if position and (
            (position.side == "LONG" and action == "SELL")
            or (position.side == "SHORT" and action == "BUY")
        ) and conviction < FLIP_MIN:
            action = "HOLD"

        # Flip if position conflicts with a strong opposite signal.
        if position and (
            (position.side == "LONG" and action == "SELL")
            or (position.side == "SHORT" and action == "BUY")
        ):
            exit_price = price
            if position.side == "LONG":
                pnl = (exit_price - position.entry) * position.qty
                cash += position.qty * exit_price
            else:
                pnl = (position.entry - exit_price) * position.qty
                cash += position.qty * (2 * position.entry - exit_price)
            trades.append(Trade(day, "EXIT", position.qty, exit_price, pnl, "signal flip"))
            position = None
            state.open_positions -= 1

        # Enter new position if flat and agent wants action.
        if not position and action in ("BUY", "SELL") and not state.halted:
            trader = decision["trader"]
            stop_pct = trader.get("stop_pct") or 2.0 * (atr_pct or 2)
            stop_price = (
                price * (1 - stop_pct / 100) if action == "BUY"
                else price * (1 + stop_pct / 100)
            )
            rd = risk.check_entry(
                state=state,
                side=action,
                price=price,
                stop_price=stop_price,
                equity=equity,
                regime=regime,
                atr_pct=atr_pct,
            )
            if not rd.approved:
                blocks += 1
                if verbose:
                    print(f"  [{day}] RISK BLOCK {action}: {rd.reason}")
            else:
                notional = equity * rd.size_pct / 100
                qty = notional / price
                if action == "BUY":
                    cost = qty * price
                    if cost <= cash:
                        cash -= cost
                        position = Position("LONG", qty, price, stop_price, day)
                        state.open_positions += 1
                        trades.append(Trade(day, "BUY", qty, price, 0.0,
                                            f"{regime} | {trader['rationale']}"))
                else:  # SELL (short) — margin = notional reserved from cash
                    if notional <= cash:
                        cash -= notional  # reserve margin
                        position = Position("SHORT", qty, price, stop_price, day)
                        state.open_positions += 1
                        trades.append(Trade(day, "SELL", qty, price, 0.0,
                                            f"{regime} | {trader['rationale']}"))

    # Liquidate at end.
    if position:
        last = bars[-1].close
        if position.side == "LONG":
            pnl = (last - position.entry) * position.qty
            cash += position.qty * last
        else:
            pnl = (position.entry - last) * position.qty
            cash += position.qty * (2 * position.entry - last)  # release margin + pnl
        trades.append(Trade(bars[-1].date, "EXIT", position.qty, last, pnl, "end-of-backtest"))
        position = None

    closed = [t for t in trades if t.side == "EXIT"]
    wins = sum(1 for t in closed if t.pnl > 0)
    final_equity = cash
    return BacktestResult(
        ticker=ticker,
        final_equity=round(final_equity, 2),
        start_equity=start_equity,
        total_return_pct=round((final_equity / start_equity - 1) * 100, 2),
        max_drawdown_pct=round(max_dd, 2),
        num_trades=len(closed),
        wins=wins,
        win_rate_pct=round(wins / len(closed) * 100, 1) if closed else 0.0,
        trades=trades,
        equity_curve=equity_curve,
        blocks=blocks,
    )
