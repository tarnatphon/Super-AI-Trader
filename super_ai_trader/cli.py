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
from .data.indicators import snapshot
from .agents.trading_firm import TradingFirm
from .risk.manager import RiskConfig
from .engine.backtest import run_backtest


def cmd_analyze(args) -> None:
    bars = get_series(args.ticker, days=max(args.days, 260), real=args.real)
    snap = snapshot(bars, len(bars) - 1)
    firm = TradingFirm(use_llm=args.llm)
    decision = firm.analyze(snap, news=args.news or None)
    print(json.dumps(decision, indent=2, default=str))


def cmd_backtest(args) -> None:
    cfg = RiskConfig(allow_shorts=not args.long_only)
    tickers = [t.strip() for t in args.ticker.split(",") if t.strip()]
    print(f"\nSuper-AI-Trader v0.1  |  data={'real(yfinance)' if args.real else 'synthetic'}  "
          f"|  LLM={'on' if args.llm else 'off'}\n")
    for ticker in tickers:
        res = run_backtest(
            ticker=ticker,
            days=args.days,
            real=args.real,
            start_equity=args.equity,
            risk_config=cfg,
            use_llm=args.llm,
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
    common.add_argument("--days", type=int, default=750)
    common.add_argument("--real", action="store_true", help="use real Yahoo Finance data (needs pip install yfinance)")
    common.add_argument("--llm", action="store_true", help="enable LLM agents (needs LLM_API_KEY / OPENAI_API_KEY)")

    p_bt = sub.add_parser("backtest", parents=[common], help="run a backtest")
    p_bt.add_argument("--equity", type=float, default=100_000)
    p_bt.add_argument("--long-only", action="store_true")
    p_bt.add_argument("--trades", action="store_true", help="print recent trades")
    p_bt.add_argument("--verbose", action="store_true")
    p_bt.set_defaults(func=cmd_backtest)

    p_an = sub.add_parser("analyze", parents=[common], help="run one AI-firm analysis and print the decision JSON")
    p_an.add_argument("--news", nargs="*", help="optional headlines for the sentiment agent")
    p_an.set_defaults(func=cmd_analyze)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
