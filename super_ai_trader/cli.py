"""Command-line interface for Super-AI-Trader.

Examples:
    python -m super_ai_trader backtest --ticker DEMO
    python -m super_ai_trader backtest --ticker AAPL --real --days 750
    python -m super_ai_trader analyze --ticker DEMO
    LLM_API_KEY=sk-... python -m super_ai_trader analyze --ticker DEMO --llm
"""
from __future__ import annotations

import argparse
import json

from .data.market import get_series
from .data.indicators import precompute, snapshot_pre
from .data.orderflow import precompute_flow
from .agents.trading_firm import TradingFirm
from .risk.manager import RiskConfig
from .engine.backtest import run_backtest


def cmd_analyze(args) -> None:
    bars = get_series(args.ticker, days=max(args.days, 260), real=args.real)
    pre = precompute(bars)
    flow = precompute_flow(bars)
    i = len(bars) - 1
    snap = snapshot_pre(pre, bars, i)
    firm = TradingFirm(use_llm=args.llm)
    decision = firm.analyze(snap, bars=bars, idx=i, pre=pre, flow=flow,
                            news=args.news or None)
    fs = decision.get("order_flow", {})
    lv = decision.get("levels", {})
    print("=" * 64)
    print(f"  {args.ticker}  |  price {snap['price']}  |  "
          f"decision: {decision['action']} ({decision['conviction']:.0f}) "
          f"regime={decision['regime']}")
    print("=" * 64)
    print("  REAL BUYING vs SELLING PRESSURE (order flow):")
    print(f"    pressure           : {fs.get('pressure', 'n/a')}")
    print(f"    order-flow imbal.  : {fs.get('ofi')}  (-1 all sellers .. +1 all buyers)")
    print(f"    buy-volume ratio   : {fs.get('buy_vol_ratio')}")
    print(f"    cum-delta divergence: {fs.get('cum_delta_divergence')}")
    print("  WHERE TO BUY / SELL (price zones):")
    print(f"    SUPPORT / buy zone : {lv.get('support')}  (at zone: {lv.get('at_support')})")
    print(f"    RESIST / sell zone : {lv.get('resistance')}  (at zone: {lv.get('at_resistance')})")
    print(f"    stop-below / above : {lv.get('stop_below')} / {lv.get('stop_above')}")
    print("  AGENT VOTES:")
    for a in decision["analysts"]:
        print(f"    {a['agent']:<12} {a['action']:<5} {a['conviction']:>4.0f}  {a['rationale']}")
    print(f"    bull: {decision['bull']['action']} {decision['bull']['conviction']:.0f} | "
          f"bear: {decision['bear']['action']} {decision['bear']['conviction']:.0f}")
    if args.json:
        print("\n" + json.dumps(decision, indent=2, default=str))


def cmd_ask(args) -> None:
    """AI Command Center — one plain-language command for every function."""
    from .ai.commands import run_command
    import json as _json
    text = " ".join(args.request)
    out = run_command(text)
    print("\n" + out["reply"] + "\n")
    if args.json:
        print(_json.dumps(out["data"], indent=2, default=str)[:4000])


def cmd_talk(args) -> None:
    from .ai.assistant import interpret, to_grid_config, explain
    from .grid.engine import simulate_on_bars
    from .data.market import get_series
    text = " ".join(args.request)
    parsed = interpret(text)
    print("\n🤖 " + explain(parsed) + "\n")
    # Use live recent candles if ccxt + internet work, else synthetic bars.
    bars = None
    try:
        from .exchange.connector import ExchangeConnector
        conn = ExchangeConnector(parsed["exchange"], paper=True)
        bars = conn.ohlcv(parsed["symbol"], timeframe="1h", limit=600)
        print(f"Loaded {len(bars)} live {parsed['exchange']} candles for {parsed['symbol']}.")
    except Exception as e:
        print(f"(Live exchange feed unavailable: {e} — using practice data.)")
    bars = bars or get_series(parsed["coin"], days=600)
    cfg = to_grid_config(parsed, bars[0].close)
    res = simulate_on_bars(cfg, bars)
    print(res.summary())


