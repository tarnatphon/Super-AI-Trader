"""Order-flow / market-microstructure features.

This module infers *real buying vs selling pressure* from OHLCV bars — the closest
you can get to order flow without paid tick/Level-2 data. The core idea (well
established in market micro-structure research, e.g. the Lee–Ready / Easley-style
signing of trades):

- A bar that closes near its **high** on rising volume = aggressive **buyers** in
  control. A bar closing near its **low** = aggressive **sellers** in control.
- Signed volume (≈ buy minus sell) is summed into **cumulative delta**; persistent
  divergence between price and delta (price makes a new high but delta doesn't) is a
  classic exhaustion/turnover warning.

With real tick data later, the same interface can be fed exact aggressor side.

All functions only use data up to and including bar `idx` (no look-ahead).
"""
from __future__ import annotations

from .indicators import closes


def _clv(bar) -> float:
    """Close Location Value in [-1, 1]: where the close sits within the bar's range.
    +1 = close at high (buyers won the bar), -1 = close at low (sellers won)."""
    rng = bar.high - bar.low
    if rng <= 0:
        return 0.0
    return ((bar.close - bar.low) - (bar.high - bar.close)) / rng


def signed_volume(bar) -> tuple[float, float]:
    """Return (buy_volume, sell_volume) estimate for one bar."""
    clv = _clv(bar)
    if clv >= 0:
        buy = bar.volume * (0.5 + clv / 2)
        sell = bar.volume - buy
    else:
        sell = bar.volume * (0.5 + (-clv) / 2)
        buy = bar.volume - sell
    return buy, sell


def precompute_flow(bars, period: int = 20) -> dict:
    """Precompute order-flow series once (O(n))."""
    c = closes(bars)
    clv, delta, cum_delta, buy_v, sell_v, vol_ma = [], [], [], [], [], []
    cd = 0.0
    for i, b in enumerate(bars):
        v = _clv(b)
        buy, sell = signed_volume(b)
        d = buy - sell
        cd += d
        clv.append(v)
        buy_v.append(buy)
        sell_v.append(sell)
        delta.append(d)
        cum_delta.append(cd)
        lo = max(0, i - period + 1)
        vol_ma.append(sum(x.volume for x in bars[lo : i + 1]) / (i - lo + 1))
    # returns for divergence calcs
    return {
        "clv": clv,
        "delta": delta,
        "cum_delta": cum_delta,
        "buy_vol": buy_v,
        "sell_vol": sell_v,
        "vol_ma": vol_ma,
        "closes": c,
        "period": period,
    }


def flow_snapshot(flow: dict, bars, idx: int) -> dict:
    """Order-flow features at bar `idx` (uses bars up to idx only)."""
    p = flow["period"]
    lo = max(0, idx - p + 1)
    window_delta = sum(flow["delta"][lo : idx + 1])
    window_vol = flow["buy_vol"][idx] + flow["sell_vol"][idx]  # current bar
    win_buy = sum(flow["buy_vol"][lo : idx + 1])
    win_sell = sum(flow["sell_vol"][lo : idx + 1])
    total = win_buy + win_sell
    ofi = (win_buy - win_sell) / total if total > 0 else 0.0  # order-flow imbalance -1..1

    c = flow["closes"]
    # Cumulative delta divergence: price higher than `p` bars ago but delta weaker,
    # or vice versa (sign of hidden buying/selling).
    price_up = c[idx] > c[max(0, idx - p)]
    cd_now = flow["cum_delta"][idx]
    cd_then = flow["cum_delta"][max(0, idx - p)]
    delta_up = cd_now > cd_then
    if price_up and not delta_up:
        divergence = "bearish"   # price up but sellers quietly absorbing
    elif (not price_up) and delta_up:
        divergence = "bullish"   # price down but buyers quietly accumulating
    else:
        divergence = "none"

    vol_spike = flow["vol_ma"][idx] and bars[idx].volume > 1.8 * flow["vol_ma"][idx]

    return {
        "clv": round(flow["clv"][idx], 2),
        "ofi": round(ofi, 3),                    # order-flow imbalance (-1 sell .. +1 buy)
        "window_delta": round(window_delta),     # signed volume over the window
        "buy_vol_ratio": round(win_buy / total, 3) if total else 0.5,
        "cum_delta_divergence": divergence,
        "volume_spike": bool(vol_spike),
        "pressure": "buying" if ofi > 0.12 else "selling" if ofi < -0.12 else "balanced",
    }
