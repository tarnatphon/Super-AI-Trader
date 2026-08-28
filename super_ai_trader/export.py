"""Export the local run journal to CSV (grids, replays, tunes, events).

Reads the owner-only journal.jsonl and flattens it into one row per entry,
ready to open in Excel/Sheets or keep for your records.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime

from .journal import history


COLUMNS = [
    ("date", lambda e, d: d),
    ("kind", lambda e, d: e.get("kind")),
    ("coin", lambda e, d: (e.get("data", {}) or {}).get("coin")
                            or (e.get("data", {}) or {}).get("ticker") or ""),
    ("source", lambda e, d: (e.get("data", {}) or {}).get("source", "")),
    ("roi_pct", lambda e, d: (e.get("data", {}) or {}).get("roi_pct", "")),
    ("pnl", lambda e, d: (e.get("data", {}) or {}).get("pnl", "")),
    ("round_trips", lambda e, d: (e.get("data", {}) or {}).get("round_trips", "")),
    ("stopped", lambda e, d: (e.get("data", {}) or {}).get("stopped", "")),
    ("trail_arm", lambda e, d: (e.get("data", {}) or {}).get("trail_arm", "")),
    ("trail_giveback", lambda e, d: (e.get("data", {}) or {}).get("trail_giveback", "")),
    ("note", lambda e, d: (e.get("data", {}) or {}).get("note")
                            or (e.get("data", {}) or {}).get("label", "")),
]


def to_csv_rows(entries: list[dict]) -> list[list]:
    header = [c[0] for c in COLUMNS]
    rows = [header]
    for e in entries:
        ts = e.get("ts")
        when = datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="seconds") if ts else ""
        rows.append([fn(e, when) for _, fn in COLUMNS])
    return rows


def export_csv(kind: str | None = None) -> str:
    entries = history(10000, kind=kind)
    rows = to_csv_rows(entries)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(rows)
    return buf.getvalue()
