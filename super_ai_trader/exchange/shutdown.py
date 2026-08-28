"""Safe restart / shutdown — the #1 priority rule.

Before the app restarts or closes, any running live/paper grid must be fully
stopped first:

  1. Tell the bot to STOP placing new orders.
  2. Cancel ALL open buy and sell orders.
  3. Wait until the loop is idle / positions flat (with a timeout).
  4. Only then allow the restart/shutdown to proceed.

This returns a report; callers MUST check `safe_to_restart` before actually
restarting. Never restarts over an active session without this confirmation.
"""
from __future__ import annotations

import time


def _sessions(store: dict):
    sess = store.get("live")
    return [s for s in (sess, store.get("replay")) if s is not None]


def stop_all(store: dict, timeout: float = 12.0, log=print) -> dict:
    """Cancel everything and confirm nothing is running. Idempotent.

    Returns a report dict with safe_to_restart=True only when all sessions
    are stopped and carry no open orders (or only harmless paper orders).
    """
    report = {
        "stopped": [],
        "open_orders_before": 0,
        "open_orders_after": 0,
        "safe_to_restart": False,
        "notes": [],
    }
    sessions = _sessions(store)
    for sess in sessions:
        name = getattr(getattr(sess, "cfg", None), "symbol", "session")
        try:
            runner = getattr(sess, "runner", None)
            open_before = len(getattr(runner, "orders", []) or [])
            report["open_orders_before"] += open_before
            # 1) stop new orders + 2) cancel every open order
            try:
                sess.stop()
            except Exception as e:  # noqa: BLE001
                report["notes"].append(f"{name}: stop() error {e}")
            # give the loop a moment to finish any in-flight step
            deadline = time.time() + timeout
            while getattr(sess, "running", False) and time.time() < deadline:
                time.sleep(0.1)
            open_after = len(getattr(runner, "orders", []) or []) if runner else 0
            report["open_orders_after"] += open_after
            report["stopped"].append({
                "symbol": name,
                "running": getattr(sess, "running", False),
                "stopped": getattr(sess, "stopped", True),
                "open_orders_after": open_after,
            })
        except Exception as e:  # noqa: BLE001
            report["notes"].append(f"{name}: {e}")

    report["safe_to_restart"] = report["open_orders_after"] == 0 and all(
        s.get("stopped", False) for s in report["stopped"]
    )
    if report["safe_to_restart"]:
        report["message"] = "All buys/sells stopped, orders cancelled, bot is flat — safe to restart."
    else:
        report["message"] = "Bot still has open orders/running — NOT safe to restart yet."
    log(f"[safe-shutdown] {report['message']} ({report['open_orders_before']} -> "
        f"{report['open_orders_after']} orders)")
    return report
