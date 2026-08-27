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
    cfg = RiskConfig(allow_shorts=not args.long_only)
    tickers = [t.strip() for t in args.ticker.split(",") if t.strip()]
    print(f"\nSuper-AI-Trader  |  data={'real(yfinance)' if args.real else 'synthetic'}  "
          f"|  LLM={'on' if args.llm else 'off'}  |  order-flow={'on' if not args.no_orderflow else 'off'}  "
          f"|  learned={'on' if not args.no_learned else 'off'}  |  cost={args.cost}%/side\n")
    for ticker in tickers:
        res = run_backtest(
            ticker=ticker,
            days=args.days,
            real=args.real,
            start_equity=args.equity,
            risk_config=cfg,
            use_llm=args.llm,
            use_orderflow=not args.no_orderflow,
            use_learned=not args.no_learned,
            cost_per_side_pct=args.cost,
            horizon=args.horizon,
            verbose=args.verbose,
        )
        print(res.summary())
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
    p_bt.add_argument("--equity", type=float, default=100_000)
    p_bt.add_argument("--long-only", action="store_true")
    p_bt.add_argument("--trades", action="store_true", help="print recent trades")
    p_bt.add_argument("--verbose", action="store_true")
    p_bt.add_argument("--no-orderflow", action="store_true", help="disable the order-flow agent")
    p_bt.add_argument("--no-learned", action="store_true", help="disable the learned ML agent")
    p_bt.add_argument("--cost", type=float, default=0.1, help="trading cost %% per side (default 0.1)")
    p_bt.add_argument("--horizon", type=int, default=5, help="bars ahead the model predicts")
    p_bt.set_defaults(func=cmd_backtest)

    p_an = sub.add_parser("analyze", parents=[common], help="show buying/selling pressure, buy/sell zones, and AI-firm decision")
    p_an.add_argument("--news", nargs="*", help="optional headlines for the sentiment agent")
    p_an.add_argument("--json", action="store_true", help="also print full decision JSON")
    p_an.set_defaults(func=cmd_analyze)

    p_le = sub.add_parser("learn", parents=[common], help="train the ML model, validate out-of-sample, show live read")
    p_le.add_argument("--horizon", type=int, default=5, help="bars ahead to predict")
    p_le.add_argument("--save", default=None, help="optional path to save the trained model JSON")
    p_le.set_defaults(func=cmd_learn)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
