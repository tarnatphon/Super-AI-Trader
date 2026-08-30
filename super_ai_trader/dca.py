"""DCA (Dollar-Cost Averaging) — buy a fixed amount on a fixed schedule.

This is the #1 beginner/passive strategy across all the popular bots
(Pionex, 3Commas, Coinrule): instead of timing the market, you buy a
small fixed USD amount at regular intervals. Works in PAPER mode against
live prices here (no keys); real orders go through the guarded live path.

A DCA plan runs inside the same MultiGrid manager tick (checked on each
poll) so it needs no extra timers and benefits from the same kill-switch.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class DCAPlan:
    symbol: str                 # e.g. "BTC/USDT"
    coin: str                   # "BTC"
    usd_amount: float           # fixed buy per interval (practice USDT)
    interval_seconds: float = 24 * 3600  # daily by default
    max_buys: int = 0           # 0 = unlimited (until stopped)
    buys_done: int = 0
    total_spent: float = 0.0
    base_acquired: float = 0.0
    started_at: float = field(default_factory=time.time)
    last_buy_at: float = 0.0
    history: list = field(default_factory=list)
    running: bool = True

    def due(self, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        if not self.running:
            return False
        if self.max_buys and self.buys_done >= self.max_buys:
            self.running = False
            return False
        if self.last_buy_at == 0.0:
            return True   # buy on start
        return (now - self.last_buy_at) >= self.interval_seconds

    def execute_buy(self, price: float, now: float | None = None) -> dict:
        """Record a simulated purchase at the current live price."""
        now = now if now is not None else time.time()
        qty = self.usd_amount / price if price else 0.0
        self.buys_done += 1
        self.total_spent += self.usd_amount
        self.base_acquired += qty
        self.last_buy_at = now
        fill = {"ts": now, "coin": self.coin, "price": round(price, 6),
                "usd": self.usd_amount, "qty": round(qty, 8)}
        self.history.append(fill)
        if self.max_buys and self.buys_done >= self.max_buys:
            self.running = False
        return fill

    def average_entry(self) -> float:
        return (self.total_spent / self.base_acquired) if self.base_acquired else 0.0

    def snapshot(self, price: float) -> dict:
        value = self.base_acquired * price if price else 0.0
        return {
            "coin": self.coin,
            "running": self.running,
            "usd_per_buy": self.usd_amount,
            "interval_hours": round(self.interval_seconds / 3600, 1),
            "buys_done": self.buys_done,
            "max_buys": self.max_buys,
            "total_spent": round(self.total_spent, 2),
            "base_acquired": round(self.base_acquired, 8),
            "avg_entry": round(self.average_entry(), 6),
            "current_value": round(value, 2),
            "pnl": round(value - self.total_spent, 2),
            "next_buy_in": round(max(0, (self.last_buy_at + self.interval_seconds - time.time())), 0),
        }
