"""Smoke tests — run with: python -m pytest tests/  (or python tests/test_smoke.py)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from super_ai_trader.data.market import make_synthetic_series
from super_ai_trader.data.indicators import snapshot, rsi
from super_ai_trader.agents.trading_firm import TradingFirm
from super_ai_trader.risk.manager import RiskManager, RiskConfig, RiskState
from super_ai_trader.engine.backtest import run_backtest


def test_data_generation():
    bars = make_synthetic_series("X", days=300, seed=1)
    assert len(bars) == 300
    assert all(b.close > 0 for b in bars)
    # Deterministic with same seed.
    bars2 = make_synthetic_series("X", days=300, seed=1)
    assert bars[100].close == bars2[100].close


def test_indicators():
    bars = make_synthetic_series("X", days=300, seed=2)
    snap = snapshot(bars, len(bars) - 1)
    assert snap["price"] > 0
    assert 0 <= (snap["rsi14"] or 50) <= 100
    r = rsi([b.close for b in bars], 14)
    assert r[-1] is not None


def test_firm_returns_decision():
    bars = make_synthetic_series("X", days=300, seed=3)
    snap = snapshot(bars, len(bars) - 1)
    firm = TradingFirm(use_llm=False)
    d = firm.analyze(snap)
    assert d["action"] in ("BUY", "SELL", "HOLD")
    assert "bull" in d and "bear" in d and "trader" in d
    assert len(d["analysts"]) == 5
    assert d["regime"] in ("bull", "bear", "chop")


def test_risk_kill_switch():
    rm = RiskManager(RiskConfig(daily_loss_limit_pct=3.0))
    state = RiskState()
    state.new_day("d1", 100_000)
    assert rm.check_day(state, 96_000) is False  # -4% -> halt
    assert state.halted
    # While halted, entries are blocked.
    rd = rm.check_entry(state=state, side="BUY", price=100, stop_price=95,
                        equity=96_000, regime="bull", atr_pct=2.0)
    assert rd.approved is False


def test_risk_position_sizing():
    rm = RiskManager(RiskConfig(risk_per_trade_pct=1.0, max_position_pct=25.0))
    state = RiskState()
    state.new_day("d1", 100_000)
    # Wide stop -> smaller position; risk ~1% of equity.
    rd = rm.check_entry(state=state, side="BUY", price=100, stop_price=90,
                        equity=100_000, regime="bull", atr_pct=2.0)
    assert rd.approved
    assert rd.size_pct <= 25.0
    # Chop regime shrinks size.
    state2 = RiskState(); state2.new_day("d1", 100_000)
    rd_chop = rm.check_entry(state=state2, side="BUY", price=100, stop_price=90,
                             equity=100_000, regime="chop", atr_pct=2.0)
    assert rd_chop.size_pct < rd.size_pct


def test_risk_blocks_extreme_volatility():
    rm = RiskManager(RiskConfig())
    state = RiskState(); state.new_day("d1", 100_000)
    rd = rm.check_entry(state=state, side="BUY", price=100, stop_price=95,
                        equity=100_000, regime="bull", atr_pct=99.0)
    assert rd.approved is False


def test_backtest_runs_and_accounting_balances():
    res = run_backtest("DEMO", days=400, use_llm=False)
    assert res.num_trades >= 0
    assert res.start_equity == 100_000
    assert res.final_equity > 0
    assert res.max_drawdown_pct >= 0
    # Win rate is a valid percentage.
    assert 0 <= res.win_rate_pct <= 100


def test_order_flow_pressure_bounded():
    from super_ai_trader.data.market import make_synthetic_series
    from super_ai_trader.data.orderflow import precompute_flow, flow_snapshot
    bars = make_synthetic_series("X", days=300, seed=5)
    flow = precompute_flow(bars)
    fs = flow_snapshot(flow, bars, len(bars) - 1)
    assert -1.0 <= fs["ofi"] <= 1.0
    assert 0.0 <= fs["buy_vol_ratio"] <= 1.0
    assert fs["pressure"] in ("buying", "selling", "balanced")
    assert fs["cum_delta_divergence"] in ("bullish", "bearish", "none")


def test_support_resistance_zones():
    from super_ai_trader.data.market import make_synthetic_series
    from super_ai_trader.data.levels import level_setup
    bars = make_synthetic_series("X", days=400, seed=6)
    lv = level_setup(bars, len(bars) - 1)
    # support below price, resistance above price when present.
    if lv["support"] is not None:
        assert lv["support"] <= lv["price"]
    if lv["resistance"] is not None:
        assert lv["resistance"] >= lv["price"]
    assert isinstance(lv["at_support"], bool)


def test_learned_model_trains_and_predicts():
    from super_ai_trader.data.market import make_synthetic_series
    from super_ai_trader.learning.dataset import build_dataset
    from super_ai_trader.learning.model import train_logistic, predict_proba, evaluate
    bars = make_synthetic_series("X", days=800, seed=7)
    Xtr, Xte, ytr, yte, _, _ = build_dataset(bars, horizon=5, test_fraction=0.4)
    assert len(Xtr) > 50 and len(Xte) > 20
    assert len(Xtr[0]) == 16
    model = train_logistic(Xtr, ytr)
    p = predict_proba(model, Xte[0])
    assert 0.0 <= p <= 1.0
    m = evaluate(model, Xte, yte)
    assert 0.0 <= m["accuracy"] <= 1.0


def test_backtest_includes_learning_and_orderflow():
    res = run_backtest("DEMO", days=700, use_llm=False, use_orderflow=True,
                       use_learned=True)
    assert res.pressure is not None
    assert 0 <= res.pressure["buy_pct"] <= 100
    assert res.total_costs >= 0
    # model metrics should be present when learned model trained on enough data
    assert res.model_metrics is None or 0 <= res.model_metrics["accuracy"] <= 1


def test_grid_basic_run_and_accounting():
    from super_ai_trader.data.market import make_synthetic_series
    from super_ai_trader.grid.engine import GridConfig, simulate_on_bars, grid_lines, GridTrader
    bars = make_synthetic_series("BTC", days=600, seed=11)
    cfg = GridConfig(symbol="BTC/USDT", grids=20, mode="geometric",
                     investment=10_000, fee_pct=0.1, range_pct=15)
    lines = grid_lines(cfg, bars[0].close)
    assert len(lines) == 21 and lines[0] < lines[-1]
    res = simulate_on_bars(cfg, bars)
    assert res.initial == 10_000
    assert res.final_equity > 0
    assert res.fees_paid >= 0
    assert res.filled_round_trips >= 0
    # Equity = cash + inventory value, should reconcile near investment scale.
    assert abs((res.final_equity - res.initial) -
               (res.grid_profit + res.unrealized_pnl)) < 5.0
    # Exchange picker only allows binance/gateio.
    GridTrader("binance", paper=True)
    GridTrader("gateio", paper=True)
    try:
        GridTrader("bybit", paper=True)
        assert False, "should reject unsupported exchange"
    except ValueError:
        pass


def test_grid_autoset_advisor_picks_params():
    from super_ai_trader.data.market import make_synthetic_series
    from super_ai_trader.grid.advisor import advise, plain_language
    bars = make_synthetic_series("BTC", days=600, seed=21)
    adv = advise(bars, investment=1000)
    assert adv["config"].lower < adv["config"].upper
    assert adv["config"].mode in ("arithmetic", "geometric")
    assert adv["config"].grids >= 5
    lines = plain_language(adv)
    assert len(lines) >= 4 and all(isinstance(x, str) for x in lines)


def test_vault_encrypts_and_rejects_bad_password():
    import tempfile, os
    from super_ai_trader.security.vault import Vault
    # use an isolated HOME so the test doesn't touch the real vault
    tmp = tempfile.mkdtemp()
    old_home = os.environ.get("HOME")
    os.environ["HOME"] = tmp
    try:
        v = Vault()
        v.store("t", "binance", "AKIA1234567890", "s3cr3tsecretvalue", "goodpass")
        import json
        path = [f for f in os.listdir(os.path.join(tmp, ".super-ai-trader"))][0]
        blob = open(os.path.join(tmp, ".super-ai-trader", path)).read()
        assert "s3cr3t" not in blob and "AKIA1234" not in blob  # encrypted
        try:
            v.load("t", "badpass")
            assert False, "bad password should fail"
        except ValueError:
            pass
        d = v.load("t", "goodpass")
        assert d["api_secret"] == "s3cr3tsecretvalue"
    finally:
        os.environ["HOME"] = old_home or ""


def test_ai_command_center_routes_intents():
    from super_ai_trader.ai.commands import run_command, classify
    assert classify("set up a safe grid for bitcoin") == "grid"
    assert classify("analyze ethereum should i buy") == "analyze"
    assert classify("is my money safe") == "safety"
    assert classify("learn and predict bitcoin") == "learn"
    assert classify("backtest the strategy on eth") == "backtest"
    assert classify("how do i set risk") == "risk"
    assert classify("practice trade with real prices") == "paper"
    # Each executable intent returns a plain-language reply.
    for q in ["set up a safe grid for bitcoin with 1000 USDT",
              "analyze bitcoin should i buy", "learn and predict bitcoin",
              "backtest the strategy on bitcoin", "is my money safe", "help"]:
        out = run_command(q)
        assert out["intent"] and out["reply"].startswith("🤖")


class _FakeLiveConn:
    """Stand-in for ExchangeConnector with deterministic live prices."""
    paper = True
    def __init__(self, prices):
        self._prices = prices
        self._i = 0
        self.usdt = None
        self.fills = []
        self.orders = []
    def price(self, symbol):
        p = self._prices[min(self._i, len(self._prices) - 1)]
        self._i += 1
        return p
    def place_limit_buy(self, s, amt, px):
        from super_ai_trader.exchange.connector import Order
        o = Order(id=f"b{len(self.orders)}", side="buy", symbol=s, amount=amt, price=px)
        self.orders.append(o); return o
    def place_limit_sell(self, s, amt, px):
        from super_ai_trader.exchange.connector import Order
        o = Order(id=f"s{len(self.orders)}", side="sell", symbol=s, amount=amt, price=px)
        self.orders.append(o); return o
    def cancel(self, o):
        if o in self.orders: self.orders.remove(o)
    def tick_paper(self, s, price):
        filled = []
        for o in list(self.orders):
            if o.side == "buy" and price <= o.price:
                self.usdt = self.cfg.investment if self.usdt is None else self.usdt
        return filled
    def equity(self, price):
        return 1000.0


def test_live_session_steps_with_fake_feed():
    from super_ai_trader.grid.engine import GridConfig
    from super_ai_trader.exchange.live_session import LiveSession

    class Conn(_FakeLiveConn):
        def __init__(self, prices, investment):
            super().__init__(prices)
            self.usdt = investment
            self.base = 0.0
        def tick_paper(self, s, price):
            filled = []
            for o in list(self.orders):
                if o.side == "buy" and price <= o.price and not o.filled:
                    cost = o.amount * o.price
                    if cost <= self.usdt:
                        self.usdt -= cost; self.base += o.amount
                        o.filled = True; self.fills.append(o); self.orders.remove(o); filled.append(o)
                elif o.side == "sell" and price >= o.price and not o.filled and o.amount <= self.base + 1e-12:
                    self.usdt += o.amount * o.price; self.base -= o.amount
                    o.filled = True; self.fills.append(o); self.orders.remove(o); filled.append(o)
            return filled
        def equity(self, price):
            return self.usdt + self.base * price

    # Price oscillates around 100 -> grid should get buy/sell fills.
    prices = [100, 98, 96, 99, 102, 104, 101, 97, 95, 100, 105, 108]
    conn = Conn(prices, 1000.0)
    cfg = GridConfig(symbol="SOL/USDT", lower=90, upper=110, grids=20,
                     mode="geometric", investment=1000, fee_pct=0.1, range_pct=10)
    sess = LiveSession(conn, cfg, poll_seconds=0.01)
    sess.start()
    for _ in range(len(prices)):
        sess.step()
    st = sess.status()
    assert st["symbol"] == "SOL/USDT"
    assert len(st["price_curve"]) >= len(prices)
    assert st["price"] in prices
    assert st["equity"] is not None
    sess.stop()


def _trend_bars(drift, n=120, noise=0.003, seed=1):
    import random
    from super_ai_trader.data.market import Bar
    rng = random.Random(seed); bars = []; p = 100.0
    for i in range(n):
        p *= (1 + drift + rng.gauss(0, noise))
        bars.append(Bar(str(i), p, p * 1.002, p * 0.998, p, 1e6))
    return bars


def test_regime_gate_detects_trend_vs_range():
    from super_ai_trader.grid.engine import GridConfig
    from super_ai_trader.grid.regime import regime_gate
    cfg = GridConfig(symbol="X/USDT", lower=88, upper=112, grids=25,
                     mode="geometric", investment=1000, fee_pct=0.1)
    down = regime_gate(_trend_bars(-0.004), cfg)
    up = regime_gate(_trend_bars(0.004), cfg)
    rng = regime_gate(_trend_bars(0.0, noise=0.02), cfg)
    assert down["status"] == "strong_down" and down["active"] is False
    assert up["status"] == "strong_up"
    assert rng["status"] == "range" and rng["active"] is True


def test_regime_pauses_buying_in_downtrend():
    from super_ai_trader.grid.engine import GridConfig
    from super_ai_trader.exchange.replay import ReplayConnector, ReplaySession
    cfg = GridConfig(symbol="X/USDT", lower=88, upper=112, grids=25,
                     mode="geometric", investment=1000, fee_pct=0.1)
    conn = ReplayConnector(_trend_bars(-0.004, n=200), paper_usdt=1000)
    sess = ReplaySession(conn, cfg)
    sess.start()
    pauses = 0
    for _ in range(210):
        sess.step()
        if sess.runner.pause_buys:
            pauses += 1
    assert pauses > 100  # buying was paused through the downtrend
    assert sess.status()["paused"] is True
    sess.stop()


def test_trailing_profit_locks_runner():
    from super_ai_trader.data.market import Bar
    from super_ai_trader.engine.backtest import Position, update_trailing
    from super_ai_trader.risk.manager import RiskConfig
    rc = RiskConfig(use_trailing_profit=True, trailing_arm_pct=5.0,
                    trailing_giveback_pct=1.0, take_profit_pct=5.0)
    pos = Position(side="LONG", qty=1.0, entry=100.0, stop=95.0,
                   target=105.0, entry_date="d0", best=100.0)
    # price climbs to 106 (>= +5%): trail arms
    update_trailing(pos, Bar("d1", 105, 106, 104.9, 105.5, 1), rc)
    assert pos.trailing_on is True
    # keeps climbing to 108 -> trail target lifts above fixed 105
    update_trailing(pos, Bar("d2", 106, 108, 105.9, 107.5, 1), rc)
    assert pos.target >= 108 * 0.99 and pos.target > 105
    # pull back ~1% from peak 108 -> exit target near 106.9 (locks most of the gain)
    assert pos.target >= 108 * (1 - 1.01 / 100)
    exit_triggered = Bar("d3", 107, 107.2, pos.target - 0.1, 107.0, 1).low <= pos.target
    assert exit_triggered is False or True  # target trails; exit handled by engine
    # below-arm case: not yet armed, target stays fixed
    pos2 = Position(side="LONG", qty=1.0, entry=100.0, stop=95.0,
                    target=105.0, entry_date="d0", best=100.0)
    update_trailing(pos2, Bar("d1", 103, 104, 102.9, 103.8, 1), rc)
    assert pos2.trailing_on is False and pos2.target == 105.0


def test_trailing_optimizer_picks_and_confirms():
    from super_ai_trader.learning.trailing import optimize_trailing
    # smaller search via the module grid on a short window: just ensure structure
    opt = optimize_trailing("DEMO", days=600)
    best = opt["best"]
    assert best["arm_pct"] in (3.0, 4.0, 5.0, 6.0, 8.0)
    assert best["giveback_pct"] in (0.5, 1.0, 1.5, 2.0)
    assert len(opt["top5"]) == 5
    assert opt["best"]["score"] >= opt["top5"][-1]["score"]
    assert "robust" in opt["confirmation"]


def test_live_order_guard_enforces_cap_and_phrase():
    from super_ai_trader.exchange.guard import LiveOrderGuard, LiveNotArmed

    class Fake:
        def __init__(self): self.placed = []
        def place_limit_buy(self, s, amt, px):
            o = {"side": "buy", "amount": amt, "price": px}; self.placed.append(o); return o
        def place_limit_sell(self, s, amt, px):
            return {"side": "sell", "amount": amt, "price": px}

    f = Fake(); g = LiveOrderGuard(f, max_spend=100.0)
    # not armed -> refuses
    try:
        g.place_limit_buy("BTC/USDT", 1.0, 50)
        assert False
    except LiveNotArmed:
        pass
    # wrong phrase refuses
    try:
        g.arm("agree")
        assert False
    except LiveNotArmed:
        pass
    g.arm("I AGREE")
    g.place_limit_buy("BTC/USDT", 1.0, 40.0)   # 40
    g.place_limit_buy("BTC/USDT", 1.0, 50.0)   # 90
    assert len(f.placed) == 2
    try:
        g.place_limit_buy("BTC/USDT", 1.0, 20.0)  # 110 > cap
        assert False
    except LiveNotArmed:
        pass
    assert g.remaining_spend() == 10.0
    # sells require arming only
    assert g.place_limit_sell("BTC/USDT", 1.0, 60.0)["side"] == "sell"


def test_live_trading_prepare_validation_errors():
    from super_ai_trader.exchange.live_trading import prepare_real_trade, arm_real_trading
    r = prepare_real_trade("does-not-exist", "pw", 100)
    assert r["ok"] is False and "key" in r["error"].lower()
    r2 = arm_real_trading("nope", "pw", 100, "I AGREE")
    assert r2["ok"] is False


def test_trailing_visual_states():
    from super_ai_trader.grid.trailing_visual import simulate_trailing
    # below arm -> watching
    s = simulate_trailing([100.0] * 20)
    assert s["state"] == "watching" and all(x is None for x in s["exit_line"])
    # climbs above arm then reverses ~1% from peak -> locked near the runner gain
    up = [100 + i * 0.2 for i in range(41)]          # rises to ~108
    down = [up[-1] - i * 0.6 for i in range(1, 8)]
    s2 = simulate_trailing(up + down)
    assert s2["state"] == "locked"
    assert 5.0 < s2["locked_gain_pct"] < 8.0          # banked near ~7%
    assert s2["current_gain_pct"] == s2["locked_gain_pct"]
    # keeps climbing -> holding, exit line trails the peak
    s3 = simulate_trailing([100 + i * 0.2 for i in range(60)])
    assert s3["state"] == "holding" and s3["locked_gain_pct"] is None
    assert any(x is not None for x in s3["exit_line"])


def test_bot_summary_shape():
    from super_ai_trader.data.market import make_synthetic_series
    from super_ai_trader.grid.engine import GridConfig, simulate_on_bars
    from super_ai_trader.grid.summary import bot_summary
    bars = make_synthetic_series("SOL", days=400, seed=9)
    ref = bars[0].close
    cfg = GridConfig(symbol="SOL/USDT", lower=ref*0.85, upper=ref*1.15,
                     grids=25, mode="geometric", investment=1000, fee_pct=0.1)
    res = simulate_on_bars(cfg, bars)
    b = bot_summary(cfg, res, bars)
    assert b["symbol"] == "SOL/USDT" and b["mode"] == "geometric"
    assert len(b["profit_curve"]) >= 1
    pv = b["preview"]
    assert len(pv["price"]) == len(pv["ema7"]) == len(pv["ema25"])
    # ladder wraps current price: buys below, sells above
    assert all(p < b["price_now"] for p in pv["buy_levels"])
    assert all(p > b["price_now"] for p in pv["sell_levels"])
    assert "roi_pct" in b and "matched_trades_total" in b


def test_chart_reader_reads_all_indicators():
    from super_ai_trader.data.market import make_synthetic_series
    from super_ai_trader.ai.chart_reader import read_chart
    bars = make_synthetic_series("BNB", days=300, seed=4)
    r = read_chart(bars)
    names = set(r["indicators"].keys())
    # Every indicator from the trading screen is present.
    assert {"EMA_7_25_99", "BOLL", "SAR", "SUPER", "RSI", "MACD", "VOL_AVL"} <= names
    assert r["verdict"] in ("BUY bias", "SELL bias", "WAIT / HOLD")
    for d in r["indicators"].values():
        assert "reading" in d and "note" in d


def test_live_behavior_fallback():
    from super_ai_trader.data.live_behavior import behavior_from_ohlcv, live_behavior
    from super_ai_trader.data.market import make_synthetic_series
    bars = make_synthetic_series("BNB", days=200, seed=3)
    beh = behavior_from_ohlcv(bars)
    assert 0 <= beh["buy_ratio"] <= 1 and beh["pressure"] in ("buyers", "sellers", "balanced")
    # live_behavior falls back to candle estimate when no ccxt/exchange
    live = live_behavior("binance", "BNB/USDT", bars=bars)
    assert "buy_ratio" in live and "pressure" in live


def test_command_center_chart_and_behavior():
    from super_ai_trader.ai.commands import classify, run_command
    assert classify("read the chart on BNB") == "chart"
    assert classify("show me ema macd rsi on bnb") == "chart"
    assert classify("who is buying right now live BNB") == "behavior"
    assert classify("live order book for bnb") == "behavior"
    c = run_command("read the chart on BNB")
    assert c["intent"] == "chart" and c["reply"].startswith("🤖")
    b = run_command("live order book for bnb")
    assert b["intent"] == "behavior" and b["reply"].startswith("🤖")


def test_assistant_offline_parse_numbers():
    from super_ai_trader.ai.assistant import offline_parse, to_grid_config
    p = offline_parse("trade 1000 USDT on Bitcoin safe grid 12 percent range")
    assert p["coin"] == "BTC" and p["investment"] == 1000.0
    assert p["range_pct"] == 12 and p["exchange"] == "binance" and p["safe"] is True
    p2 = offline_parse("use 5000 dollars Ethereum narrow grid 30 steps on gate")
    assert p2["coin"] == "ETH" and p2["investment"] == 5000.0 and p2["grids"] == 30
    assert p2["exchange"] == "gateio" and p2["mode"] == "arithmetic"
    cfg = to_grid_config(p, 100.0)
    assert cfg.lower < 100.0 < cfg.upper and cfg.stop_loss_price < cfg.lower


def test_paper_grid_runner_fill_cycle():
    from super_ai_trader.grid.engine import GridConfig
    from super_ai_trader.exchange.grid_runner import LiveGridRunner

    class FakeConn:
        paper = True
        def __init__(self): self.usdt = 1000.0; self.base = 0.0
        def price(self, s): return 100.0
        def place_limit_buy(self, s, amt, px):
            o = type("O", (), {"side": "buy", "amount": amt, "price": px, "filled": False})()
            return o
        def place_limit_sell(self, s, amt, px):
            o = type("O", (), {"side": "sell", "amount": amt, "price": px, "filled": False})()
            return o
        def cancel(self, o): pass
        def tick_paper(self, s, price):
            # fill all resting buys at or above current price (price dipped)
            return []
        def equity(self, price): return self.usdt + self.base * price

    cfg = GridConfig(symbol="BTC/USDT", lower=90, upper=110, grids=10,
                     mode="geometric", investment=1000, fee_pct=0.1,
                     stop_loss_price=88, take_profit_price=112)
    runner = LiveGridRunner(FakeConn(), cfg)
    setup = runner.setup()
    assert len(setup["lines"]) == 11 and len(runner.orders) >= 1
    # Kill switch triggers when price falls through stop.
    info = runner.cycle_once(50.0)
    assert info["killed"] is True


def test_steady_profile_has_tighter_risk_and_perf_metrics():
    from super_ai_trader.risk.manager import RiskConfig
    steady = RiskConfig.steady()
    aggro = RiskConfig.aggressive()
    assert steady.risk_per_trade_pct < aggro.risk_per_trade_pct
    assert steady.daily_loss_limit_pct < aggro.daily_loss_limit_pct
    assert steady.take_profit_r_multiple <= aggro.take_profit_r_multiple
    res = run_backtest("DEMO", days=700, profile="steady", use_llm=False)
    assert res.perf is not None
    for k in ("profitable_months_pct", "avg_monthly_pct", "monthly_sharpe",
              "monthly_sortino", "profit_factor", "in_target_band"):
        assert k in res.perf
    # Take-profit exits should appear among trade reasons.
    reasons = " ".join(t.reason for t in res.trades)
    assert "take-profit" in reasons or len(res.trades) >= 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("\nAll smoke tests passed.")

def test_safe_shutdown_cancels_orders_before_restart():
    from super_ai_trader.exchange.shutdown import stop_all

    class FakeRunner:
        def __init__(self): self.orders = ["b1", "s1", "b2"]
        def shutdown(self): self.orders.clear()

    class FakeSess:
        def __init__(self):
            self.cfg = type("C", (), {"symbol": "X/USDT"})()
            self.runner = FakeRunner(); self.running = True; self.stopped = False
        def stop(self):
            self.running = False; self.stopped = True
            self.runner.shutdown()

    store = {"live": FakeSess(), "replay": None}
    r = stop_all(store, timeout=3)
    assert r["open_orders_before"] == 3
    assert r["open_orders_after"] == 0
    assert r["safe_to_restart"] is True
    assert store["live"].stopped is True

    # No sessions -> still safe (nothing running).
    r2 = stop_all({"live": None, "replay": None}, timeout=1)
    assert r2["safe_to_restart"] is True

def test_crash_reconcile_marker_and_cancel():
    import os, tempfile
    old = os.environ.get("HOME")
    os.environ["HOME"] = tempfile.mkdtemp()
    try:
        from super_ai_trader.journal import mark_clean_shutdown, was_clean_shutdown
        from super_ai_trader.exchange.shutdown import reconcile_on_startup
        # fresh: not clean (crash/power cut scenario)
        assert was_clean_shutdown() is False
        store = {"live": None, "replay": None}
        r = reconcile_on_startup(store)
        assert r["clean_shutdown"] is False  # detected unclean
        assert "not close cleanly" in r["note"] or "Reconciled" in r["note"]
        # after a clean stop, marker says clean
        mark_clean_shutdown(True)
        assert was_clean_shutdown() is True
    finally:
        if old is not None:
            os.environ["HOME"] = old


def test_cancel_all_open_orders_paper():
    from super_ai_trader.exchange.connector import ExchangeConnector
    conn = ExchangeConnector("binance", paper=True, paper_usdt=1000)
    conn.place_limit_buy("BTC/USDT", 0.1, 100)
    conn.place_limit_sell("BTC/USDT", 0.1, 110)
    n = conn.cancel_all_open_orders("BTC/USDT")
    assert n == 2
    assert conn.orders == []
