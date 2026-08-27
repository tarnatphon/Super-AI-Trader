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


def snapshot(bars, idx: int) -> dict:
    """A compact feature snapshot at bar index `idx` for agents/strategies."""
    c = closes(bars)
    price = c[idx]
    rsi14 = rsi(c, 14)
    macd_line, sig, hist = macd(c)
    atr14 = atr(bars, 14)
    sma50 = sma(c, 50)
    sma200 = sma(c, 200)
    upper, mid, lower = bollinger(c)

    def pct(a, b):
        return None if a is None else round((a / b - 1) * 100, 2)

    return {
        "date": bars[idx].date,
        "price": round(price, 2),
        "rsi14": round(rsi14[idx], 1) if rsi14[idx] is not None else None,
        "macd_hist": round(hist[idx], 3) if hist[idx] is not None else None,
        "atr14_pct": round(atr14[idx] / price * 100, 2) if atr14[idx] else None,
        "sma50_dist_pct": pct(sma50[idx], price) if sma50[idx] else None,
        "sma200_dist_pct": pct(sma200[idx], price) if sma200[idx] else None,
        "bb_pos": (
            round((price - lower[idx]) / (upper[idx] - lower[idx]), 2)
            if lower[idx] and upper[idx] and upper[idx] != lower[idx]
            else None
        ),
        "ret_20d_pct": round((price / c[idx - 20] - 1) * 100, 2) if idx >= 20 else None,
        "ret_60d_pct": round((price / c[idx - 60] - 1) * 100, 2) if idx >= 60 else None,
    }
