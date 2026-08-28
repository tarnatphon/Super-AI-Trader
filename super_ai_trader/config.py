"""Small persisted app config (owner-only, local). Holds things like the
chosen local AI model and other user preferences. No secrets here."""
from __future__ import annotations

import json
import os


def _path() -> str:
    d = os.path.join(os.path.expanduser("~"), ".super-ai-trader")
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return os.path.join(d, "config.json")


_DEFAULTS = {
    "ai_model": None,        # e.g. "qwen3:4b"; None = built-in simple parser
    "ai_chosen": False,      # has the user made a first-run choice?
}


def load() -> dict:
    p = _path()
    if not os.path.exists(p):
        return dict(_DEFAULTS)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        out = dict(_DEFAULTS)
        out.update(data)
        return out
    except Exception:
        return dict(_DEFAULTS)


def save(updates: dict) -> dict:
    data = load()
    data.update(updates)
    with open(_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    try:
        os.chmod(_path(), 0o600)
    except OSError:
        pass
    return data


def get(key, default=None):
    return load().get(key, default)
