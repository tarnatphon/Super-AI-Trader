"""Local run journal — a persistent, owner-only record of what the bot did.

Each grid/replay/paper run and notable event (fill, profit lock, safety stop)
is appended to ~/.super-ai-trader/journal.jsonl. This gives the "Historical
Profits" view across sessions and survives app restarts. No secrets are stored
here — only results and plain labels.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass


def _dir() -> str:
    d = os.path.join(os.path.expanduser("~"), ".super-ai-trader")
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def _path() -> str:
    return os.path.join(_dir(), "journal.jsonl")


def record(kind: str, data: dict) -> dict:
    """Append an event. kind e.g. 'grid', 'replay', 'paper', 'event'."""
    entry = {"ts": int(time.time()), "kind": kind, "data": data or {}}
    line = json.dumps(entry)
    with open(_path(), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    try:
        os.chmod(_path(), 0o600)
    except OSError:
        pass
    return entry


def history(limit: int = 100, kind: str | None = None) -> list:
    p = _path()
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if kind and e.get("kind") != kind:
                continue
            out.append(e)
    return out[-limit:]


def stats() -> dict:
    """Roll-up of recorded runs for the dashboard."""
    runs = [e for e in history(500) if e.get("kind") in ("grid", "replay", "paper")]
    total = len(runs)
    pnl = sum(float(e.get("data", {}).get("pnl", 0) or 0) for e in runs)
    wins = sum(1 for e in runs if float(e.get("data", {}).get("pnl", 0) or 0) > 0)
    round_trips = sum(int(e.get("data", {}).get("round_trips", 0) or 0) for e in runs)
    last = runs[-1] if runs else None
    return {
        "runs": total,
        "total_pnl": round(pnl, 2),
        "wins": wins,
        "round_trips": round_trips,
        "last_kind": last.get("kind") if last else None,
    }


def record_grid(ticker: str, source: str, investment: float, roi_pct: float,
                pnl: float, round_trips: int, stopped: bool, extra: dict | None = None):
    return record("grid", {
        "ticker": ticker, "source": source, "investment": investment,
        "roi_pct": round(roi_pct, 3), "pnl": round(pnl, 3),
        "round_trips": round_trips, "stopped": bool(stopped),
        **(extra or {}),
    })


def record_event(label: str, ticker: str = "", **kw):
    return record("event", {"label": label, "ticker": ticker, **kw})


# --- clean-shutdown marker (crash / power-cut detection) -----------------

def _state_path() -> str:
    return os.path.join(_dir(), "state.json")


def mark_clean_shutdown(clean: bool = True) -> None:
    """Write whether the previous run stopped cleanly."""
    with open(_state_path(), "w", encoding="utf-8") as f:
        json.dump({"clean_shutdown": bool(clean), "ts": int(time.time())}, f)
    try:
        os.chmod(_state_path(), 0o600)
    except OSError:
        pass


def was_clean_shutdown() -> bool:
    """True only if the last run set a clean marker; False after a crash/power cut."""
    p = _state_path()
    if not os.path.exists(p):
        return False
    try:
        with open(p, encoding="utf-8") as f:
            return bool(json.load(f).get("clean_shutdown", False))
    except Exception:
        return False
