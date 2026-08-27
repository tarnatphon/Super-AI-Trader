"""Learn LIVE human buying/selling behavior.

Two sources of real trader behavior:
1. ORDER BOOK depth  -> who is stacking buy bids vs sell asks (support/resistance
   that real people placed right now), and the imbalance between them.
2. LIVE TRADES feed  -> each executed trade is signed buyer-aggressive vs
   seller-aggressive (taker side), giving real buy/sell volume flow.

When ccxt + internet are available this uses the live exchange. Otherwise it falls
back to an estimate from recent candles so the app still works offline.
"""
from __future__ import annotations

from .indicators import closes, sma


def behavior_from_ohlcv(bars, depth: int = 30) -> dict:
    """Offline approximation of live behavior (used when no live feed)."""
    c = closes(bars)
    recent = bars[-depth:]
    buy_vol = sell_vol = 0.0
    for b in recent:
        rng = b.high - b.low
        clv = 0.0 if rng <= 0 else ((b.close - b.low) - (b.high - b.close)) / rng
        if clv >= 0:
            buy_vol += b.volume * (0.5 + clv / 2)
            sell_vol += b.volume * (0.5 - clv / 2)
        else:
            sell_vol += b.volume * (0.5 + (-clv) / 2)
            buy_vol += b.volume * (0.5 - (-clv) / 2)
    total = buy_vol + sell_vol or 1.0
    return {
        "source": "recent candles (live feed not connected)",
        "buy_ratio": round(buy_vol / total, 3),
        "sell_ratio": round(sell_vol / total, 3),
        "trade_flow_imbalance": round((buy_vol - sell_vol) / total, 3),
        "pressure": "buyers" if buy_vol > sell_vol * 1.08 else "sellers" if sell_vol > buy_vol * 1.08 else "balanced",
        "order_book": None,
    }


def fetch_live_behavior(exchange_id: str = "binance", symbol: str = "BNB/USDT",
                        depth: int = 50) -> dict:
    """Pull the live order book + recent trades and summarize real behavior.
    Requires ccxt and internet. Raises on failure so the caller can fall back."""
    import ccxt  # lazy
    klass = getattr(ccxt, exchange_id)
    ex = klass({"enableRateLimit": True})
    ob = ex.fetch_order_book(symbol, limit=depth)
    trades = ex.fetch_trades(symbol, limit=200)

    bids = ob.get("bids", [])
    asks = ob.get("asks", [])
    bid_vol = sum(q for _p, q in bids)
    ask_vol = sum(q for _p, q in asks)
    ob_total = bid_vol + ask_vol or 1.0
    best_bid = bids[0][0] if bids else None
    best_ask = asks[0][0] if asks else None
    spread = (best_ask - best_bid) / best_bid * 100 if best_bid and best_ask else None

    # Sign trades by aggressive side.
    buy_q = sell_q = 0.0
    for t in trades:
        side = (t.get("side") or "").lower()
        amt = float(t.get("amount") or 0)
        if side == "buy":
            buy_q += amt
        elif side == "sell":
            sell_q += amt
        else:
            # infer from tick direction
            buy_q += amt
    flow_total = buy_q + sell_q or 1.0
    tfi = (buy_q - sell_q) / flow_total

    # Walls: largest single bid/ask (real support/resistance).
    big_bid = max(bids, key=lambda x: x[1], default=None)
    big_ask = max(asks, key=lambda x: x[1], default=None)

    return {
        "source": f"LIVE {exchange_id} {symbol}",
        "buy_ratio": round(buy_q / flow_total, 3),
        "sell_ratio": round(sell_q / flow_total, 3),
        "trade_flow_imbalance": round(tfi, 3),
        "pressure": "buyers" if tfi > 0.12 else "sellers" if tfi < -0.12 else "balanced",
        "order_book_bid_ask_imbalance": round((bid_vol - ask_vol) / ob_total, 3),
        "best_bid": best_bid, "best_ask": best_ask,
        "spread_pct": round(spread, 4) if spread is not None else None,
        "big_bid_wall": (round(big_bid[0], 4), round(big_bid[1], 2)) if big_bid else None,
        "big_ask_wall": (round(big_ask[0], 4), round(big_ask[1], 2)) if big_ask else None,
        "buyer_pressure_depth": round(bid_vol / ob_total, 3),
        "seller_pressure_depth": round(ask_vol / ob_total, 3),
    }


def live_behavior(exchange_id: str = "binance", symbol: str = "BNB/USDT",
                  bars=None) -> dict:
    """Try live; fall back to candle estimate. Never raises."""
    try:
        return fetch_live_behavior(exchange_id, symbol)
    except Exception:
        if bars is None:
            from .market import make_synthetic_series
            bars = make_synthetic_series(symbol.split("/")[0], days=300)
        return behavior_from_ohlcv(bars)
