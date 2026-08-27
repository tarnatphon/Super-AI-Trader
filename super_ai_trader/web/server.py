"""A tiny, SAFE local web server (standard library only).

Design rules for security and simplicity:
- Binds ONLY to 127.0.0.1 (localhost) — never reachable from the internet.
- Practice mode is the default; it only runs simulations, no orders.
- Exchange secrets are never sent to the browser (a redacted fingerprint only).
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from ..data.market import get_series
from ..grid.engine import GridConfig, simulate_on_bars
from ..grid.advisor import advise, plain_language
from ..security.vault import Vault, security_checklist, platform_security_note
from ..ai.commands import run_command


def _simulate(payload: dict) -> dict:
    ticker = payload.get("ticker", "BTC")
    investment = float(payload.get("investment", 10_000))
    bars = get_series(ticker, days=int(payload.get("days", 600)),
                      real=False)
    ref = bars[-1].close
    range_pct = float(payload.get("range_pct", 12))
    lower = payload.get("lower")
    upper = payload.get("upper")
    cfg = GridConfig(
        symbol=f"{ticker}/USDT",
        lower=float(lower) if lower else ref * (1 - range_pct / 100),
        upper=float(upper) if upper else ref * (1 + range_pct / 100),
        grids=int(payload.get("grids", 25)),
        mode=payload.get("mode", "geometric"),
        investment=investment,
        fee_pct=float(payload.get("fee", 0.1)),
        range_pct=range_pct,
    )
    if payload.get("stop_loss"):
        cfg.stop_loss_price = float(payload["stop_loss"])
    if payload.get("take_profit"):
        cfg.take_profit_price = float(payload["take_profit"])
    res = simulate_on_bars(cfg, bars)
    # Downsample the equity curve for the chart.
    curve = res.equity_curve
    step = max(1, len(curve) // 120)
    points = [round(v, 2) for _i, v in curve[::step]]
    if points[-1:] != [res.final_equity]:
        points.append(res.final_equity)
    return {
        "symbol": res.symbol,
        "price_now": round(ref, 2),
        "price_start": round(res.start_price, 2),
        "price_end": round(res.end_price, 2),
        "lower": round(cfg.lower, 2),
        "upper": round(cfg.upper, 2),
        "grid_profit": res.grid_profit,
        "fees": res.fees_paid,
        "unrealized": res.unrealized_pnl,
        "round_trips": res.filled_round_trips,
        "final_equity": res.final_equity,
        "initial": res.initial,
        "return_pct": round((res.final_equity / res.initial - 1) * 100, 2),
        "stopped": res.stopped,
        "curve": points,
    }


def _autoset(payload: dict) -> dict:
    ticker = payload.get("ticker", "BTC")
    investment = float(payload.get("investment", 10_000))
    bars = get_series(ticker, days=int(payload.get("days", 600)), real=False)
    adv = advise(bars, investment=investment, risk_mode=payload.get("risk_mode", "steady"))
    cfg = adv["config"]
    sim = _simulate({
        "ticker": ticker, "investment": investment,
        "lower": cfg.lower, "upper": cfg.upper, "grids": cfg.grids,
        "mode": cfg.mode, "fee": cfg.fee_pct,
        "stop_loss": cfg.stop_loss_price, "take_profit": cfg.take_profit_price,
        "days": payload.get("days", 600),
    })
    return {
        "lower": cfg.lower, "upper": cfg.upper, "grids": cfg.grids, "mode": cfg.mode,
        "fee": cfg.fee_pct, "stop_loss": cfg.stop_loss_price,
        "take_profit": cfg.take_profit_price,
        "plain": plain_language(adv),
        "sim": sim,
    }


def _connect(payload: dict) -> dict:
    """Save credentials locally (never echoed back)."""
    exchange = payload.get("exchange")
    if exchange not in ("binance", "gateio"):
        return {"ok": False, "error": "choose Binance or Gate.io"}
    name = payload.get("name") or exchange
    api_key = payload.get("api_key", "").strip()
    api_secret = payload.get("api_secret", "").strip()
    password = payload.get("password", "")
    if len(api_key) < 8 or len(api_secret) < 8 or not password:
        return {"ok": False, "error": "need an API key, secret, and a vault password"}
    vault = Vault()
    cred = vault.store(name, exchange, api_key, api_secret, password)
    return {"ok": True, "name": name, "exchange": exchange,
            "api_key_fp": f"•••• {cred.api_key_fp}",
            "note": "Saved encrypted on this computer only. Withdrawals must be OFF."}


def _list_connections() -> dict:
    vault = Vault()
    return {"connections": vault.list_names(), "note": platform_security_note()}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet; don't log request data
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            self._page()
        elif u.path == "/api/checklist":
            self._send({"checklist": security_checklist()})
        elif u.path == "/api/connections":
            self._send(_list_connections())
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            payload = {}
        if u.path == "/api/simulate":
            self._send(_simulate(payload))
        elif u.path == "/api/autoset":
            self._send(_autoset(payload))
        elif u.path == "/api/connect":
            self._send(_connect(payload))
        elif u.path == "/api/ask":
            self._send(run_command(payload.get("text", "")))
        else:
            self._send({"error": "not found"}, 404)

    def _page(self):
        from .page import HTML
        body = HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host: str = "127.0.0.1", port: int = 8787):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Super-AI-Trader dashboard: http://{host}:{port}")
    print("(local only — not reachable from the internet). Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
