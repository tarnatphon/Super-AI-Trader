"""AI Command Center — one place where the AI understands what you want and the
bot carries it out across EVERY app function.

You talk in plain words. The AI (local Ollama if present, else an offline intent
parser) decides which function to run, and the "bot" executes it safely:

  grid / simulate  -> backtest a grid on a coin
  analyze / look   -> full AI-firm read (buying/selling pressure, zones, votes)
  backtest / test  -> run the directional strategy backtest
  learn / train    -> train the learned model, report out-of-sample accuracy
  paper / practice -> (explain) live paper grid; needs `ccxt` + internet
  risk / stop / target / set ... percent -> tune the safety percentages
  safety / security / connect -> the protection checklist
  help             -> what you can ask

The bot always answers in plain language and includes the key numbers.
"""
from __future__ import annotations

from .assistant import offline_parse, _find_coin


INTENTS = {
    "grid": ["grid", "simulate grid", "set up a grid", "grid bot", "buy low sell high"],
    "analyze": ["analyze", "look at", "what about", "should i buy", "pressure", "buying", "selling", "zone"],
    "backtest": ["backtest", "test the strategy", "test strategy", "how would it do", "run a test"],
    "learn": ["learn", "train", "teach", "model", "predict"],
    "paper": ["paper", "practice trade", "live practice", "demo trade", "run it live"],
    "risk": ["risk", "stop loss", "daily loss", "take profit", "set ", "percent", "%", "target"],
    "safety": ["safety", "security", "protect", "hack", "connect", "api key", "vault", "shield"],
    "help": ["help", "what can you do", "how do i", "commands"],
}


def classify(text: str) -> str:
    low = text.lower()
    if any(k in low for k in ("optimize", "best trailing", "best position", "best settings",
                              "find the best", "tune", "fine-tune", "fine tune")):
        return "optimize"
    # Order matters: check specific intents first.
    if any(k in low for k in ("paper", "practice trade", "demo trade")):
        return "paper"
    if any(k in low for k in ("read the chart", "read chart", "read the graph", "indicators",
                              "ema", "macd", "boll", "rsi", "sar", "supertrend", "super trend")):
        return "chart"
    if any(k in low for k in ("live", "order book", "orderbook", "buyers", "sellers",
                              "human", "right now", "depth", "who is buying", "who's buying",
                              "live behavior")):
        return "behavior"
    # Grid / strategy intents before general safety, so "safe grid" -> grid.
    if any(k in low for k in ("grid", "buy low", "sell high")):
        return "grid"
    if any(k in low for k in ("learn", "train", "teach the", "predict the next")):
        return "learn"
    if any(k in low for k in ("backtest", "test the strategy", "test strategy", "how would it do")):
        return "backtest"
    if any(k in low for k in ("safety", "security", "protect", "hack", "connect", "api key",
                              "vault", "shield", "money safe", "is it safe", "safe?", "my money")):
        return "safety"
    if any(k in low for k in ("analyze", "look at", "what about", "should i buy", "pressure", "zone")):
        return "analyze"
    if any(k in low for k in ("risk", "stop loss", "daily loss", "take profit", "target", "set ")):
        return "risk"
    return "help"


def _bot(line: str) -> str:
    return f"🤖 {line}"


def _grid_dict(res) -> dict:
    return {
        "final_equity": res.final_equity, "grid_profit": res.grid_profit,
        "unrealized": res.unrealized_pnl, "round_trips": res.filled_round_trips,
        "fees": res.fees_paid, "stopped": res.stopped,
        "start_price": res.start_price, "end_price": res.end_price,
    }


