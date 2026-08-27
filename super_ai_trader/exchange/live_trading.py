"""Real-money flow: vault unlock -> read-only key validation -> confirmation.

No real order is placed unless:
1. The user unlocks their encrypted vault with the password.
2. The exchange key validates (read-only: balances load).
3. The user explicitly arms with the phrase 'I AGREE' and sets a max-spend cap.
The LiveOrderGuard then enforces the cap on every order.
"""
from __future__ import annotations

from ..security.vault import Vault
from .connector import ExchangeConnector


def prepare_real_trade(name: str, vault_password: str, max_spend: float) -> dict:
    """Unlock key, validate read-only, and return a confirmation summary.

    Returns dict with ok=False and an error message on any failure. Does NOT
    arm trading or place orders.
    """
    try:
        cred = Vault().load(name, vault_password)
    except FileNotFoundError:
        return {"ok": False, "error": "No saved key for that name. Save a trade-only key first."}
    except ValueError:
        return {"ok": False, "error": "Wrong vault password or the file was altered."}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"Could not unlock: {e}"}

    # Read-only validation: connect and try to read balances (no orders).
    conn = ExchangeConnector(cred["exchange"], paper=False,
                             api_key=cred["api_key"], api_secret=cred["api_secret"])
    try:
        bal = conn.ex.fetch_balance()
        usdt = float(bal.get("USDT", {}).get("free", 0) or bal.get("free", {}).get("USDT", 0) or 0)
    except Exception as e:  # noqa: BLE001
        return {"ok": False,
                "error": f"Key loaded but exchange rejected it: {e}. "
                         "Check the key is trade-only, withdrawals OFF, and IP is allowed."}

    return {
        "ok": True,
        "exchange": cred["exchange"],
        "label": cred.get("label", cred["exchange"]),
        "key_fingerprint": "•••• " + cred["api_key"][-4:],
        "free_usdt": round(usdt, 2),
        "max_spend_requested": float(max_spend),
        "confirm_phrase": "I AGREE",
        "note": "Review before arming. The bot can never withdraw funds or spend "
                "more than the cap you set.",
    }


def arm_real_trading(name: str, vault_password: str, max_spend: float,
                     confirm_phrase: str) -> dict:
    """Fully arm live trading after explicit confirmation. Returns a guard summary."""
    from .guard import LiveOrderGuard, LiveNotArmed
    pre = prepare_real_trade(name, vault_password, max_spend)
    if not pre["ok"]:
        return pre
    if (confirm_phrase or "").strip().upper() != "I AGREE":
        return {"ok": False, "error": "You must type 'I AGREE' to arm real trading."}
    try:
        cred = Vault().load(name, vault_password)
        conn = ExchangeConnector(cred["exchange"], paper=False,
                                 api_key=cred["api_key"], api_secret=cred["api_secret"])
        guard = LiveOrderGuard(conn, max_spend=float(max_spend))
        guard.arm(confirm_phrase)
    except LiveNotArmed as e:
        return {"ok": False, "error": str(e)}
    return {
        "ok": True,
        "armed": True,
        "exchange": cred["exchange"],
        "key_fingerprint": "•••• " + cred["api_key"][-4:],
        "max_spend": float(max_spend),
        "remaining_spend": guard.remaining_spend(),
        "message": "LIVE trading armed. Trade-only key active; withdrawals disabled; "
                   "hard spend cap enforced. Stop the bot any time to disarm.",
    }
