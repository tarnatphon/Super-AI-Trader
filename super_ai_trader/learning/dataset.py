"""Build a supervised dataset from market data for the learned directional model.

Features at bar i use ONLY information available at bar i. The label is whether the
price is up `horizon` bars later (1) or not (0).
"""
from __future__ import annotations

from ..data.indicators import precompute, closes
from ..data.orderflow import precompute_flow, flow_snapshot
from ..data.levels import level_setup

FEATURE_NAMES = [
    "rsi14", "macd_hist", "atr14_pct", "sma50_dist", "sma200_dist", "bb_pos",
    "ret_1", "ret_5", "ret_20",
    "clv", "ofi", "buy_vol_ratio", "delta_diverg", "vol_spike",
    "dist_support", "dist_resist",
]


def features_at(bars, idx: int, pre: dict, flow: dict) -> list[float] | None:
    """Return a 16-feature vector at bar idx, or None if indicators not ready.
    Features use only data up to and including idx, so they are valid on the most
    recent bar (idx = len-1) for live prediction. Only *labels* need future bars.
    """
    c = pre["c"]
    if idx < 200:
        return None
    snap_p = c[idx]
    rsi = pre["rsi"][idx]
    macdh = pre["macd_hist"][idx]
    atr = pre["atr"][idx]
    up, lo = pre["bb_upper"][idx], pre["bb_lower"][idx]

    def nz(v, default=0.0):
        return default if v is None else v

    rsi_v = nz(rsi, 50.0)
    macdh_v = nz(macdh, 0.0)
    atr_pct = (atr / snap_p * 100) if atr else 1.0
    s50 = pre["sma50"][idx]
    s200 = pre["sma200"][idx]
    s50_d = (snap_p / s50 - 1) * 100 if s50 else 0.0
    s200_d = (snap_p / s200 - 1) * 100 if s200 else 0.0
    bb_pos = (snap_p - lo) / (up - lo) if (lo and up and up != lo) else 0.5

    fs = flow_snapshot(flow, bars, idx)
    lvl = level_setup(bars, idx, flow, atr_pct=atr_pct)

    diverg = {"bullish": 1.0, "bearish": -1.0, "none": 0.0}[fs["cum_delta_divergence"]]
    return [
        rsi_v,
        macdh_v,
        atr_pct,
        s50_d,
        s200_d,
        bb_pos,
        (c[idx] / c[idx - 1] - 1) * 100 if idx >= 1 else 0.0,
        (c[idx] / c[idx - 5] - 1) * 100 if idx >= 5 else 0.0,
        (c[idx] / c[idx - 20] - 1) * 100 if idx >= 20 else 0.0,
        fs["clv"],
        fs["ofi"],
        fs["buy_vol_ratio"],
        diverg,
        1.0 if fs["volume_spike"] else 0.0,
        lvl["dist_to_support_pct"] if lvl["dist_to_support_pct"] is not None else 5.0,
        lvl["dist_to_resist_pct"] if lvl["dist_to_resist_pct"] is not None else 5.0,
    ]


def label_at(bars, idx: int, horizon: int = 5, threshold_pct: float = 0.0) -> int:
    """1 if close `horizon` bars later is up by > threshold_pct, else 0."""
    c = closes(bars)
    if idx + horizon >= len(c):
        return None  # type: ignore
    future_ret = (c[idx + horizon] / c[idx] - 1) * 100
    return 1 if future_ret > threshold_pct else 0


def build_dataset(bars, horizon: int = 5, test_fraction: float = 0.0):
    """Return (X, y, indices). Split chronologically when test_fraction > 0."""
    pre = precompute(bars)
    flow = precompute_flow(bars)
    X, y, idxs = [], [], []
    for i in range(200, len(bars) - horizon - 1):
        feats = features_at(bars, i, pre, flow)
        lab = label_at(bars, i, horizon)
        if feats is None or lab is None:
            continue
        X.append(feats)
        y.append(lab)
        idxs.append(i)
    if test_fraction and X:
        split = int(len(X) * (1 - test_fraction))
        return (X[:split], X[split:], y[:split], y[split:], idxs[:split], idxs[split:])
    return X, y, idxs