def cmd_paper(args) -> None:
    from .exchange.connector import ExchangeConnector
    from .exchange.grid_runner import LiveGridRunner
    from .ai.assistant import interpret, to_grid_config
    ex = args.exchange
    symbol = args.symbol
    cfg = None
    if args.request:
        parsed = interpret(" ".join(args.request))
        ex = parsed["exchange"]
        symbol = parsed["symbol"]
        conn0 = ExchangeConnector(ex, paper=True)
        try:
            ref = conn0.price(symbol)
        except Exception as e:
            print(f"Cannot reach {ex}: {e}")
            return
        cfg = to_grid_config(parsed, ref)
    else:
        from .grid.engine import GridConfig
        conn0 = ExchangeConnector(ex, paper=True)
        try:
            ref = conn0.price(symbol)
        except Exception as e:
            print(f"Cannot reach {ex}: {e}")
            return
        cfg = GridConfig(symbol=symbol, range_pct=args.range_pct,
                         grids=args.grids, mode="geometric",
                         investment=args.investment, fee_pct=0.1,
                         stop_loss_price=ref * (1 - args.range_pct * 2 / 100),
                         take_profit_price=ref * (1 + args.range_pct * 2 / 100))
    conn = ExchangeConnector(ex, paper=True, paper_usdt=cfg.investment)
    runner = LiveGridRunner(conn, cfg)
    print(f"\nPAPER grid on {ex} {cfg.symbol} (practice money, live prices).\n")
    runner.run(poll_seconds=args.poll, max_loops=args.loops)


def cmd_grid(args) -> None:
    from .grid.engine import GridConfig, simulate_on_bars
    from .data.market import get_series
    bars = get_series(args.ticker, days=args.days, real=args.real)
    ref = bars[0].close

    # Auto range from reference price when bounds not given.
    cfg = GridConfig(
        symbol=f"{args.ticker}/USDT",
        lower=args.lower or ref * (1 - args.range_pct / 100),
        upper=args.upper or ref * (1 + args.range_pct / 100),
        grids=args.grids,
        mode=args.mode,
        investment=args.investment,
        fee_pct=args.fee,
        range_pct=args.range_pct,
        stop_loss_price=args.stop_loss,
        take_profit_price=args.take_profit,
    )
    print(f"\nGRID  {cfg.symbol}  exchange={args.exchange}  mode={cfg.mode}  grids={cfg.grids}")
    print(f"  range {cfg.lower:,.2f} – {cfg.upper:,.2f}  "
          f"(ref {ref:,.2f}, ±{args.range_pct}%)  investment {cfg.investment:,.0f}  fee {cfg.fee_pct}%/side")
    res = simulate_on_bars(cfg, bars)
    print(res.summary())


def cmd_learn(args) -> None:
    from .learning.train import train_for_ticker
    tickers = [t.strip() for t in args.ticker.split(",") if t.strip()]
    for ticker in tickers:
        _, metrics, live = train_for_ticker(
            ticker, days=args.days, real=args.real, horizon=args.horizon,
            save_path=args.save,
        )
        print("=" * 64)
        print(f"  LEARNED MODEL — {ticker}  (predict move {args.horizon} bars ahead)")
        print("=" * 64)
        print(f"  Trained on {metrics.get('train_samples')} bars, "
              f"validated out-of-sample on {metrics.get('test_samples')} bars")
        print(f"  OOS accuracy: {metrics.get('accuracy')}  (base up-rate {metrics.get('base_up_rate')})")
        print(f"  Confident BUY hit rate: {metrics.get('confident_buy_hit_rate')} "
              f"across {metrics.get('confident_buy_n')} calls")
        print(f"  Confident SELL hit rate: {metrics.get('confident_sell_hit_rate')} "
              f"across {metrics.get('confident_sell_n')} calls")
        print(f"  Top features the model learned from:")
        for name, w in metrics.get("top_features", []):
            print(f"    {name:<16} weight {w:+.3f}")
        print("  LIVE READ:")
        print(f"    pressure              : {live['pressure']} (OFI {live['order_flow_imbalance']})")
        print(f"    SUPPORT / buy zone    : {live['support_buy_zone']}  (at: {live['at_support']})")
        print(f"    RESISTANCE / sell zone: {live['resistance_sell_zone']}  (at: {live['at_resistance']})")
        print(f"    stop-below/above      : {live['stop_below']} / {live['stop_above']}")
        print(f"    model P(up)           : {live['model_prob_up']}  ->  {live['model_call']}")
        if args.save:
            print(f"  model saved to {args.save}")
        print()


