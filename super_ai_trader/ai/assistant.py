"""Plain-language assistant for the local app.

You say things like:
  "Trade 1000 USDT on Bitcoin with a safe grid, about 12 percent range"
The assistant returns a GridConfig-like dict and a simple explanation.

- If a local Ollama model is running (LLM_BASE_URL / OLLAMA host), it is used to
  understand the request — fully local, no cloud AI.
- Otherwise an offline rule-based parser handles common phrasings, so it always
  works.
"""
from __future__ import annotations

import json
import os
import urllib.request

from ..grid.engine import GridConfig


COINS = {
    "bitcoin": "BTC", "btc": "BTC",
    "ethereum": "ETH", "eth": "ETH",
    "binance coin": "BNB", "bnb": "BNB",
    "dogecoin": "DOGE", "doge": "DOGE",
    "solana": "SOL", "sol": "SOL",
    "xrp": "XRP", "ripple": "XRP",
}


def _find_coin(text: str) -> str:
    low = text.lower()
    for name, sym in COINS.items():
        if name in low:
            return sym
    return "BTC"


def _numbers_by_context(text: str) -> dict:
    """Walk words; classify each number by the tokens around it."""
    import re
    low = text.lower().replace("$", "$ ").replace(",", "")
    words = re.findall(r"[a-zA-Z%]+|[\d.]+", low)
    vals = {"investment": None, "range_pct": None, "grids": None}
    for i, tok in enumerate(words):
        if not re.fullmatch(r"\d+(\.\d+)?", tok):
            continue
        num = float(tok)
        prev = words[i - 1] if i > 0 else ""
        nxt = words[i + 1] if i + 1 < len(words) else ""
        nxt2 = words[i + 2] if i + 2 < len(words) else ""
        if nxt in ("usdt", "usd", "dollar", "dollars") or prev == "$" or prev in ("use", "amount", "trade"):
            vals["investment"] = num
        elif nxt in ("grid", "grids", "step", "steps", "line", "lines") or prev in ("grids", "grid", "steps", "step"):
            vals["grids"] = int(num)
        elif nxt in ("percent", "%", "percentage") or nxt2 in ("range",) or prev in ("range",):
            vals["range_pct"] = num
    return vals


def offline_parse(text: str) -> dict:
    """Rule-based parser: always available, no AI needed."""
    nums = _numbers_by_context(text)
    low_w = "narrow" in text or "tight" in text or "calm" in text
    wide_w = "wide" in text or "bouncy" in text or "volatile" in text
    rng = nums["range_pct"] or (8 if low_w else 20 if wide_w else 12)
    coin = _find_coin(text)
    safe = any(w in text.lower() for w in ("safe", "steady", "careful", "kid", "beginner"))
    return {
        "symbol": f"{coin}/USDT", "coin": coin,
        "investment": nums["investment"] or 1000.0,
        "range_pct": rng,
        "grids": nums["grids"] or (20 if low_w else 30 if wide_w else 25),
        "mode": "arithmetic" if low_w else "geometric",
        "fee_pct": 0.1,
        "exchange": "gateio" if "gate" in text.lower() else "binance",
        "safe": safe,
        "source": "offline rules",
    }


def ollama_available(base_url: str | None = None) -> bool:
    base = base_url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    try:
        with urllib.request.urlopen(base + "/api/tags", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def ollama_parse(text: str, model: str | None = None,
                 base_url: str | None = None) -> dict | None:
    """Ask a local Ollama model to extract grid parameters. Returns None on
    failure so callers can fall back to offline parsing."""
    base = base_url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
    prompt = (
        "Extract grid-trading settings from this user request and reply with ONLY "
        "JSON. Keys: coin (BTC/ETH/BNB/DOGE/SOL/XRP), investment_usdt (number), "
        "range_pct (number, the price range width percent), grids (integer number "
        "of grid lines), mode (geometric or arithmetic), exchange (binance or "
        "gateio), safe (true if the user wants careful/safe settings). "
        "If a value is not stated use null. Request: " + text)
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    try:
        req = urllib.request.Request(base + "/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode())
        out = data.get("response", "")
        s, e = out.find("{"), out.rfind("}")
        if s == -1 or e == -1:
            return None
        j = json.loads(out[s:e + 1])
        coin = (j.get("coin") or "BTC").upper()
        return {
            "symbol": f"{coin}/USDT", "coin": coin,
            "investment": float(j.get("investment_usdt") or 1000),
            "range_pct": float(j.get("range_pct") or 12),
            "grids": int(j.get("grids") or 25),
            "mode": j.get("mode") or "geometric",
            "fee_pct": 0.1,
            "exchange": j.get("exchange") or "binance",
            "safe": bool(j.get("safe", True)),
            "source": f"local AI ({model})",
        }
    except Exception:
        return None


def interpret(text: str, model: str | None = None) -> dict:
    """Best-effort: local Ollama if present, else offline rules."""
    parsed = None
    if ollama_available():
        parsed = ollama_parse(text, model=model)
    parsed = parsed or offline_parse(text)
    # Safety defaulting for the "anyone can use it" goal.
    if parsed.get("safe"):
        parsed["mode"] = parsed.get("mode") or "geometric"
    return parsed


def to_grid_config(parsed: dict, ref_price: float) -> GridConfig:
    rng = parsed["range_pct"]
    cfg = GridConfig(
        symbol=parsed["symbol"],
        lower=ref_price * (1 - rng / 100),
        upper=ref_price * (1 + rng / 100),
        grids=parsed["grids"],
        mode=parsed["mode"],
        investment=parsed["investment"],
        fee_pct=parsed.get("fee_pct", 0.1),
        range_pct=rng,
        stop_loss_price=ref_price * (1 - rng * 2 / 100),
        take_profit_price=ref_price * (1 + rng * 2 / 100),
    )
    return cfg


def explain(parsed: dict) -> str:
    return (f"OK! Using {parsed['source']}. I'll set up a {parsed['mode']} grid for "
            f"{parsed['coin']} on {parsed['exchange']}, using about "
            f"{parsed['investment']:.0f} USDT, spread across {parsed['grids']} small "
            f"steps over a {parsed['range_pct']:.0f}% price range. Practice mode is on, "
            f"and the safety stop is on too. Nothing is bought with real money until "
            f"you connect an exchange.")
