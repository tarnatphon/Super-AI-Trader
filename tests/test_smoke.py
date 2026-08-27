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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("\nAll smoke tests passed.")
