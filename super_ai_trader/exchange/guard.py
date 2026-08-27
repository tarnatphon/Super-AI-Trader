"""Safety guard for real-money trading.

Wraps an exchange connector and refuses any order unless:
- the session was explicitly armed with a confirmation phrase, and
- total committed notional stays under a hard max-spend cap.

This is the code-level backstop behind the "real money" confirmation wall.
Paper trading never goes through this guard.
"""
from __future__ import annotations

from dataclasses import dataclass, field


CONFIRM_PHRASE = "I AGREE"


class LiveNotArmed(Exception):
    pass


@dataclass
class LiveOrderGuard:
    connector: object
    max_spend: float
    armed: bool = False
    spent: float = 0.0
    orders: list = field(default_factory=list)

    def arm(self, confirm_phrase: str) -> None:
        if (confirm_phrase or "").strip().upper() != CONFIRM_PHRASE:
            raise LiveNotArmed(
                f"real trading not armed — type '{CONFIRM_PHRASE}' to confirm")
        self.armed = True

    def _check(self, notional: float) -> None:
        if not self.armed:
            raise LiveNotArmed("real trading is not armed (confirmation required)")
        if self.spent + notional > self.max_spend + 1e-9:
            raise LiveNotArmed(
                f"max spend reached: {self.spent + notional:.2f} > cap {self.max_spend:.2f}")

    def place_limit_buy(self, symbol: str, amount: float, price: float) -> object:
        notional = amount * price
        self._check(notional)
        order = self.connector.place_limit_buy(symbol, amount, price)
        self.spent += notional
        self.orders.append(order)
        return order

    def place_limit_sell(self, symbol: str, amount: float, price: float) -> object:
        # Sells reduce risk; still require the session to be armed.
        if not self.armed:
            raise LiveNotArmed("real trading is not armed (confirmation required)")
        return self.connector.place_limit_sell(symbol, amount, price)

    def remaining_spend(self) -> float:
        return max(0.0, self.max_spend - self.spent)
