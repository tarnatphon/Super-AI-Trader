"""Pure-Python technical indicators (no third-party deps required)."""
from __future__ import annotations

from collections import deque


def closes(bars) -> list[float]:
    return [b.close for b in bars]


def sma(values: list[float], period: int) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(values)):
        if i < period - 1:
            out.append(None)
        else:
            out.append(sum(values[i - period + 1 : i + 1]) / period)
    return out


def ema(values: list[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    k = 2 / (period + 1)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(values: list[float], period: int = 14) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return out
    gains = deque(maxlen=period)
    losses = deque(maxlen=period)
    for i in range(1, period + 1):
        ch = values[i] - values[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    out[period] = 100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    for i in range(period + 1, len(values)):
        ch = values[i] - values[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(ch, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-ch, 0.0)) / period
        out[i] = 100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    return out


def macd(values: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(values, fast)
    ema_slow = ema(values, slow)
    macd_line: list[float | None] = []
    for f, s in zip(ema_fast, ema_slow):
        macd_line.append(None if f is None or s is None else f - s)
    valid = [m for m in macd_line if m is not None]
    sig_valid = ema(valid, signal) if valid else []
    sig: list[float | None] = [None] * len(values)
    j = 0
    for i, m in enumerate(macd_line):
        if m is None:
            continue
        sig[i] = sig_valid[j] if j < len(sig_valid) else None
        j += 1
    hist = [
        None if (m is None or s is None) else m - s
        for m, s in zip(macd_line, sig)
    ]
    return macd_line, sig, hist


def atr(bars, period: int = 14) -> list[float | None]:
    out: list[float | None] = [None] * len(bars)
    if len(bars) <= period:
        return out
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i].high, bars[i].low, bars[i - 1].close
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    prev = sum(trs[:period]) / period
    out[period] = prev
    for i in range(period, len(trs)):
        prev = (prev * (period - 1) + trs[i]) / period
        out[i + 1] = prev
    return out


def bollinger(values: list[float], period: int = 20, num_std: float = 2.0):
    mid = sma(values, period)
    upper: list[float | None] = []
    lower: list[float | None] = []
    for i in range(len(values)):
        m = mid[i]
        if m is None:
            upper.append(None)
            lower.append(None)
            continue
        window = values[i - period + 1 : i + 1]
        var = sum((x - m) ** 2 for x in window) / period
        sd = var**0.5
        upper.append(m + num_std * sd)
        lower.append(m - num_std * sd)
    return upper, mid, lower


def parabolic_sar(bars, af_start: float = 0.02, af_step: float = 0.02, af_max: float = 0.2):
    """Parabolic SAR. Returns (sar_values, trend) with trend 1=uptrend, -1=downtrend."""
    n = len(bars)
    sar = [None] * n
    trend = [0] * n
    if n < 3:
        return sar, trend
    down = bars[1].close < bars[0].close
    ep = bars[0].low if down else bars[0].high      # extreme point
    s = bars[0].high if down else bars[0].low        # SAR value
    af = af_start
    for i in range(1, n):
        h, l = bars[i].high, bars[i].low
        prev_h, prev_l = bars[i - 1].high, bars[i - 1].low
        if down:
            s = s + af * (ep - s)
            s = max(s, prev_h, bars[i - 2].high) if i >= 2 else max(s, prev_h)
            if h > s:                                   # reversal up
                down = False
                s = ep
                ep = h
                af = af_start
            elif l < ep:
                ep = l
                af = min(af + af_step, af_max)
        else:
            s = s + af * (ep - s)
            s = min(s, prev_l, bars[i - 2].low) if i >= 2 else min(s, prev_l)
            if l < s:                                   # reversal down
                down = True
                s = ep
                ep = l
                af = af_start
            elif h > ep:
                ep = h
                af = min(af + af_step, af_max)
        sar[i] = round(s, 6)
        trend[i] = -1 if down else 1
    return sar, trend


def supertrend(bars, period: int = 10, mult: float = 3.0):
    """Supertrend (ATR-based). Returns (line, direction), direction 1=up, -1=down."""
    n = len(bars)
    atr_v = atr(bars, period)
    line = [None] * n
    direction = [1] * n
    upper_band, lower_band = [None] * n, [None] * n
    for i in range(n):
        a = atr_v[i]
        if a is None:
            continue
        hl2 = (bars[i].high + bars[i].low) / 2
        bu, bl = hl2 + mult * a, hl2 - mult * a
        if upper_band[i - 1] is not None:
            bu = bu if bu < upper_band[i - 1] or bars[i - 1].close > upper_band[i - 1] else upper_band[i - 1]
            bl = bl if bl > lower_band[i - 1] or bars[i - 1].close < lower_band[i - 1] else lower_band[i - 1]
        upper_band[i], lower_band[i] = bu, bl
    st, dir_ = None, 1
    for i in range(n):
        if upper_band[i] is None:
            continue
        c = bars[i].close
        if st is None:
            st = lower_band[i]
        if dir_ == 1:
            st = lower_band[i]
            if c < st:
                dir_, st = -1, upper_band[i]
        else:
            st = upper_band[i]
            if c > st:
                dir_, st = 1, lower_band[i]
        line[i] = round(st, 6)
        direction[i] = dir_
    return line, direction


def volume_ma(bars, period: int = 10):
    return sma([b.volume for b in bars], period)


def snapshot(bars, idx: int) -> dict:
    """A compact feature snapshot at bar index `idx` for agents/strategies."""
    return snapshot_pre(precompute(bars), bars, idx)


def precompute(bars) -> dict:
    """Compute every indicator series once (O(n)) so per-bar lookups are O(1)."""
    c = closes(bars)
    macd_line, sig, hist = macd(c)
    upper, mid, lower = bollinger(c)
    return {
        "c": c,
        "rsi": rsi(c, 14),
        "macd_hist": hist,
        "atr": atr(bars, 14),
        "sma50": sma(c, 50),
        "sma200": sma(c, 200),
        "bb_upper": upper,
        "bb_mid": mid,
        "bb_lower": lower,
    }


def snapshot_pre(pre: dict, bars, idx: int) -> dict:
    """Build the snapshot dict from precomputed series (fast, no look-ahead)."""
    c = pre["c"]
    price = c[idx]

    def pct(a, b):
        return None if a is None else round((a / b - 1) * 100, 2)

    rsi_v = pre["rsi"][idx]
    hist_v = pre["macd_hist"][idx]
    atr_v = pre["atr"][idx]
    s50 = pre["sma50"][idx]
    s200 = pre["sma200"][idx]
    up, lo = pre["bb_upper"][idx], pre["bb_lower"][idx]

    return {
        "date": bars[idx].date,
        "price": round(price, 2),
        "rsi14": round(rsi_v, 1) if rsi_v is not None else None,
        "macd_hist": round(hist_v, 3) if hist_v is not None else None,
        "atr14_pct": round(atr_v / price * 100, 2) if atr_v else None,
        "sma50_dist_pct": pct(s50, price) if s50 else None,
        "sma200_dist_pct": pct(s200, price) if s200 else None,
        "bb_pos": (
            round((price - lo) / (up - lo), 2)
            if lo and up and up != lo
            else None
        ),
        "ret_20d_pct": round((price / c[idx - 20] - 1) * 100, 2) if idx >= 20 else None,
        "ret_60d_pct": round((price / c[idx - 60] - 1) * 100, 2) if idx >= 60 else None,
    }
