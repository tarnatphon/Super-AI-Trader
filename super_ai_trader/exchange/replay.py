"""Time-machine replay: run the live grid engine over historical candles.

The exact same LiveSession/grid logic used for live trading, but the price feed
is a cursor walking forward through past bars. Each step advances one candle, so
you can watch buys/sells fill and the equity (profit) curve build up over time —
safe, no orders, no keys. Works on real exchange candles (ccxt) or built-in data.
"""
from __future__ import annotations

from .connector import ExchangeConnector
from .live_session import LiveSession


class ReplayConnector(ExchangeConnector):
    """Paper connector whose 'live' price is the next historical candle."""

    def __init__(self, bars, exchange_id: str = "binance", paper_usdt: float = 10_000.0):
        super().__init__(exchange_id, paper=True, paper_usdt=paper_usdt)
        self.bars = bars
        self.cursor = 0

    def price(self, symbol: str) -> float:
        i = min(self.cursor, len(self.bars) - 1)
        return self.bars[i].close

    def ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 500):
        return self.bars[-limit:]

    @property
    def total(self) -> int:
        return len(self.bars)


class ReplaySession(LiveSession):
    """Advances one historical candle per step."""

    def __init__(self, conn: ReplayConnector, cfg, **kw):
        super().__init__(conn, cfg, poll_seconds=0.0, **kw)
        self.finished = False

    def step(self) -> dict:
        if self.conn.cursor >= self.conn.total - 1:
            self.finished = True
            self.running = False
            return {"finished": True}
        self.conn.cursor += 1
        info = super().step()
        if self.conn.cursor >= self.conn.total - 1:
            self.finished = True
            self.running = False
            info["finished"] = True
        return info

    def status(self) -> dict:
        s = super().status()
        s["mode"] = "REPLAY (historical candles)"
        s["bar"] = self.conn.cursor
        s["total_bars"] = self.conn.total
        s["progress_pct"] = round(100 * self.conn.cursor / max(1, self.conn.total - 1), 1)
        s["finished"] = self.finished
        s["running"] = not self.finished
        return s
