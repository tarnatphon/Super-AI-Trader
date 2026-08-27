"""Train the learned directional model on a market series and report OOS metrics."""
from __future__ import annotations

from ..data.market import get_series
from ..data.indicators import precompute
from ..data.orderflow import precompute_flow, flow_snapshot
from ..data.levels import level_setup
from .dataset import build_dataset, features_at, FEATURE_NAMES
from .model import train_logistic, evaluate, predict_proba, save_model


def train_for_ticker(ticker: str, days: int = 900, real: bool = False,
                     horizon: int = 5, save_path: str | None = None):
    bars = get_series(ticker, days=days, real=real)
    split_idx = int(len(bars) * 0.6)
    Xtr, ytr, _ = build_dataset(bars[:split_idx], horizon=horizon)
    Xte, yte, idxs_te = build_dataset(bars[split_idx:], horizon=horizon)
    model = train_logistic(Xtr, ytr)
    metrics = evaluate(model, Xte, yte) if Xte else {}
    metrics["train_samples"] = len(ytr)
    metrics["test_samples"] = len(yte)

    # Feature weights (interpretable — see which inputs drive the prediction).
    weights = sorted(
        ((FEATURE_NAMES[j], round(model["w"][j], 3)) for j in range(len(FEATURE_NAMES))),
        key=lambda kv: abs(kv[1]),
        reverse=True,
    )
    metrics["top_features"] = weights[:6]

    # Latest live read: pressure, levels, and model P(up).
    pre = precompute(bars)
    flow = precompute_flow(bars)
    i = len(bars) - 1
    fs = flow_snapshot(flow, bars, i)
    snap_idx = min(i, len(bars) - 1)
    atr_v = pre["atr"][snap_idx]
    atr_pct = atr_v / bars[snap_idx].close * 100 if atr_v else None
    lv = level_setup(bars, snap_idx, flow, atr_pct=atr_pct)
    feats = features_at(bars, snap_idx, pre, flow)
    p_up = predict_proba(model, feats) if feats else None

    live = {
        "ticker": ticker,
        "pressure": fs["pressure"],
        "order_flow_imbalance": fs["ofi"],
        "buy_vol_ratio": fs["buy_vol_ratio"],
        "cum_delta_divergence": fs["cum_delta_divergence"],
        "price": lv["price"],
        "support_buy_zone": lv["support"],
        "resistance_sell_zone": lv["resistance"],
        "at_support": lv["at_support"],
        "at_resistance": lv["at_resistance"],
        "stop_below": lv["stop_below"],
        "stop_above": lv["stop_above"],
        "model_prob_up": round(p_up, 3) if p_up is not None else None,
        "model_call": "BUY" if p_up and p_up >= 0.58 else "SELL" if p_up and p_up <= 0.42 else "HOLD",
    }

    if save_path:
        save_model(model, save_path)

    return model, metrics, live
