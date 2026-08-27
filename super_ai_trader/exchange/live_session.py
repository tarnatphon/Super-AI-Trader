"""A live grid trading session with real-time results.

- Uses REAL exchange prices (Binance/Gate.io via ccxt) for the price feed.
- PAPER mode by default: fills are simulated from live prices — no orders sent,
  no keys needed. (Live trading with a trade-only key is the later step.)
- Streams price, equity/PnL, matched buys/sells and the live profit curve while
  the bot runs. A Preview can show the past result over real historical candles.

The session runs a background poller thread; `step()` is one poll (used directly
in tests and for replay).
"""
from __future__ import annotations

import threading
import time

from ..grid.engine import GridConfig
from .grid_runner import LiveGridRunner


class LiveSession:
    def __init__(self, conn, cfg: GridConfig, poll_seconds: float = 5.0,
                 behavior_fn=None):
        self.conn = conn
        self.cfg = cfg
        self.runner = LiveGridRunner(conn, cfg)
        self.poll_seconds = poll_seconds
        self.behavior_fn = behavior_fn
        self.running = False
        self.stopped = False
        self.thread = None
        self.ticks: list[dict] = []        # price + equity over time
        self.fill_log: list[dict] = []     # every matched buy/sell
        self.setup_info: dict = {}
        self.last_behavior: dict | None = None
        self.killed: dict | None = None
        self.start_price = None
        self._seen_fills = 0
        self._lock = threading.Lock()

    def start(self):
        self.setup_info = self.runner.setup()
        self.start_price = self.setup_info.get("price")
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running and not self.stopped:
            try:
                self.step()
            except Exception as e:  # never die on a transient API error
                self.ticks.append({"error": str(e)})
            time.sleep(self.poll_seconds)

    def step(self) -> dict:
        """One live poll: fetch real price, match orders, record results."""
        price = self.conn.price(self.cfg.symbol)
        before = len(self.conn.fills)
        info = self.runner.cycle_once(price)
        # record new fills
        for o in self.conn.fills[self._seen_fills:]:
            self.fill_log.append({"side": o.side, "price": round(o.price, 6),
                                  "amount": round(o.amount, 8), "ts": time.time()})
        self._seen_fills = len(self.conn.fills)
        equity = self.cfg.investment
        try:
            equity = self.conn.equity(price)
        except Exception:
            pass
        with self._lock:
            self.ticks.append({"t": time.time(), "price": round(price, 6),
                               "equity": round(equity, 2) if equity else None})
        if info.get("killed"):
            self.killed = info
            self.stop()
        # behavior (order book) — best effort
        if self.behavior_fn and len(self.ticks) % 6 == 0:
            try:
                self.last_behavior = self.behavior_fn()
            except Exception:
                self.last_behavior = None
        return info

    def stop(self):
        self.running = False
        self.stopped = True
        try:
            self.runner.shutdown()
        except Exception:
            pass

    def status(self) -> dict:
        with self._lock:
            ticks = list(self.ticks)
            fills = list(self.fill_log)
        price = ticks[-1]["price"] if ticks else self.start_price
        equity = ticks[-1].get("equity") if ticks else self.cfg.investment
        pnl = (equity - self.cfg.investment) if equity else 0.0
        roi = (pnl / self.cfg.investment * 100) if equity else 0.0
        buys = sum(1 for f in fills if f["side"] == "buy")
        sells = sum(1 for f in fills if f["side"] == "sell")
        return {
            "running": self.running and not self.stopped,
            "symbol": self.cfg.symbol,
            "mode": "LIVE (paper orders, real prices)",
            "price": price,
            "investment": self.cfg.investment,
            "equity": round(equity, 2) if equity else None,
            "pnl": round(pnl, 2),
            "roi_pct": round(roi, 2),
            "matched_buys": buys,
            "matched_sells": sells,
            "round_trips": self.runner.round_trips,
            "open_orders": len(self.runner.orders),
            "lower": round(self.cfg.lower, 6),
            "upper": round(self.cfg.upper, 6),
            "grids": self.cfg.grids,
            "grid_mode": self.cfg.mode,
            "killed": self.killed,
            "profit_curve": [t["equity"] for t in ticks if t.get("equity")],
            "price_curve": [t["price"] for t in ticks],
            "recent_fills": fills[-12:],
            "behavior": self.last_behavior,
            "poll_seconds": self.poll_seconds,
        }
