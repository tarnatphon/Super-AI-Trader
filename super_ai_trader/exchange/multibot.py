"""Multi-coin paper grid manager.

Runs several live paper grid sessions at once (one per coin), each with its
own real price feed, regime pause, trailing/exit logic, and alert feed.

PAPER ONLY — no real orders and no keys are used here. Real (guarded) trading
stays behind the safety wall in live_trading.py.
"""
from __future__ import annotations

import threading
import time

from ..grid.engine import GridConfig
from .connector import ExchangeConnector
from .live_session import LiveSession


class MultiGrid:
    def __init__(self, exchange: str = "binance", poll_seconds: float = 8.0,
                 timeframe: str = "1h"):
        self.exchange = exchange
        self.poll_seconds = poll_seconds
        self.timeframe = timeframe
        self.sessions: dict[str, LiveSession] = {}
        self.running = False
        self._lock = threading.Lock()

    def start(self, coins: list[str], investment: float = 1000.0,
              range_pct: float = 12.0, grids: int = 25,
              range_pct_map: dict | None = None) -> dict:
        """Start (or restart) paper grids for the given coins. Non-blocking."""
        self.stop()  # clear any previous set first
        range_pct_map = range_pct_map or {}
        started = []
        for coin in coins:
            sym = f"{coin}/USDT"
            conn = ExchangeConnector(self.exchange, paper=True, paper_usdt=investment)
            try:
                ref = conn.price(sym)
            except Exception as e:  # network/ccxt issues
                started.append({"coin": coin, "ok": False, "error": str(e)})
                continue
            rp = range_pct_map.get(coin, range_pct)
            cfg = GridConfig(
                symbol=sym,
                lower=ref * (1 - rp / 100),
                upper=ref * (1 + rp / 100),
                grids=grids, mode="geometric", investment=investment,
                fee_pct=0.1, range_pct=rp,
                stop_loss_price=ref * (1 - rp * 2 / 100),
                take_profit_price=ref * (1 + rp * 2 / 100),
            )
            sess = LiveSession(conn, cfg, poll_seconds=self.poll_seconds,
                               timeframe=self.timeframe)
            try:
                sess.start()
            except Exception as e:
                started.append({"coin": coin, "ok": False, "error": str(e)})
                continue
            with self._lock:
                self.sessions[coin] = sess
            started.append({"coin": coin, "ok": True, "price": round(ref, 6)})
        self.running = bool(self.sessions)
        return {"ok": self.running, "started": started, "count": len(self.sessions)}

    def stop(self) -> dict:
        from .shutdown import stop_all
        with self._lock:
            store = {"live": None, "replay": None}
            sessions = list(self.sessions.values())
        report = {"stopped": 0, "safe": True}
        for sess in sessions:
            try:
                sess.stop()
                sess.runner.shutdown()
                report["stopped"] += 1
            except Exception:
                report["safe"] = False
        # cancel paper orders on each connector
        for sess in sessions:
            try:
                sess.conn.cancel_all_open_orders(sess.cfg.symbol)
            except Exception:
                pass
        self.sessions.clear()
        self.running = False
        return report

    def overview(self) -> dict:
        """Per-coin snapshot for the dashboard."""
        with self._lock:
            coins = list(self.sessions.keys())
        rows = []
        for coin in coins:
            sess = self.sessions[coin]
            try:
                st = sess.status()
                rows.append({
                    "coin": coin,
                    "price": st.get("price"),
                    "roi_pct": st.get("roi_pct"),
                    "pnl": st.get("pnl"),
                    "buys": st.get("matched_buys"),
                    "sells": st.get("matched_sells"),
                    "round_trips": st.get("round_trips"),
                    "paused": st.get("paused"),
                    "regime": (st.get("regime") or {}).get("status"),
                    "trail": (st.get("trail") or {}).get("state"),
                    "running": st.get("running"),
                    "events": st.get("events", [])[-6:],
                })
            except Exception:
                continue
        return {"running": self.running, "count": len(rows), "coins": rows}

    def summary(self) -> dict:
        ov = self.overview()
        coins = ov["coins"]
        total_pnl = round(sum(c.get("pnl") or 0 for c in coins), 2)
        total_inv = 0.0
        for c in coins:
            sess = self.sessions.get(c["coin"])
            if sess:
                try:
                    total_inv += float(sess.cfg.investment)
                except Exception:
                    pass
        total_rt = sum(c.get("round_trips") or 0 for c in coins)
        total_buys = sum(c.get("buys") or 0 for c in coins)
        total_sells = sum(c.get("sells") or 0 for c in coins)
        paused = [c["coin"] for c in coins if c.get("paused")]
        active = [c["coin"] for c in coins if not c.get("paused") and c.get("running")]
        all_events = []
        for c in coins:
            for e in (c.get("events") or []):
                all_events.append({"coin": c["coin"], **e})
        all_events.sort(key=lambda e: e.get("ts", 0))
        return {
            "running": ov["running"],
            "count": ov["count"],
            "total_pnl": total_pnl,
            "total_pnl_pct": round(total_pnl / total_inv * 100, 2) if total_inv else 0.0,
            "total_round_trips": total_rt,
            "total_buys": total_buys,
            "total_sells": total_sells,
            "paused_coins": paused,
            "active_coins": active,
            "recent_events": all_events[-15:],
        }



# One shared manager for the web session (paper).


def get_manager(exchange: str = "binance") -> MultiGrid:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = MultiGrid(exchange=exchange)
    return _MANAGER
