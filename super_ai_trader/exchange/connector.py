"""Exchange connector over CCXT.

- PUBLIC data (prices, OHLCV) needs no API key.
- PRIVATE actions (orders, balances) use a trade-only key from the local vault.
- PAPER mode simulates fills with live prices but never sends an order.
- The AI is local; this module only uses the machine's internet to reach the
  exchange. Nothing is sent to any AI cloud.

CCXT is imported lazily so the rest of the app works with zero dependencies.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..data.market import Bar


@dataclass
class Order:
    id: str
    side: str           # "buy" | "sell"
    symbol: str
    amount: float
    price: float
    filled: bool = False
    ts: float = 0.0


class ExchangeConnector:
    """Uniform interface for Binance, Gate.io, and any CCXT venue."""

    def __init__(self, exchange_id: str = "binance", paper: bool = True,
                 api_key: str | None = None, api_secret: str | None = None,
                 paper_usdt: float = 10_000.0):
        self.exchange_id = exchange_id
        self.paper = paper
        self._ccxt = None
        self.ex = None
        self.paper_usdt = paper_usdt
        self.base_held = 0.0
        self.orders: list[Order] = []
        self.fills: list[Order] = []
        self._oid = 0
        if not paper and (api_key and api_secret):
            import ccxt  # lazy
            klass = getattr(ccxt, exchange_id)
            self.ex = klass({
                "apiKey": api_key, "secret": api_secret,
                "enableRateLimit": True, "options": {"defaultType": "spot"},
            })
        elif not paper:
            raise ValueError("live mode requires api_key and api_secret (trade-only)")

    # ---- public market data (works in paper mode too, via ccxt) ----------- #
    def _pub(self):
        if self._ccxt is None:
            import ccxt
            klass = getattr(ccxt, self.exchange_id)
            self._ccxt = klass({"enableRateLimit": True})
        return self._ccxt

    def price(self, symbol: str) -> float:
        t = self._pub().fetch_ticker(symbol)
        return float(t["last"] or t["close"])

    def ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 500) -> list[Bar]:
        raw = self._pub().fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        bars = []
        for ts, o, h, low, c, v in raw:
            bars.append(Bar(date=str(ts), open=o, high=h, low=low, close=c, volume=v or 0.0))
        return bars

    # ---- orders ----------------------------------------------------------- #
    def _new_id(self) -> str:
        self._oid += 1
        return f"paper-{self._oid}" if self.paper else None

    def place_limit_buy(self, symbol: str, amount: float, price: float) -> Order:
        if self.paper:
            order = Order(id=self._new_id(), side="buy", symbol=symbol,
                          amount=amount, price=price, ts=time.time())
            self.orders.append(order)
            return order
        res = self.ex.create_limit_buy_order(symbol, amount, price)
        return Order(id=str(res.get("id")), side="buy", symbol=symbol,
                     amount=amount, price=price, ts=time.time())

    def place_limit_sell(self, symbol: str, amount: float, price: float) -> Order:
        if self.paper:
            order = Order(id=self._new_id(), side="sell", symbol=symbol,
                          amount=amount, price=price, ts=time.time())
            self.orders.append(order)
            return order
        res = self.ex.create_limit_sell_order(symbol, amount, price)
        return Order(id=str(res.get("id")), side="sell", symbol=symbol,
                     amount=amount, price=price, ts=time.time())

    def cancel(self, order: Order):
        if not self.paper and self.ex and order.id:
            try:
                self.ex.cancel_order(order.id, order.symbol)
            except Exception:
                pass
        if order in self.orders:
            self.orders.remove(order)

    # ---- paper fill simulation from a live price tick -------------------- #
    def tick_paper(self, symbol: str, price: float) -> list[Order]:
        """Fill any resting paper orders crossed by `price`. Returns filled orders."""
        if not self.paper:
            return []
        filled_now = []
        for o in list(self.orders):
            if o.symbol == "buy" and price <= o.price and not o.filled:
                cost = o.amount * o.price
                if cost <= self.paper_usdt:
                    self.paper_usdt -= cost
                    self.base_held += o.amount
                    o.filled = True
                    self.fills.append(o)
                    self.orders.remove(o)
                    filled_now.append(o)
            elif o.symbol == "sell" and price >= o.price and not o.filled:
                if o.amount <= self.base_held + 1e-12:
                    self.paper_usdt += o.amount * o.price
                    self.base_held -= o.amount
                    o.filled = True
                    self.fills.append(o)
                    self.orders.remove(o)
                    filled_now.append(o)
        return filled_now

    def equity(self, price: float) -> float:
        if self.paper:
            return self.paper_usdt + self.base_held * price
        bal = self.ex.fetch_balance()
        usdt = float(bal.get("USDT", {}).get("free", 0) or 0)
        base = 0.0  # caller can add held base value
        return usdt + base
