"""Display-currency formatting (USD default; THB, EUR supported).

Live rates are fetched when possible (ccxt gives USDT pairs; fiat rates
fall back to approximate constants offline). Formatting is best-effort and
only affects DISPLAY — trading stays in USDT on the exchange.
"""
from __future__ import annotations

import os
import json
import time

# Approximate fallback rates per 1 USD (used offline). Easy to update.
_FALLBACK = {  # code: (rate_per_usd, symbol)
    "USD": (1.0, "$"),
    "THB": (35.0, "฿"),
    "EUR": (0.92, "€"),
    "GBP": (0.78, "£"),
    "CNY": (7.2, "¥"),
}
_CACHE = {"rates": None, "ts": 0.0}

CURRENCIES = [
    ("USD", "US Dollar", "$"),
    ("THB", "Thai baht", "฿"),
    ("EUR", "Euro", "€"),
    ("GBP", "British pound", "£"),
    ("CNY", "Chinese yuan", "¥"),
]


def config_path() -> str:
    d = os.path.join(os.path.expanduser("~"), ".super-ai-trader")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "currency.json")


def get_currency() -> str:
    from . import config
    return config.get("display_currency", "USD") or "USD"


def set_currency(code: str) -> str:
    from . import config
    code = (code or "USD").upper()
    if code not in [c[0] for c in CURRENCIES]:
        code = "USD"
    config.save({"display_currency": code})
    return code


def rates() -> dict:
    """USD->fiat rates; tries a public feed, falls back to constants."""
    if _CACHE["rates"] and (time.time() - _CACHE["ts"] < 6 * 3600):
        return _CACHE["rates"]
    r = {c: _FALLBACK.get(c, (1.0, ""))[0] for c in ["USD", "THB", "EUR", "GBP", "CNY"]}
    try:
        import urllib.request
        url = "https://open.er-api.com/v6/latest/USD"
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        rates = data.get("rates", {})
        for c in list(r):
            if c in rates and rates[c]:
                r[c] = float(rates[c])
    except Exception:
        pass
    _CACHE["rates"] = r
    _CACHE["ts"] = time.time()
    return r


def convert(amount_usd: float, code: str | None = None) -> float:
    code = (code or get_currency()).upper()
    if code == "USD":
        return float(amount_usd or 0.0)
    return float(amount_usd or 0.0) * rates().get(code, 1.0)


def symbol(code: str | None = None) -> str:
    code = (code or get_currency()).upper()
    return {"USD": "$", "THB": "฿", "EUR": "€", "GBP": "£", "CNY": "¥"}.get(code, "$")


def fmt_money(amount_usd: float, code: str | None = None) -> str:
    """Format an amount that's natively USDT/USD into the display currency."""
    code = (code or get_currency()).upper()
    val = convert(amount_usd, code)
    sym = symbol(code)
    if abs(val) >= 100000:
        return f"{sym}{val:,.0f}"
    if abs(val) >= 1000:
        return f"{sym}{val:,.1f}"
    return f"{sym}{val:,.2f}"
