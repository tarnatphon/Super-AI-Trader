"""Event-driven backtesting engine.

Runs the trading firm bar-by-bar, but the RiskManager has veto power over every
order. Positions use ATR-based stops; equity is marked to market each bar; a
daily-loss kill switch can halt trading. Long/short, long-only configurable, no
leverage (notional capped by equity).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..data.market import Bar, get_series
from ..data.indicators import precompute, snapshot_pre
from ..data.orderflow import precompute_flow
from ..agents.trading_firm import TradingFirm
from ..risk.manager import RiskManager, RiskConfig, RiskState


@dataclass
class Position:
    side: str               # "LONG" | "SHORT"
    qty: float
    entry: float
    stop: float
    target: float           # take-profit price
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
    total_costs: float = 0.0
    model_metrics: dict | None = None
    pressure: dict | None = None
    perf: dict | None = None

    def summary(self) -> str:
        s = (
            f"--- {self.ticker} backtest ---\n"
            f"  Start equity : {self.start_equity:,.2f}\n"
            f"  Final equity : {self.final_equity:,.2f}\n"
            f"  Total return : {self.total_return_pct:+.2f}%\n"
            f"  Max drawdown : {self.max_drawdown_pct:.2f}%\n"
            f"  Trades       : {self.num_trades} (win rate {self.win_rate_pct:.1f}%)\n"
            f"  Risk blocks  : {self.blocks}\n"
            f"  Trading costs: {self.total_costs:,.2f}\n"
        )
        if self.model_metrics:
            m = self.model_metrics
            s += (f"  Learned model (out-of-sample): acc {m['accuracy']} "
                  f"(base {m['base_up_rate']}), confident-buy hit {m['confident_buy_hit_rate']} "
                  f"on {m['confident_buy_n']} calls, confident-sell hit {m['confident_sell_hit_rate']} "
                  f"on {m['confident_sell_n']} calls\n")
        if self.pressure:
            p = self.pressure
            s += (f"  Order flow   : {p['buy_pct']:.0f}% bars net buying / "
                  f"{p['sell_pct']:.0f}% net selling\n")
        if self.perf:
            m = self.perf
            s += (
                f"  STEADINESS    : {m['profitable_months_pct']:.0f}% profitable months, "
                f"avg {m['avg_monthly_pct']:+.2f}%/mo "
                f"(best {m['best_month_pct']:+.2f}, worst {m['worst_month_pct']:+.2f})\n"
                f"  Risk-adjusted : Sharpe {m['monthly_sharpe']}, "
                f"Sortino {m['monthly_sortino']}, profit factor {m['profit_factor']}\n"
                f"  Target band   : avg/month in {m['target_band'][0]:.0f}-{m['target_band'][1]:.0f}% "
                f"-> {'YES ✅' if m['in_target_band'] else 'no'}\n"
            )
        return s


def run_backtest(
    ticker: str = "DEMO",
    days: int = 900,
    real: bool = False,
    start_equity: float = 100_000,
    risk_config: RiskConfig | None = None,
    profile: str = "steady",
    use_llm: bool = False,
    use_orderflow: bool = True,
    use_learned: bool = True,
    learned_model: dict | None = None,
    cost_per_side_pct: float = 0.1,
    horizon: int = 5,
    train_fraction: float = 0.6,
    overrides: dict | None = None,
    verbose: bool = False,
) -> BacktestResult:
    bars = get_series(ticker, days=days, real=real)

    # Precompute indicators + order flow once (O(n)) so the per-bar loop is fast.
    pre = precompute(bars)
    flow = precompute_flow(bars)

    # --- Train the learned model on the FIRST portion; trade only the REST (OOS).
    model_metrics = None
    model = learned_model
    split_idx = int(len(bars) * train_fraction)
    if use_learned and model is None:
        from ..learning.dataset import build_dataset
        from ..learning.model import train_logistic, evaluate
        Xtr, ytr, _ = build_dataset(bars[:split_idx], horizon=horizon)
        if len(Xtr) > 50:
            model = train_logistic(Xtr, ytr)
            # Evaluate out-of-sample on the test window labels.
            Xte, yte, _ = build_dataset(bars[split_idx:], horizon=horizon)
            if Xte:
                model_metrics = evaluate(model, Xte, yte)

    # Risk profile: steady (default) vs aggressive.
    if risk_config is None:
        risk_config = RiskConfig.steady() if profile == "steady" else (
            RiskConfig.aggressive() if profile == "aggressive" else RiskConfig()
        )
    # Apply manual percentage overrides on top of the profile.
    if overrides:
        for k, v in overrides.items():
            if v is not None and hasattr(risk_config, k):
                setattr(risk_config, k, v)
    tp_r = risk_config.take_profit_r_multiple
    tp_pct = risk_config.take_profit_pct

    firm = TradingFirm(use_llm=use_llm, use_orderflow=use_orderflow,
                       learned_model=model if use_learned else None)
    risk = RiskManager(risk_config)
    state = RiskState()

    cash = start_equity
    position: Position | None = None
    trades: list[Trade] = []
    equity_curve: list[tuple[str, float]] = []
    peak = start_equity
    max_dd = 0.0
    blocks = 0
    total_costs = 0.0
    buy_bars = sell_bars = 0
    current_day = ""

    # Only trade the out-of-sample window so results are honest.
    start_i = max(split_idx, 210)

    def apply_cost(notional: float) -> float:
        c = notional * cost_per_side_pct / 100
        return c

    for i in range(start_i, len(bars)):
        bar = bars[i]
        day = bar.date
        if day != current_day:
            current_day = day
            state.new_day(day, cash)

        price = bar.close

        equity = cash
        if position:
            if position.side == "LONG":
                equity = cash + position.qty * price
            else:
                equity = cash + position.qty * (2 * position.entry - price)

        equity_curve.append((day, round(equity, 2)))
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak * 100)
        risk.check_day(state, equity)

        # Manage open position: stop-out then take-profit (check stop first —
        # conservative, since within one bar both could trade).
        if position:
            hit_stop = (
                (position.side == "LONG" and bar.low <= position.stop)
                or (position.side == "SHORT" and bar.high >= position.stop)
            )
            hit_target = (
                (position.side == "LONG" and bar.high >= position.target)
                or (position.side == "SHORT" and bar.low <= position.target)
            )
            exit_reason = None
            exit_price = None
            if hit_stop:
                exit_reason, exit_price = "stop-out", position.stop
            elif hit_target:
                exit_reason, exit_price = "take-profit", position.target
            if exit_reason:
                notional = position.qty * exit_price
                fee = apply_cost(notional)
                cash -= fee
                total_costs += fee
                if position.side == "LONG":
                    pnl = (exit_price - position.entry) * position.qty - fee
                    cash += position.qty * exit_price
                else:
                    pnl = (position.entry - exit_price) * position.qty - fee
                    cash += position.qty * (2 * position.entry - exit_price)
                trades.append(Trade(day, "EXIT", position.qty, exit_price, pnl, exit_reason))
                position = None
                state.open_positions -= 1

        # Ask the firm (now with the tape + order flow + learned model).
        snap = snapshot_pre(pre, bars, i)
        decision = firm.analyze(snap, bars=bars, idx=i, pre=pre, flow=flow)
        raw_action = decision["action"]
        conviction = decision["conviction"]
        regime = decision["regime"]
        atr_pct = snap.get("atr14_pct")

        # Track aggregate buying/selling pressure over the test window.
        if decision.get("order_flow"):
            if decision["order_flow"]["ofi"] > 0.12:
                buy_bars += 1
            elif decision["order_flow"]["ofi"] < -0.12:
                sell_bars += 1

        ENTRY_MIN = 55
        FLIP_MIN = 70
        action = raw_action if conviction >= ENTRY_MIN else "HOLD"
        if position and (
            (position.side == "LONG" and action == "SELL")
            or (position.side == "SHORT" and action == "BUY")
        ) and conviction < FLIP_MIN:
            action = "HOLD"

        # Flip on strong opposite signal.
        if position and (
            (position.side == "LONG" and action == "SELL")
            or (position.side == "SHORT" and action == "BUY")
        ):
            exit_price = price
            notional = position.qty * exit_price
            fee = apply_cost(notional)
            cash -= fee
            total_costs += fee
            if position.side == "LONG":
                pnl = (exit_price - position.entry) * position.qty - fee
                cash += position.qty * exit_price
            else:
                pnl = (position.entry - exit_price) * position.qty - fee
                cash += position.qty * (2 * position.entry - exit_price)
            trades.append(Trade(day, "EXIT", position.qty, exit_price, pnl, "signal flip"))
            position = None
            state.open_positions -= 1

        # Enter.
        if not position and action in ("BUY", "SELL") and not state.halted:
            trader = decision["trader"]
            levels = decision.get("levels") or {}
            stop_pct = trader.get("stop_pct") or 2.0 * (atr_pct or 2)
            stop_price = (
                price * (1 - stop_pct / 100) if action == "BUY"
                else price * (1 + stop_pct / 100)
            )
            if action == "BUY" and levels.get("stop_below"):
                stop_price = min(stop_price, levels["stop_below"])
            if action == "SELL" and levels.get("stop_above"):
                stop_price = max(stop_price, levels["stop_above"])
            # Take-profit: fixed % if set, otherwise tp_r x risk distance.
            if tp_pct:
                target_price = (
                    price * (1 + tp_pct / 100) if action == "BUY"
                    else price * (1 - tp_pct / 100)
                )
            else:
                risk_dist = abs(price - stop_price)
                target_price = (
                    price + tp_r * risk_dist if action == "BUY"
                    else price - tp_r * risk_dist
                )

            rd = risk.check_entry(
                state=state, side=action, price=price, stop_price=stop_price,
                equity=equity, regime=regime, atr_pct=atr_pct,
            )
            if not rd.approved:
                blocks += 1
                if verbose:
                    print(f"  [{day}] RISK BLOCK {action}: {rd.reason}")
            else:
                notional = equity * rd.size_pct / 100
                fee = apply_cost(notional)
                cash -= fee
                total_costs += fee
                qty = notional / price
                zone = ""
                if levels:
                    zone = (f" @support {levels['support']}" if levels.get("at_support")
                            else f" @resistance {levels['resistance']}" if levels.get("at_resistance")
                            else "")
                if action == "BUY" and notional + fee <= cash:
                    cash -= notional
                    position = Position("LONG", qty, price, stop_price, target_price, day)
                    state.open_positions += 1
                    trades.append(Trade(day, "BUY", qty, price, 0.0,
                                        f"{regime}{zone} | T {target_price:.2f} | {trader['rationale']}"))
                elif action == "SELL" and notional + fee <= cash:
                    cash -= notional
                    position = Position("SHORT", qty, price, stop_price, target_price, day)
                    state.open_positions += 1
                    trades.append(Trade(day, "SELL", qty, price, 0.0,
                                        f"{regime}{zone} | T {target_price:.2f} | {trader['rationale']}"))

    if position:
        last = bars[-1].close
        notional = position.qty * last
        fee = apply_cost(notional)
        total_costs += fee
        if position.side == "LONG":
            pnl = (last - position.entry) * position.qty - fee
            cash += position.qty * last - fee
        else:
            pnl = (position.entry - last) * position.qty - fee
            cash += position.qty * (2 * position.entry - last) - fee
        trades.append(Trade(bars[-1].date, "EXIT", position.qty, last, pnl, "end-of-backtest"))
        position = None

    closed = [t for t in trades if t.side == "EXIT"]
    wins = sum(1 for t in closed if t.pnl > 0)
    final_equity = cash
    pressure_total = buy_bars + sell_bars

    from .metrics import compute_metrics
    perf = compute_metrics(
        equity_curve, trades, start_equity,
        target_low=(overrides or {}).get("target_low", 2.0) or 2.0,
        target_high=(overrides or {}).get("target_high", 5.0) or 5.0,
    )

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
        total_costs=round(total_costs, 2),
        model_metrics=model_metrics,
        perf=perf,
        pressure={
            "buy_pct": round(100 * buy_bars / pressure_total, 1) if pressure_total else 0,
            "sell_pct": round(100 * sell_bars / pressure_total, 1) if pressure_total else 0,
        },
    )
