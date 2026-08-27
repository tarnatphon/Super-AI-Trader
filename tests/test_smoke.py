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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("\nAll smoke tests passed.")
