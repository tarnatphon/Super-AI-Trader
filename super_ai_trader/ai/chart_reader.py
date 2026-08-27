"""Read the whole chart clearly — every indicator from the trading screen.

Covers the indicator bar seen in the Binance screenshot:
  MA (moving average) · EMA (7/25/99) · BOLL (Bollinger bands) · SAR (Parabolic)
  · AVL (average volume) · SUPER (Supertrend) · VOL (volume) · MACD · RSI (6/12/24)

Each indicator returns a structured reading + a plain-language line, then an
overall summary combines them (with a vote), suitable for the AI command center.
"""
from __future__ import annotations

from ..data.indicators import (
    closes, sma, ema, rsi, macd, atr, bollinger,
    parabolic_sar, supertrend, volume_ma,
)


def _word(score):
    return "BULL (points up)" if score >= 1 else "BEAR (points down)" if score <= -1 else "NEUTRAL (mixed)"


def read_chart(bars) -> dict:
    c = closes(bars)
    i = len(bars) - 1
    price = c[i]
    out = {"price": round(price, 4), "indicators": {}, "score": 0, "lines": []}
    score = 0

    # --- MA / EMA (trend) ---
    ema7 = ema(c, 7); ema25 = ema(c, 25); ema99 = ema(c, 99)
    ma50 = sma(c, 50)
    e7, e25, e99 = ema7[i], ema25[i], ema99[i]
    ema_bull = e7 and e25 and e99 and e7 > e25 > e99
    ema_bear = e7 and e25 and e99 and e7 < e25 < e99
    ema_score = 1 if ema_bull else -1 if ema_bear else 0
    score += ema_score
    out["indicators"]["EMA_7_25_99"] = {
        "ema7": round(e7, 4) if e7 else None,
        "ema25": round(e25, 4) if e25 else None,
        "ema99": round(e99, 4) if e99 else None,
        "reading": _word(ema_score),
        "note": ("Ema7 above Ema25 above Ema99: clean uptrend" if ema_bull
                 else "Ema7 below Ema25 below Ema99: clean downtrend" if ema_bear
                 else "The three EMA lines are tangled: no clear trend"),
    }

    # --- Bollinger Bands ---
    up, mid, low = bollinger(c, 20, 2)
    if up[i] and low[i]:
        if price >= up[i]:
            bb_score = -1; note = "Price touched the top band — often stretched/overbought"
        elif price <= low[i]:
            bb_score = 1; note = "Price touched the bottom band — often stretched/oversold"
        elif price > mid[i]:
            bb_score = 1; note = "Price is in the upper half of the Bollinger band"
        else:
            bb_score = -1; note = "Price is in the lower half of the Bollinger band"
        score += bb_score
        out["indicators"]["BOLL"] = {
            "upper": round(up[i], 4), "middle": round(mid[i], 4), "lower": round(low[i], 4),
            "reading": _word(bb_score), "note": note,
        }

    # --- Parabolic SAR ---
    sar, trend = parabolic_sar(bars)
    if sar[i] is not None:
        sar_score = 1 if trend[i] == 1 else -1
        score += sar_score
        out["indicators"]["SAR"] = {
            "sar": sar[i], "reading": _word(sar_score),
            "note": "SAR dots are below price: uptrend" if sar_score == 1
                    else "SAR dots are above price: downtrend",
        }

    # --- Supertrend ---
    st, stdir = supertrend(bars, 10, 3.0)
    if st[i] is not None:
        st_score = 1 if stdir[i] == 1 else -1
        score += st_score
        out["indicators"]["SUPER"] = {
            "supertrend": st[i], "reading": _word(st_score),
            "note": "Supertrend flipped green (below price): up" if st_score == 1
                    else "Supertrend flipped red (above price): down",
        }

    # --- RSI (6/12/24 like the screenshot) ---
    r = {p: rsi(c, p)[i] for p in (6, 12, 24)}
    rsi_vals = [v for v in r.values() if v is not None]
    if rsi_vals:
        avg_rsi = sum(rsi_vals) / len(rsi_vals)
        if avg_rsi > 70:
            rsi_score = -1; label = "overbought (above 70)"
        elif avg_rsi < 30:
            rsi_score = 1; label = "oversold (below 30)"
        elif avg_rsi > 55:
            rsi_score = 1; label = "strong but not extreme"
        elif avg_rsi < 45:
            rsi_score = -1; label = "weak but not extreme"
        else:
            rsi_score = 0; label = "neutral mid-range"
        score += rsi_score
        out["indicators"]["RSI"] = {
            "rsi6": round(r[6], 1) if r[6] else None,
            "rsi12": round(r[12], 1) if r[12] else None,
            "rsi24": round(r[24], 1) if r[24] else None,
            "reading": _word(rsi_score), "note": f"RSI average {avg_rsi:.0f}: {label}",
        }

    # --- MACD ---
    mline, sig, hist = macd(c)
    if hist[i] is not None:
        prev = hist[i - 1] if i > 0 and hist[i - 1] is not None else hist[i]
        growing = hist[i] > prev
        if hist[i] > 0 and growing:
            macd_score, macd_note = 1, "MACD histogram above zero and rising: bullish momentum"
        elif hist[i] < 0 and not growing:
            macd_score, macd_note = -1, "MACD histogram below zero and falling: bearish momentum"
        else:
            macd_score, macd_note = 0, "MACD momentum is mixed"
        score += macd_score
        out["indicators"]["MACD"] = {
            "hist": round(hist[i], 4), "reading": _word(macd_score), "note": macd_note,
        }

    # --- Volume + AVL (average volume) ---
    vma = volume_ma(bars, 10)
    vol = bars[i].volume
    if vma[i] is not None:
        ratio = vol / vma[i] if vma[i] else 1.0
        up_bar = c[i] >= c[i - 1]
        vol_score = 1 if (ratio > 1.2 and up_bar) else -1 if (ratio > 1.2 and not up_bar) else 0
        score += vol_score
        out["indicators"]["VOL_AVL"] = {
            "volume": round(vol, 1), "avg_volume_10": round(vma[i], 1),
            "volume_ratio": round(ratio, 2), "reading": _word(vol_score),
            "note": (f"Volume is {ratio:.1f}x the average on a GREEN bar: buyers active"
                     if (ratio > 1.2 and up_bar) else
                     f"Volume is {ratio:.1f}x average on a RED bar: sellers active"
                     if ratio > 1.2 else
                     f"Volume {ratio:.1f}x average: normal / quiet ({'up' if up_bar else 'down'} bar)"),
        }

    out["score"] = score
    if score >= 3:
        out["verdict"] = "BUY bias"
    elif score <= -3:
        out["verdict"] = "SELL bias"
    else:
        out["verdict"] = "WAIT / HOLD"

    # Plain-language lines.
    for name, d in out["indicators"].items():
        out["lines"].append(f"{name}: {d['note']} → {d['reading']}")
    return out


def explain_chart(reading: dict) -> str:
    lines = [f"Price is {reading['price']}."]
    lines += reading["lines"]
    lines.append(f"Put together, the {len(reading['indicators'])} indicators score "
                 f"{reading['score']:+d}, which is a **{reading['verdict']}**.")
    return " ".join(lines)