def cmd_backtest(args) -> None:
    cfg = RiskConfig(allow_shorts=False) if args.long_only else None
    tickers = [t.strip() for t in args.ticker.split(",") if t.strip()]

    # Manual percentage overrides take precedence over the profile.
    overrides = {
        "risk_per_trade_pct": args.risk_per_trade,
        "max_position_pct": args.max_position,
        "daily_loss_limit_pct": args.daily_loss,
        "take_profit_r_multiple": args.take_profit_r,
        "take_profit_pct": args.take_profit_pct,
        "target_low": args.target_low,
        "target_high": args.target_high,
    }
    overrides = {k: v for k, v in overrides.items() if v is not None}

    tp_desc = (f"TP {args.take_profit_pct}%" if args.take_profit_pct is not None
               else f"TP {args.take_profit_r}R" if args.take_profit_r is not None else "TP 1.5R")
    print(f"\nSuper-AI-Trader  |  profile={args.profile}  |  "
          f"data={'real(yfinance)' if args.real else 'synthetic'}  "
          f"|  LLM={'on' if args.llm else 'off'}  |  order-flow={'on' if not args.no_orderflow else 'off'}  "
          f"|  learned={'on' if not args.no_learned else 'off'}  |  cost={args.cost}%/side\n"
          f"  Manual: risk/trade={args.risk_per_trade if args.risk_per_trade else 'profile'}%  "
          f"maxPos={args.max_position if args.max_position else 'profile'}%  "
          f"dailyStop={args.daily_loss if args.daily_loss else 'profile'}%  {tp_desc}  "
          f"target={args.target_low if args.target_low else 2}-{args.target_high if args.target_high else 5}%/mo\n")
    for ticker in tickers:
        res = run_backtest(
            ticker=ticker,
            days=args.days,
            real=args.real,
            start_equity=args.equity,
            risk_config=cfg,
            profile=args.profile,
            use_llm=args.llm,
            use_orderflow=not args.no_orderflow,
            use_learned=not args.no_learned,
            cost_per_side_pct=args.cost,
            horizon=args.horizon,
            overrides=overrides,
            verbose=args.verbose,
        )
        print(res.summary())
        if args.trades:
            for t in res.trades[-12:]:
                pnl = f"{t.pnl:+,.0f}" if t.side == "EXIT" else "-"
                print(f"   {t.date}  {t.side:4s}  qty={t.qty:8.2f}  px={t.price:8.2f}  pnl={pnl}  {t.reason}")
            print()
        if args.trades:
            for t in res.trades[-15:]:
                tag = t.side
                pnl = f"{t.pnl:+,.0f}" if t.side == "EXIT" else "-"
                print(f"   {t.date}  {tag:4s}  qty={t.qty:8.2f}  px={t.price:8.2f}  pnl={pnl}  {t.reason}")
            print()


