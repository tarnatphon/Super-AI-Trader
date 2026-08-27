"""Saved presets — store the user's favorite grid/strategy settings locally.

A named preset captures everything on the setup card plus timeframe. Stored as
JSON in an owner-only folder (no secrets here; API keys live in the vault).
"""
from __future__ import annotations

import json
import os


def _dir() -> str:
    d = os.path.join(os.path.expanduser("~"), ".super-ai-trader")
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def _path(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in "-_ ").strip() or "preset"
    return os.path.join(_dir(), f"preset-{safe}.json")


DEFAULTS = {
    "ticker": "BTC",
    "exchange": "binance",
    "investment": 1000.0,
    "range_pct": 12.0,
    "grids": 25,
    "mode": "geometric",
    "fee": 0.1,
    "timeframe": "1h",
    "trail_arm": 5.0,
    "trail_giveback": 1.0,
    "risk_per_trade": 0.5,
    "max_position": 15.0,
    "daily_loss": 1.5,
}


def save_preset(name: str, settings: dict) -> dict:
    data = {k: settings.get(k, DEFAULTS[k]) for k in DEFAULTS}
    with open(_path(name), "w") as f:
        json.dump({"name": name, "settings": data}, f, indent=2)
    try:
        os.chmod(_path(name), 0o600)
    except OSError:
        pass
    return {"ok": True, "name": name, "settings": data}


def load_preset(name: str) -> dict:
    p = _path(name)
    if not os.path.exists(p):
        return {"ok": False, "error": f"no preset called '{name}'"}
    with open(p) as f:
        return json.load(f)


def list_presets() -> list:
    out = []
    for fn in os.listdir(_dir()):
        if fn.startswith("preset-") and fn.endswith(".json"):
            try:
                with open(os.path.join(_dir(), fn)) as f:
                    j = json.load(f)
                out.append({"name": j.get("name", fn[7:-5]), "settings": j.get("settings", {})})
            except Exception:
                continue
    return sorted(out, key=lambda x: x["name"])


def delete_preset(name: str) -> dict:
    p = _path(name)
    if os.path.exists(p):
        os.remove(p)
        return {"ok": True}
    return {"ok": False, "error": "not found"}
