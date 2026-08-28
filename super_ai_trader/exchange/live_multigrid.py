"""Guarded REAL-money multi-coin grid.

This is the live counterpart to multibot.py (which is paper-only). Real
order placement is gated by THREE things:

1. A valid unlocked trade-only key (withdrawals OFF) from the local vault.
2. A hard per-run spend CAP enforced in code by LiveOrderGuard.
3. Explicit arming with the phrase "I AGREE".

Until armed, place_limit_buy raises LiveNotArmed — so the bot literally
cannot spend real money. Sells (exits) require arming too.
"""
from __future__ import annotations

import threading

from ..grid.engine import GridConfig
from .connector import ExchangeConnector
from .guard import LiveOrderGuard, LiveNotArmed
from .grid_runner import LiveGridRunner
from ..security.vault import Vault


class GuardedCoin:
    """One coin's live grid: real connector + guard + runner."""

    def __init__(self, coin: str, guard: LiveOrderGuard, cfg: GridConfig):
        self.coin = coin
        self.guard = guard
        self.cfg = cfg
        self.runner = LiveGridRunner(guard, cfg)   # orders go through guard
        self.status_msg = "created (not armed)"
        self.armed = False

    def arm(self, confirm: str) -> None:
        self.guard.arm(confirm)          # raises if not "I AGREE"
        self.armed = True
        self.status_msg = "ARMED (live)"
        self.runner.setup()              # places the buy ladder

    def safe_stop(self) -> None:
        try:
            self.runner.shutdown()
        except Exception:
            pass
        try:
            self.guard.connector.cancel_all_open_orders(self.cfg.symbol)
        except Exception:
            pass
        self.status_msg = "stopped"

    def snapshot(self) -> dict:
        r = self.guard
        return {
            "coin": self.coin,
            "armed": self.armed,
            "status": self.status_msg,
            "spent": round(getattr(r, "spent", 0.0), 2),
            "max_spend": getattr(r, "max_spend", 0.0),
            "remaining_spend": round(r.remaining_spend(), 2) if self.armed else getattr(r, "max_spend", 0.0),
            "open_orders": len(getattr(r, "orders", [])),
        }


class LiveMultiGrid:
    """Holds the guarded grids for a whole basket. Paper-free (real exchange)."""

    def __init__(self):
        self.coins: dict[str, GuardedCoin] = {}
        self._lock = threading.Lock()
        self.armed = False

    def prepare(self, key_name: str, vault_password: str, coins: list[str],
                investment_per_coin: float, range_pct: float, grids: int,
                max_spend_per_coin: float) -> dict:
        """Validate the key and BUILD (but don't arm) the guarded grids.

        Returns a confirmation summary; nothing is ordered yet.
        """
        try:
            cred = Vault().load(key_name, vault_password)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"Could not unlock key: {e}"}

        self.cred = cred
        self._built = []
        for coin in coins:
            sym = f"{coin}/USDT"
            conn = ExchangeConnector(cred["exchange"], paper=False,
                                     api_key=cred["api_key"],
                                     api_secret=cred["api_secret"])
            try:
                ref = conn.price(sym)
            except Exception as e:  # noqa: BLE001
                self._built.append({"coin": coin, "ok": False, "error": str(e)})
                continue
            cfg = GridConfig(
                symbol=sym,
                lower=ref * (1 - range_pct / 100),
                upper=ref * (1 + range_pct / 100),
                grids=grids, mode="geometric",
                investment=investment_per_coin, fee_pct=0.1, range_pct=range_pct,
            )
            guard = LiveOrderGuard(conn, max_spend=float(max_spend_per_coin))
            self.coins[coin] = GuardedCoin(coin, guard, cfg)
            self._built.append({
                "coin": coin, "ok": True, "price": round(ref, 6),
                "max_spend": float(max_spend_per_coin),
                "key_fingerprint": "•••• " + cred["api_key"][-4:],
            })
        ok_coins = [b for b in self._built if b.get("ok")]
        return {
            "ok": True,
            "exchange": cred["exchange"],
            "key_fingerprint": "•••• " + cred["api_key"][-4:],
            "coins_ready": len(ok_coins),
            "details": self._built,
            "total_cap": round(len(ok_coins) * max_spend_per_coin, 2),
            "note": ("Review carefully. If armed, the robot places real buy "
                     "orders up to the cap; withdrawals are impossible."),
        }

    def arm(self, confirm: str) -> dict:
        """Arms ALL prepared grids after the 'I AGREE' confirmation."""
        if not self.coins:
            return {"ok": False, "error": "Nothing prepared yet."}
        errors = []
        armed = 0
        for coin, gc in list(self.coins.items()):
            try:
                gc.arm(confirm)
                armed += 1
            except LiveNotArmed as e:
                errors.append(f"{coin}: {e}")
        self.armed = armed > 0 and not errors
        return {"ok": self.armed, "armed_coins": armed, "errors": errors,
                "statuses": [gc.snapshot() for gc in self.coins.values()]}

    def stop_all(self) -> dict:
        for gc in self.coins.values():
            gc.safe_stop()
        self.armed = False
        return {"ok": True, "statuses": [gc.snapshot() for gc in self.coins.values()]}

    def overview(self) -> dict:
        return {"armed": self.armed,
                "coins": [gc.snapshot() for gc in self.coins.values()]}


_LIVE: LiveMultiGrid | None = None


def get_live_manager() -> LiveMultiGrid:
    global _LIVE
    if _LIVE is None:
        _LIVE = LiveMultiGrid()
    return _LIVE
