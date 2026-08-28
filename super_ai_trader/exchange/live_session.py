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
                 behavior_fn=None, timeframe: str = "1h"):
        self.conn = conn
        self.cfg = cfg
        self.timeframe = timeframe
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
        self.events: list[dict] = []          # human-readable alerts (newest last)
        self._seen_fills = 0
        self._regime_state = None
        self._trail_state = None
        self.killed: dict | None = None
        self.start_price = None
        self.regime: dict | None = None
        self._seen_fills = 0
        self._lock = threading.Lock()

    def _recent_bars(self, limit: int = 120):
        """Candles up to now — replay uses the cursor, live fetches from the exchange."""
        conn = self.conn
        if hasattr(conn, "bars") and hasattr(conn, "cursor"):
            return conn.bars[max(0, conn.cursor - limit):conn.cursor + 1]
        try:
            return conn.ohlcv(self.cfg.symbol, timeframe=self.timeframe, limit=limit)
        except Exception:
            return []

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

        # AI regime filter: pause buying in strong trends (protect the grid).
        try:
            from ..grid.regime import regime_gate
            bars = self._recent_bars()
            if len(bars) >= 40:
                gate = regime_gate(bars, self.cfg)
                self.regime = gate
                self.runner.set_paused(not gate["active"], price)
        except Exception:
            pass

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

        # --- human-readable alerts (the AI "telling you" what it did) ---
        self._emit_events(price, info)

        if info.get("killed"):
            self.killed = info
            self._push_event("🛑 Safety stop triggered — robot stopped all orders.",
                             "stop", "red")
            self.stop()
        # behavior (order book) — best effort
        if self.behavior_fn and len(self.ticks) % 6 == 0:
            try:
                self.last_behavior = self.behavior_fn()
            except Exception:
                self.last_behavior = None
        return info

    def _push_event(self, text: str, kind: str = "info", color: str = "muted"):
        with self._lock:
            self.events.append({"ts": time.time(), "text": text,
                                 "kind": kind, "color": color})
            self.events = self.events[-30:]  # keep a short feed

    def _emit_events(self, price: float, info: dict):
        """Detect meaningful changes and announce them (once per change)."""
        # Regime on/off transitions (announce pauses/resumes, including first).
        if self.regime is not None:
            st = self.regime.get("status")
            if st != self._regime_state:
                if not self.regime.get("active", True):
                    self._push_event(
                        f"⏸️ Grid PAUSED — {self.regime.get('reason','trend detected')}",
                        "regime_off", "amber")
                elif self._regime_state is not None and st in ("range",):
                    self._push_event("✅ Grid back ON — market in range again.",
                                     "regime_on", "green")
                self._regime_state = st
        # Trailing smart-exit state changes (lock profit).
        try:
            path = [t["price"] for t in self.ticks if t.get("price")]
            if len(path) >= 6:
                from ..grid.trailing_visual import simulate_trailing
                tr = simulate_trailing(path, arm_pct=5.0, giveback_pct=1.0)
                if tr["state"] != self._trail_state:
                    if tr["state"] == "holding" and self._trail_state in (None, "watching"):
                        self._push_event(
                            f"🟢 Trailing ON — runner up, holding for more (exit if it reverses).",
                            "trail_arm", "amber")
                    if tr["state"] == "locked":
                        self._push_event(
                            f"🔒 Smart exit LOCKED +{tr.get('locked_gain_pct')}% — profit banked.",
                            "trail_lock", "green")
                    self._trail_state = tr["state"]
        except Exception:
            pass
        # Round-trip completions (a sell matched = a small win collected).
        rt = self.runner.round_trips
        if rt > getattr(self, "_last_rt", 0):
            self._push_event(f"✅ Grid completed a buy→sell cycle ({rt} total).",
                             "roundtrip", "green")
        self._last_rt = rt

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
        equity = None
        try:
            equity = self.conn.equity(price)
        except Exception:
            equity = self.cfg.investment
        pnl = (equity - self.cfg.investment) if equity else 0.0
        roi = (pnl / self.cfg.investment * 100) if equity else 0.0

        # Trailing "smart exit" state from the live price path (watching/holding/locked).
        trail = None
        price_path = [t["price"] for t in ticks if t.get("price")]
        if len(price_path) >= 5:
            try:
                from ..grid.trailing_visual import simulate_trailing
                trail = simulate_trailing(price_path, arm_pct=5.0, giveback_pct=1.0)
                trail.pop("price", None)
                trail.pop("exit_line", None)
            except Exception:
                trail = None
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
            "paused": self.runner.pause_buys,
            "regime": self.regime,
            "trail": trail,
            "lower": round(self.cfg.lower, 6),
            "upper": round(self.cfg.upper, 6),
            "grids": self.cfg.grids,
            "grid_mode": self.cfg.mode,
            "killed": self.killed,
            "profit_curve": [t["equity"] for t in ticks if t.get("equity")],
            "price_curve": [t["price"] for t in ticks],
            "recent_fills": fills[-12:],
            "behavior": self.last_behavior,
            "events": list(self.events)[-12:],
            "poll_seconds": self.poll_seconds,
        }
