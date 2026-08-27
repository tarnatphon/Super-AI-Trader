"""Run a real or paper spot-grid against live exchange prices.

This connects to Binance/Gate.io over the internet (public prices; trade-only
keys for live). The AI brain remains local. In paper mode, fills are simulated
from live price ticks — no order ever leaves the machine.

Safety: a kill switch (stop_loss / take_profit) cancels all orders and exits.
"""
from __future__ import annotations

import time

from .connector import ExchangeConnector, Order
from ..grid.engine import GridConfig, grid_lines


class LiveGridRunner:
    def __init__(self, conn: ExchangeConnector, cfg: GridConfig):
        self.conn = conn
        self.cfg = cfg
        self.lines: list[float] = []
        self.orders: list[Order] = []
        self.round_trips = 0
        self.running = False

    def setup(self):
        price = self.conn.price(self.cfg.symbol)
        self.cfg.lower = self.cfg.lower or price * (1 - self.cfg.range_pct / 100)
        self.cfg.upper = self.cfg.upper or price * (1 + self.cfg.range_pct / 100)
        self.lines = grid_lines(self.cfg, price)
        quote_per_buy = self.cfg.investment / len(self.lines[:-1])
        # Place buy ladders below price and one sell above each buy.
        start_price = price
        for i, p in enumerate(self.lines[:-1]):
            if p < start_price:
                amt = quote_per_buy / p
                o = self.conn.place_limit_buy(self.cfg.symbol, amt, p)
                self.orders.append(o)
        return {"price": price, "lines": self.lines, "buy_orders": len(self.orders)}

    def shutdown(self):
        for o in list(self.orders):
            self.conn.cancel(o)
        self.orders = []
        self.running = False

    def cycle_once(self, price: float) -> dict:
        """One poll: simulate/collect fills; on a buy fill, place its sell one
        grid step up; on a sell fill, place a fresh buy one step down."""
        filled = self.conn.tick_paper(self.cfg.symbol, price) if self.conn.paper else []
        info = {"price": price, "new_fills": len(filled), "killed": False}
        for o in filled:
            if o.side == "buy":
                # find the grid line just above this buy
                above = [p for p in self.lines if p > o.price]
                if above:
                    sell_px = above[0]
                    so = self.conn.place_limit_sell(self.cfg.symbol, o.amount, sell_px)
                    self.orders.append(so)
            elif o.side == "sell":
                self.round_trips += 1
                below = [p for p in self.lines if p < o.price]
                if below:
                    buy_px = below[-1]
                    quote = o.amount * o.price
                    bo = self.conn.place_limit_buy(self.cfg.symbol, quote / buy_px, buy_px)
                    self.orders.append(bo)
        info["round_trips"] = self.round_trips

        # Kill switch.
        if self.cfg.stop_loss_price and price <= self.cfg.stop_loss_price:
            self.shutdown(); info["killed"] = True; info["reason"] = "stop-loss"
        elif self.cfg.take_profit_price and price >= self.cfg.take_profit_price:
            self.shutdown(); info["killed"] = True; info["reason"] = "take-profit"
        return info

    def run(self, poll_seconds: float = 15.0, max_loops: int | None = None, log=print):
        self.running = True
        s = self.setup()
        log(f"Grid armed on {self.cfg.symbol} at price {s['price']:.2f}; "
            f"{len(s['lines'])} lines {self.cfg.lower:.2f}-{self.cfg.upper:.2f} "
            f"({'PAPER' if self.conn.paper else 'LIVE'})")
        loops = 0
        while self.running:
            try:
                price = self.conn.price(self.cfg.symbol)
                info = self.cycle_once(price)
                eq = self.conn.equity(price) if self.conn.paper else None
                log(f"price {price:.2f} | fills {info['new_fills']} | "
                    f"round-trips {self.round_trips} | "
                    f"{'equity %.2f' % eq if eq is not None else 'live'}")
                if info["killed"]:
                    log(f"Kill switch: {info['reason']} — orders cancelled.")
                    break
            except Exception as e:  # never let a transient API error crash the bot
                log(f"poll error: {e}")
            loops += 1
            if max_loops and loops >= max_loops:
                break
            time.sleep(poll_seconds)
        return {"round_trips": self.round_trips}