def main() -> None:
    parser = argparse.ArgumentParser(prog="super-ai-trader", description="Multi-agent AI trading firm")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--ticker", default="DEMO", help="ticker(s), comma separated (e.g. DEMO or AAPL,MSFT)")
    common.add_argument("--days", type=int, default=900)
    common.add_argument("--real", action="store_true", help="use real Yahoo Finance data (needs pip install yfinance)")
    common.add_argument("--llm", action="store_true", help="enable LLM agents (needs LLM_API_KEY / OPENAI_API_KEY)")

    p_bt = sub.add_parser("backtest", parents=[common], help="run an out-of-sample backtest")
    p_bt.add_argument("--profile", choices=["steady", "aggressive", "default"], default="steady",
                      help="steady targets consistent 2-5%/mo with tight drawdowns (default)")
    p_bt.add_argument("--equity", type=float, default=100_000)
    p_bt.add_argument("--long-only", action="store_true")
    p_bt.add_argument("--trades", action="store_true", help="print recent trades")
    p_bt.add_argument("--verbose", action="store_true")
    p_bt.add_argument("--no-orderflow", action="store_true", help="disable the order-flow agent")
    p_bt.add_argument("--no-learned", action="store_true", help="disable the learned ML agent")
    p_bt.add_argument("--cost", type=float, default=0.1, help="trading cost %% per side (default 0.1)")
    p_bt.add_argument("--horizon", type=int, default=5, help="bars ahead the model predicts")

    # Manual percentage overrides.
    p_bt.add_argument("--risk-per-trade", type=float, default=None,
                      help="%% of equity risked to the stop (steady default 0.5)")
    p_bt.add_argument("--max-position", type=float, default=None,
                      help="max notional of equity in one position %% (steady default 15)")
    p_bt.add_argument("--daily-loss", type=float, default=None,
                      help="daily loss kill-switch %% (steady default 1.5)")
    p_bt.add_argument("--take-profit-r", type=float, default=None,
                      help="take-profit as reward:risk multiple (steady default 1.5)")
    p_bt.add_argument("--take-profit-pct", type=float, default=None,
                      help="fixed take-profit %% (overrides --take-profit-r)")
    p_bt.add_argument("--target-low", type=float, default=None,
                      help="lower monthly target %% (default 2)")
    p_bt.add_argument("--target-high", type=float, default=None,
                      help="upper monthly target %% (default 5)")
    p_bt.set_defaults(func=cmd_backtest)

    p_an = sub.add_parser("analyze", parents=[common], help="show buying/selling pressure, buy/sell zones, and AI-firm decision")
    p_an.add_argument("--news", nargs="*", help="optional headlines for the sentiment agent")
    p_an.add_argument("--json", action="store_true", help="also print full decision JSON")
    p_an.set_defaults(func=cmd_analyze)

    p_le = sub.add_parser("learn", parents=[common], help="train the ML model, validate out-of-sample, show live read")
    p_le.add_argument("--horizon", type=int, default=5, help="bars ahead to predict")
    p_le.add_argument("--save", default=None, help="optional path to save the trained model JSON")
    p_le.set_defaults(func=cmd_learn)

    p_g = sub.add_parser("grid", parents=[common], help="simulate/run a spot grid bot (binance or gate.io)")
    p_g.add_argument("--exchange", choices=["binance", "gateio"], default="binance",
                     help="venue for fee/live profile (grid runs the same; binance default)")
    p_g.add_argument("--lower", type=float, default=None, help="grid bottom price")
    p_g.add_argument("--upper", type=float, default=None, help="grid top price")
    p_g.add_argument("--range-pct", type=float, default=10.0, help="auto range ±%% from price")
    p_g.add_argument("--grids", type=int, default=20, help="number of grid lines")
    p_g.add_argument("--mode", choices=["arithmetic", "geometric"], default="geometric")
    p_g.add_argument("--investment", type=float, default=10_000.0)
    p_g.add_argument("--fee", type=float, default=0.1, help="maker fee %% per side")
    p_g.add_argument("--stop-loss", type=float, default=None)
    p_g.add_argument("--take-profit", type=float, default=None)
    p_g.set_defaults(func=cmd_grid)

    p_w = sub.add_parser("web", help="launch the simple, secure local dashboard")
    p_w.add_argument("--port", type=int, default=8787)
    p_w.add_argument("--host", default="127.0.0.1", help="localhost only by default")
    def _web(args):
        from .web.server import run
        run(host=args.host, port=args.port)
    p_w.set_defaults(func=_web)

    p_p = sub.add_parser("paper", help="paper-trade a live grid against real exchange prices (no orders sent)")
    p_p.add_argument("--exchange", choices=["binance", "gateio"], default="binance")
    p_p.add_argument("--symbol", default="BTC/USDT")
    p_p.add_argument("--range-pct", type=float, default=12)
    p_p.add_argument("--grids", type=int, default=25)
    p_p.add_argument("--investment", type=float, default=1000)
    p_p.add_argument("--poll", type=float, default=15, help="seconds between price polls")
    p_p.add_argument("--loops", type=int, default=None, help="stop after N polls (default: run)")
    p_p.add_argument("request", nargs="*", help="optional plain-language request instead of flags")
    p_p.set_defaults(func=cmd_paper)

    p_a = sub.add_parser("ask", help="AI Command Center — one plain-language command for every function")
    p_a.add_argument("request", nargs="+", help='e.g. "analyze Bitcoin" or "set up a safe grid 1000 USDT"')
    p_a.add_argument("--json", action="store_true")
    p_a.set_defaults(func=cmd_ask)

    p_t = sub.add_parser("talk", help="tell the local AI what you want in plain words")
    p_t.add_argument("request", nargs="+", help='e.g. "trade 1000 USDT on Bitcoin safe grid 12 percent"')
    p_t.set_defaults(func=cmd_talk)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
