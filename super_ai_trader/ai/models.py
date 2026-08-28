"""Local AI library — a curated list of the best compatible local models.

Works with Ollama (recommended) and llama.cpp-compatible local runners. The AI
runs 100% on your machine; nothing is sent to a cloud AI.

- catalog():     hand-picked models known to work well for this app in 2026
- ollama_up():   is a local Ollama server running?
- installed():   models already pulled locally
- recommend():   the best pick for the machine
- pull_url():    Ollama pull streaming endpoint (used by the install button)

All network calls are to 127.0.0.1 (your own machine).
"""
from __future__ import annotations

import json
import os
import urllib.request

OLLAMA = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")


# Curated for: natural-language trading commands + small, fast, private.
# size_gb is approximate download size; device = where it runs comfortably.
CATALOG = [
    {"id": "qwen3:1.7b", "name": "Qwen 3 — 1.7B", "params": "1.7B",
     "size_gb": 1.1, "good": ["chat", "commands"],
     "device": "phone / laptop", "note": "Fastest; great on iPhone/Android and weak PCs."},
    {"id": "llama3.2:3b", "name": "Llama 3.2 — 3B", "params": "3B",
     "size_gb": 2.0, "good": ["chat", "commands"],
     "device": "laptop", "note": "Balanced default; reliable for plain-language tasks."},
    {"id": "qwen3:4b", "name": "Qwen 3 — 4B", "params": "4B",
     "size_gb": 2.5, "good": ["chat", "commands", "analysis"],
     "device": "laptop / Mac", "note": "Smarter, still light; recommended on Apple Silicon."},
    {"id": "phi4-mini:latest", "name": "Phi-4 Mini", "params": "3.8B",
     "size_gb": 2.3, "good": ["commands", "analysis"],
     "device": "laptop / Mac", "note": "Strong at following structured instructions."},
    {"id": "gemma3:4b", "name": "Gemma 3 — 4B", "params": "4B",
     "size_gb": 3.3, "good": ["chat", "analysis"],
     "device": "Mac / good laptop", "note": "Google's small, clear model."},
    {"id": "llama3.1:8b", "name": "Llama 3.1 — 8B", "params": "8B",
     "size_gb": 4.7, "good": ["chat", "analysis", "research"],
     "device": "Apple Silicon / strong PC", "note": "Best 'smart' option for a home node."},
]


def catalog() -> list:
    return list(CATALOG)


def ollama_up(base: str | None = None, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen((base or OLLAMA) + "/api/tags", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def installed(base: str | None = None) -> list:
    """Return list of {'id':..., 'size_gb':...} for models already pulled."""
    try:
        with urllib.request.urlopen((base or OLLAMA) + "/api/tags", timeout=3) as r:
            data = json.loads(r.read().decode())
    except Exception:
        return []
    out = []
    for m in data.get("models", []):
        name = m.get("name", m.get("model", ""))
        size = m.get("size", 0)
        out.append({"id": name, "name": name,
                    "size_gb": round(size / 1e9, 2) if size else None})
    return out


def library() -> dict:
    """Catalog merged with installed status + the active model."""
    up = ollama_up()
    have = {m["id"].split(":")[0]: m for m in installed()}
    active = active_model()
    items = []
    for c in CATALOG:
        base = c["id"].split(":")[0]
        is_installed = up and (
            c["id"] in [m["id"] for m in installed()]
            or any(m["id"].startswith(base) for m in installed())
        )
        items.append({**c, "installed": bool(is_installed)})
    return {"ollama_running": up, "active": active, "models": items}


def active_model() -> str | None:
    """The model the assistant will use (env override or first sensible pick)."""
    env = os.getenv("OLLAMA_MODEL")
    if env:
        return env
    inst = installed()
    ids = [m["id"] for m in inst]
    if not ids:
        return None
    # Prefer a known good model if present, else the first.
    for pref in ("qwen3", "llama3.2", "llama3.1", "phi4", "gemma3"):
        for i in ids:
            if i.startswith(pref):
                return i
    return ids[0]


def recommend() -> dict | None:
    return CATALOG[2] if len(CATALOG) > 2 else (CATALOG[0] if CATALOG else None)