def run_command(text: str) -> dict:
    """Parse a plain-language instruction and execute the right app function.
    Returns {'intent', 'reply' (plain language), 'data' (structured)}.
    """
    intent = classify(text)
    coin = _find_coin(text)
    parsed = offline_parse(text)  # reuses number/coin extraction

    if intent == "grid":
        from ..grid.engine import GridConfig, simulate_on_bars
        from ..data.market import get_series
        bars = get_series(coin, days=600)
        cfg = GridConfig(
            symbol=f"{coin}/USDT",
            lower=bars[0].close * (1 - parsed["range_pct"] / 100),
            upper=bars[0].close * (1 + parsed["range_pct"] / 100),
            grids=parsed["grids"], mode=parsed["mode"],
            investment=parsed["investment"], fee_pct=0.1, range_pct=parsed["range_pct"],
            stop_loss_price=bars[0].close * (1 - parsed["range_pct"] * 2 / 100),
            take_profit_price=bars[0].close * (1 + parsed["range_pct"] * 2 / 100),
        )
        res = simulate_on_bars(cfg, bars)
        reply = _bot(
            f"I set up a {parsed['mode']} grid for {coin}: {parsed['grids']} steps over a "
            f"{parsed['range_pct']:.0f}% range, using {parsed['investment']:.0f} practice USDT. "
            f"In the test it collected {res.filled_round_trips} small wins, made "
            f"{res.grid_profit:+.2f} from the grid, and ended with {res.final_equity:.2f} "
            f"({(res.final_equity/parsed['investment']-1)*100:+.1f}%). "
            + ("The safety stop was triggered — that's the shield protecting the money."
               if res.stopped else "The safety stop was not needed in this test."))
        return {"intent": intent, "reply": reply, "data": {"result": _grid_dict(res)}}

    if intent == "chart":
        from ..ai.chart_reader import read_chart, explain_chart
        from ..data.market import get_series
        bars = get_series(coin, days=300)
        reading = read_chart(bars)
        detail = "\n".join("  • " + ln for ln in reading["lines"])
        reply = _bot(
            f"Here's how I read the {coin} chart, indicator by indicator:\n{detail}\n"
            f"Overall ({len(reading['indicators'])} indicators agree): score "
            f"{reading['score']:+d} → **{reading['verdict']}**. This is what MA, EMA, BOLL, "
            "SAR, AVL/VOLUME, SUPER(SUPERtrend), MACD and RSI are all saying together.")
        return {"intent": intent, "reply": reply, "data": {"reading": reading,
                "explain": explain_chart(reading)}}

    if intent == "behavior":
        from ..data.live_behavior import live_behavior
        ex = parsed["exchange"]
        beh = live_behavior(ex, f"{coin}/USDT")
        walls = ""
        ob = beh
        if beh.get("big_bid_wall"):
            walls += f" There's a big BUY wall around {beh['big_bid_wall'][0]} (real support)."
        if beh.get("big_ask_wall"):
            walls += f" A big SELL wall sits near {beh['big_ask_wall'][0]} (resistance)."
        spread = f", spread {beh['spread_pct']}%" if beh.get("spread_pct") is not None else ""
        reply = _bot(
            f"Watching LIVE human behavior on {coin} ({beh['source']}){spread}. "
            f"Right now {beh['pressure']} are in control — {round(beh['buy_ratio']*100)}% buying "
            f"vs {round(beh['sell_ratio']*100)}% selling, order-flow imbalance {beh['trade_flow_imbalance']:+}. "
            + (f"In the live order book, {round((beh.get('buyer_pressure_depth') or 0)*100)}% of resting "
               f"size is on BUY bids and {round((beh.get('seller_pressure_depth') or 0)*100)}% on SELL asks."
               if beh.get("order_book_bid_ask_imbalance") is not None else
               "(Using recent candles as the live feed/ccxt isn't connected; connect to see the real order book.)")
            + walls +
            " I learn this pressure over time and combine it with the chart reading before I suggest a trade.")
        return {"intent": intent, "reply": reply, "data": {"behavior": beh}}

    if intent == "analyze":
        from ..data.market import get_series
        from ..data.indicators import precompute, snapshot_pre
        from ..data.orderflow import precompute_flow
        from ..agents.trading_firm import TradingFirm
        bars = get_series(coin, days=600)
        pre = precompute(bars); flow = precompute_flow(bars); i = len(bars) - 1
        snap = snapshot_pre(pre, bars, i)
        d = TradingFirm(use_llm=False).analyze(snap, bars=bars, idx=i, pre=pre, flow=flow)
        of = d.get("order_flow", {}); lv = d.get("levels", {})
        votes = ", ".join(f"{a['agent']} {a['action']}" for a in d["analysts"])
        reply = _bot(
            f"Here's my read on {coin} at price {snap['price']}. The market pressure is "
            f"'{of.get('pressure','?')}' (buy/sell imbalance {of.get('ofi')}). "
            f"Good place to BUY (support) is around {lv.get('support')}; good place to SELL "
            f"(resistance) is around {lv.get('resistance')}. My overall call is "
            f"{d['action']} with confidence {d['conviction']:.0f}/100 in a '{d['regime']}' market. "
            f"Votes: {votes}. Remember — I advise, the safety shield decides the size.")
        return {"intent": intent, "reply": reply, "data": {"decision": d}}

    if intent == "backtest":
        from ..engine.backtest import run_backtest
        res = run_backtest(coin, days=900, use_llm=False)
        perf = res.perf or {}
        reply = _bot(
            f"I tested the full AI strategy on {coin}. Result: {res.total_return_pct:+.2f}% "
            f"with a max drawdown of {res.max_drawdown_pct:.2f}%. It made {res.num_trades} trades. "
            f"Steadiness: {perf.get('profitable_months_pct','?')}% profitable months, average "
            f"{perf.get('avg_monthly_pct','?')}% per month, profit factor {perf.get('profit_factor','?')}. "
            f"{'That lands in your 2-5% steady target — nice.' if perf.get('in_target_band') else 'Not yet in the 2-5% steady band; the shield keeps risk small while we improve.'}")
        return {"intent": intent, "reply": reply, "data": {"summary": res.summary()}}

    if intent == "optimize":
        from ..learning.trailing import optimize_trailing, explain_optimization
        opt = optimize_trailing(coin, days=900)
        reply = _bot(explain_optimization(opt))
        return {"intent": intent, "reply": reply, "data": {"best": opt["best"],
                "top5": opt["top5"], "confirmation": opt["confirmation"]}}

    if intent == "learn":
        from ..learning.train import train_for_ticker
        _, metrics, live = train_for_ticker(coin, days=900)
        reply = _bot(
            f"I studied {coin} and trained on the older data, then tested myself on data I "
            f"hadn't seen. My out-of-sample accuracy was {metrics.get('accuracy')} (a coin flip is "
            f"~0.5). Right now the live pressure is '{live['pressure']}', support (buy zone) "
            f"{live['support_buy_zone']}, resistance (sell zone) {live['resistance_sell_zone']}, "
            f"and my model says P(up) = {live['model_prob_up']} → {live['model_call']}. "
            "I'll keep learning as more real data comes in.")
        return {"intent": intent, "reply": reply, "data": {"metrics": metrics, "live": live}}

    if intent == "paper":
        reply = _bot(
            "To practice with REAL prices (no real orders), run this on your computer with "
            "internet:  pip install ccxt   then:  "
            f"python -m super_ai_trader paper \"{parsed['investment']:.0f} USDT {coin} safe grid\". "
            "The bot polls Binance/Gate.io live prices and simulates fills with practice money. "
            "When you're ready for real trading, connect a trade-only key (withdrawals OFF) from "
            "the Safety screen.")
        return {"intent": intent, "reply": reply, "data": {"parsed": parsed}}

    if intent == "risk":
        # Echo the tunable percentages the bot will use.
        rpt = parsed["range_pct"]
        reply = _bot(
            "You can tune my safety percentages any time. For example: "
            "risk per trade 0.5%, max position 15%, daily loss stop 1.5%, take-profit 1.5 "
            "reward-to-risk, monthly target 2–5%. Say things like 'set risk to 1 percent' or "
            "'use a 3 percent take profit' and I'll apply them to the backtest and the bot. "
            f"(Right now I've got a {rng_word(rpt)} range in mind for {coin}.)")
        return {"intent": intent, "reply": reply, "data": {"range_pct": rpt}}

    if intent == "safety":
        from ..security.vault import security_checklist
        checks = security_checklist()
        reply = _bot(
            "Your Safety Shield is ON. The rules I follow: "
            + " ".join(f"{i+1}) {c['title']}." for i, c in enumerate(checks))
            + " Keys are encrypted on your own computer, the app only talks to your machine "
            "(localhost), practice mode is default, and real trading needs a trade-only key "
            "with withdrawals turned OFF. Want me to walk through connecting Binance or Gate.io?")
        return {"intent": intent, "reply": reply, "data": {"checklist": checks}}

    # help
    reply = _bot(
        "I'm your AI trader — just tell me what you want in plain words. Try:\n"
        f"• \"Set up a safe grid for Bitcoin with 1,000 USDT\"\n"
        f"• \"Analyze Ethereum — should I buy?\"\n"
        f"• \"Backtest the strategy on {coin or 'BTC'}\"\n"
        "• \"Learn and predict Bitcoin\"\n"
        "• \"Read the chart\" or \"show me EMA MACD RSI on Ethereum\"\n"
        "• \"Who is buying right now / live order book for BNB\"\n"
        "• \"Practice trade with real prices\"\n"
        "• \"Set risk to 1 percent\"\n"
        "• \"Is my money safe?\"")
    return {"intent": "help", "reply": reply, "data": {}}


def rng_word(rpt: float) -> str:
    return "narrow" if rpt <= 9 else "wide" if rpt >= 18 else "normal"
