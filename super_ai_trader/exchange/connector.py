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


# App-friendly venue id -> ccxt exchange class name. Gate.io's ccxt class is
# `gate` (UI uses "gateio"); Bybit/OKX/KuCoin/Kraken map to their ccxt ids.
_CCXT_ID = {
    "binance": "binance",
    "gateio": "gate", "gate": "gate",
    "bybit": "bybit",
    "okx": "okx",
    "kucoin": "kucoin", "kucoinn": "kucoin",
    "kraken": "kraken",
}

# Venues offered in the UI (id -> display name).
VENUES = [
    ("binance", "Binance"),
    ("gateio", "Gate.io"),
    ("bybit", "Bybit"),
    ("okx", "OKX"),
    ("kucoin", "KuCoin"),
    ("kraken", "Kraken"),
]


def ccxt_id(exchange_id: str) -> str:
    return _CCXT_ID.get((exchange_id or "binance").lower(), exchange_id)


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
            klass = getattr(ccxt, ccxt_id(exchange_id))
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
            klass = getattr(ccxt, ccxt_id(self.exchange_id))
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

    def cancel_all_open_orders(self, symbol: str) -> int:
        """Cancel every open order for a symbol (used at startup reconcile and
        safe-stop). Paper orders are removed in memory; live exchange orders
        are cancelled via ccxt. Returns the count cancelled."""
        if not self.paper and self.ex is not None:
            try:
                open_orders = self.ex.fetch_open_orders(symbol)
                for o in open_orders:
                    try:
                        self.ex.cancel_order(o["id"], symbol)
                    except Exception:
                        pass
                return len(open_orders)
            except Exception:
                pass
        count = len(self.orders)
        for o in list(self.orders):
            if symbol is None or o.symbol == symbol:
                if o in self.orders:
                    self.orders.remove(o)
        return count

    # ---- paper fill simulation from a live price tick -------------------- #
    def tick_paper(self, symbol: str, price: float) -> list[Order]:
        """Fill any resting paper orders crossed by `price`. Returns filled orders.

        A limit buy at P fills when the market trades at or below P; a limit
        sell fills when the market trades at or above P (spot-grid matching).
        """
        if not self.paper:
            return []
        filled_now = []
        for o in list(self.orders):  # iterate a snapshot; safe to remove below
            if o.filled:
                continue
            if o.side == "buy" and price <= o.price:
                cost = o.amount * o.price
                if cost <= self.paper_usdt + 1e-9:
                    self.paper_usdt -= cost
                    self.base_held += o.amount
                    o.filled = True
                    self.fills.append(o)
                    self.orders.remove(o)
                    filled_now.append(o)
            elif o.side == "sell" and price >= o.price:
                if o.amount <= self.base_held + 1e-9:
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

    def fetch_balances(self, symbols=("USDT",)) -> dict:
        """Read-only balances. Paper uses the simulated wallet. Live needs a
        trade-only key; this never places an order."""
        if self.paper:
            return {"USDT": {"free": round(self.paper_usdt, 4)},
                    "_base_held": round(self.base_held, 8)}
        bal = self.ex.fetch_balance()
        out = {}
        total = bal.get("total", {}) or {}
        free = bal.get("free", {}) or {}
        for asset in list(symbols) + ["USDT"]:
            tot = float(total.get(asset, 0) or 0)
            fr = float(free.get(asset, 0) or 0)
            if tot > 0 or fr > 0 or asset == "USDT":
                out[asset] = {"total": round(tot, 6), "free": round(fr, 6)}
        return out

    def fetch_open_orders(self, symbol: str | None = None) -> list[dict]:
        """Read-only: resting orders on the exchange (live) or in the paper
        book. Never places or cancels anything on its own."""
        if self.paper:
            return [{"id": o.id, "side": o.side, "symbol": o.symbol,
                     "amount": o.amount, "price": o.price}
                    for o in self.orders]
        raw = self.ex.fetch_open_orders(symbol) if symbol else self.ex.fetch_open_orders()
        out = []
        for o in raw:
            out.append({
                "id": str(o.get("id", "")),
                "side": o.get("side"),
                "symbol": o.get("symbol"),
                "amount": o.get("amount"),
                "price": o.get("price") or (o.get("info", {}) or {}).get("price"),
                "status": o.get("status"),
            })
        return out
