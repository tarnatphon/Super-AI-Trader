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
        self.tuning: dict[str, dict] = {}   # per-coin last tuning result
        self.last_retune_day = None
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

    def retune_coin(self, coin: str) -> dict:
        """Re-learn the best trailing exit settings for one coin on recent
        market data. Returns a small report; best-effort (paper only)."""
        try:
            from ..learning.trailing import optimize_trailing
            opt = optimize_trailing(coin, days=700, real=False, quick=True)
            b = opt["best"]
            rec = {
                "coin": coin,
                "ts": time.time(),
                "trail_arm": b.get("arm_pct"),
                "trail_giveback": b.get("giveback_pct"),
                "score": b.get("score"),
                "note": f"arm {b.get('arm_pct')}%, give back {b.get('giveback_pct')}%",
            }
            with self._lock:
                self.tuning[coin] = rec
            return rec
        except Exception as e:  # noqa: BLE001
            return {"coin": coin, "error": str(e)}

    def auto_retune(self, coins: list[str] | None = None, force: bool = True) -> list:
        """Tune every running coin (or the supplied list).

        By default runs when forced; the scheduler calls it once per day
        (force=False) and records each coin's new settings to the journal.
        """
        targets = coins or list(self.sessions.keys())
        results = [self.retune_coin(c) for c in targets]
        # journal the tuning so it shows in History
        try:
            from ..journal import record
            for rec in results:
                if rec.get("note"):
                    record("tune", {
                        "coin": rec.get("coin"),
                        "trail_arm": rec.get("trail_arm"),
                        "trail_giveback": rec.get("trail_giveback"),
                        "note": rec.get("note"),
                        "forced": bool(force),
                    })
        except Exception:
            pass
        return results

    def maybe_daily_retune(self) -> dict:
        """Run auto-tune at most once per calendar day."""
        import datetime as _dt
        today = _dt.date.today().isoformat()
        if self.last_retune_day == today and self.tuning:
            return {"ran": False, "day": today}
        coins = list(self.sessions.keys())
        results = self.auto_retune(coins, force=False)
        self.last_retune_day = today
        try:
            from ..journal import record
            record("event", {"label": f"daily auto-tune ({len(results)} coin(s))",
                             "coins": coins})
        except Exception:
            pass
        return {"ran": True, "day": today, "results": results}

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
            "tuning": [self.tuning.get(c["coin"]) for c in coins if c["coin"] in self.tuning],
            "last_retune_day": self.last_retune_day,
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
_MANAGER: "MultiGrid | None" = None


def get_manager(exchange: str = "binance") -> MultiGrid:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = MultiGrid(exchange=exchange)
    return _MANAGER
