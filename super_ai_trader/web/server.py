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

_SESSION = {"live": None}


def _exchanges_ok() -> bool:
    try:
        import ccxt  # noqa: F401
        return True
    except Exception:
        return False


def _real_bars(exchange_id: str, symbol: str, timeframe: str = "1h", limit: int = 600):
    """Real historical candles from the exchange. Raises if ccxt/network unavailable."""
    from ..exchange.connector import ExchangeConnector
    conn = ExchangeConnector(exchange_id, paper=True)
    return conn.ohlcv(symbol, timeframe=timeframe, limit=limit)


def _ai_library() -> dict:
    from ..ai.models import library
    from ..installer import ollama_present
    d = library()
    d["ollama_installed"] = ollama_present()
    return d


def _ai_install(payload: dict) -> dict:
    from ..installer import do_setup, pip_present
    action = payload.get("action", "")  # "pip" or "pull_model"
    target = payload.get("target", "")
    if action == "pull_model" and not _ai_library().get("ollama_running"):
        # Try to install the ccxt-ish extras? Ollama itself must be installed
        # by the user (an app). Give clear guidance.
        return {"ok": False,
                "status": ("Ollama isn't running. Install it from https://ollama.com, "
                           "start it, then come back and install the model.")}
    if action == "pip" and not pip_present():
        return {"ok": False, "status": "pip not found; use Python 3 with pip."}
    return do_setup(action, target, auto_restart=bool(payload.get("restart", False)))


def _journal_history() -> dict:
    from ..journal import history, stats
    return {"stats": stats(), "history": history(100)}


def _connection_tests(payload: dict) -> dict:
    """Run friendly health checks: ccxt, live price, order-book, key (if named)."""
    checks = []

    def add(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})

    add("App runs on your computer", True, "Bound to 127.0.0.1 — not on the internet")
    if _exchanges_ok():
        add("Exchange library (ccxt)", True, "installed and ready")
    else:
        add("Exchange library (ccxt)", False, "Install with: pip3 install ccxt")
        return {"ok": False, "checks": checks}

    exchange = payload.get("exchange", "binance")
    symbol = f"{payload.get('ticker', 'BTC')}/USDT"
    try:
        from ..exchange.connector import ExchangeConnector
        conn = ExchangeConnector(exchange, paper=True)
        price = conn.price(symbol)
        add(f"Live price from {exchange.title()}", price and price > 0,
            f"{symbol} = {price:,.4f}")
    except Exception as e:
        add(f"Live price from {exchange.title()}", False, f"No internet/blocked? {type(e).__name__}: {e}")
        return {"ok": False, "checks": checks}

    try:
        from ..data.live_behavior import fetch_live_behavior
        beh = fetch_live_behavior(exchange, symbol)
        add("Live buyers/sellers (order book)", True,
            f"{beh['pressure']} · {round((beh.get('buy_ratio') or 0.5)*100)}% buy vs "
            f"{round((beh.get('sell_ratio') or 0.5)*100)}% sell")
    except Exception as e:
        add("Live buyers/sellers (order book)", False, type(e).__name__)

    # Optional: validate a saved trade-only key.
    name = payload.get("name")
    password = payload.get("password")
    if name and password:
        try:
            from ..exchange.live_trading import prepare_real_trade
            pre = prepare_real_trade(name, password, 0)
            add("Saved trade-only key", pre.get("ok", False),
                pre.get("note") or pre.get("error") or "")
        except Exception as e:
            add("Saved trade-only key", False, str(e))
    else:
        add("Saved trade-only key", True, "Not set — paper mode (optional, checked when you connect)")

    return {"ok": all(c["ok"] for c in checks), "checks": checks}


def _market(payload: dict) -> dict:
    """Real exchange candles + EMA 7/25/99 for the live market chart."""
    from ..data.indicators import closes, ema
    from ..data.live_behavior import live_behavior
    exchange = payload.get("exchange", "binance")
    ticker = payload.get("ticker", "BTC")
    symbol = f"{ticker}/USDT"
    timeframe = payload.get("timeframe", "1h")
    limit = int(payload.get("limit", 400))
    source = f"LIVE {exchange} {symbol} {timeframe}"
    try:
        bars = _real_bars(exchange, symbol, timeframe=timeframe, limit=limit)
        if len(bars) < 30:
            raise RuntimeError("not enough candles")
    except Exception as e:
        bars = get_series(ticker, days=300, real=False)
        source = f"practice data (live feed unavailable: install ccxt + internet; {type(e).__name__})"
    c = closes(bars)
    # downsample to a chart-friendly length
    n = len(c)
    step = max(1, n // 150)
    def ds(vals):
        out = vals[::step]
        return [round(v, 6) if v is not None else None for v in out]
    e7, e25, e99 = ema(c, 7), ema(c, 25), ema(c, 99)
    grid = None
    if payload.get("show_grid", True):
        last = c[-1]
        rp = float(payload.get("range_pct", 12))
        gn = int(payload.get("grids", 25))
        geom = payload.get("mode", "geometric") == "geometric"
        lo, hi = last * (1 - rp / 100), last * (1 + rp / 100)
        lines = [(lo * (hi / lo) ** (i / gn)) if geom else (lo + (hi - lo) * i / gn)
                 for i in range(gn + 1)]
        grid = {
            "buy_levels": [round(p, 6) for p in lines if p < last][-12:],
            "sell_levels": [round(p, 6) for p in lines if p > last][:12],
        }
    try:
        beh = live_behavior(exchange, symbol, bars=bars)
    except Exception:
        beh = None
    return {
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
        "last": round(c[-1], 6),
        "change_pct": round((c[-1] / c[0] - 1) * 100, 2),
        "closes": ds(c),
        "ema7": ds(e7), "ema25": ds(e25), "ema99": ds(e99),
        "grid": grid,
        "pressure": beh.get("pressure") if beh else None,
        "buy_ratio": beh.get("buy_ratio") if beh else None,
        "sell_ratio": beh.get("sell_ratio") if beh else None,
    }


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


def _preview(payload: dict) -> dict:
    """PAST result over REAL exchange candles (the Preview), with a labeled fallback."""
    from ..grid.summary import bot_summary
    ticker = payload.get("ticker", "SOL")
    exchange = payload.get("exchange", "binance")
    symbol = f"{ticker}/USDT"
    investment = float(payload.get("investment", 1_000))
    range_pct = float(payload.get("range_pct", 12))
    grids = int(payload.get("grids", 25))
    mode = payload.get("mode", "geometric")
    fee = float(payload.get("fee", 0.1))
    source = "LIVE exchange history"
    try:
        bars = _real_bars(exchange, symbol, timeframe=payload.get("timeframe", "1h"), limit=600)
        if len(bars) < 50:
            raise RuntimeError("not enough candles")
    except Exception as e:
        bars = get_series(ticker, days=600, real=False)
        source = f"practice data (live feed unavailable: install ccxt + internet; {type(e).__name__})"
    ref = bars[0].close
    cfg = GridConfig(symbol=symbol,
                     lower=ref * (1 - range_pct / 100), upper=ref * (1 + range_pct / 100),
                     grids=grids, mode=mode, investment=investment, fee_pct=fee,
                     range_pct=range_pct,
                     stop_loss_price=ref * (1 - range_pct * 2 / 100),
                     take_profit_price=ref * (1 + range_pct * 2 / 100))
    res = simulate_on_bars(cfg, bars)
    summary = bot_summary(cfg, res, bars)
    summary["data_source"] = source
    return summary


def _live_start(payload: dict) -> dict:
    """Start a live PAPER session trading real exchange prices."""
    from ..exchange.connector import ExchangeConnector
    from ..exchange.live_session import LiveSession
    from ..data.live_behavior import fetch_live_behavior
    exchange = payload.get("exchange", "binance")
    symbol = f"{payload.get('ticker','SOL')}/USDT"
    investment = float(payload.get("investment", 1_000))
    range_pct = float(payload.get("range_pct", 12))
    grids = int(payload.get("grids", 25))
    mode = payload.get("mode", "geometric")

    existing = _SESSION["live"]
    if existing is not None and not existing.stopped:
        return {"ok": False, "error": "a live session is already running — stop it first"}

    conn = ExchangeConnector(exchange, paper=True, paper_usdt=investment)
    try:
        ref = conn.price(symbol)
    except Exception as e:
        return {"ok": False, "error": f"cannot reach {exchange}: {e}. "
                "Run `pip install ccxt` and check internet. No real orders are sent in paper mode."}
    cfg = GridConfig(symbol=symbol,
                     lower=ref * (1 - range_pct / 100), upper=ref * (1 + range_pct / 100),
                     grids=grids, mode=mode, investment=investment, fee_pct=0.1,
                     range_pct=range_pct,
                     stop_loss_price=ref * (1 - range_pct * 2 / 100),
                     take_profit_price=ref * (1 + range_pct * 2 / 100))
    sess = LiveSession(conn, cfg, poll_seconds=float(payload.get("poll", 5)),
                       timeframe=str(payload.get("timeframe", "1h")),
                       behavior_fn=lambda: fetch_live_behavior(exchange, symbol))
    sess.start()
    _SESSION["live"] = sess
    return {"ok": True, "message": f"Live PAPER trading started on {exchange} {symbol} at {ref:.4f} "
                                   f"(real prices, practice money — no orders sent).",
            "status": sess.status()}


def _replay_start(payload: dict) -> dict:
    """Start a time-machine replay over real (or built-in) historical candles."""
    from ..grid.engine import GridConfig
    from ..exchange.replay import ReplayConnector, ReplaySession
    exchange = payload.get("exchange", "binance")
    ticker = payload.get("ticker", "SOL")
    symbol = f"{ticker}/USDT"
    investment = float(payload.get("investment", 1_000))
    range_pct = float(payload.get("range_pct", 12))
    grids = int(payload.get("grids", 25))
    mode = payload.get("mode", "geometric")
    timeframe = payload.get("timeframe", "1h")
    source = "LIVE exchange history"
    try:
        bars = _real_bars(exchange, symbol, timeframe=timeframe, limit=int(payload.get("limit", 600)))
        if len(bars) < 60:
            raise RuntimeError("not enough candles")
    except Exception as e:
        bars = get_series(ticker, days=int(payload.get("limit", 600)), real=False)
        source = f"practice data (live feed unavailable: install ccxt + internet; {type(e).__name__})"
    ref = bars[0].close
    cfg = GridConfig(symbol=symbol,
                     lower=ref * (1 - range_pct / 100), upper=ref * (1 + range_pct / 100),
                     grids=grids, mode=mode, investment=investment, fee_pct=0.1,
                     range_pct=range_pct,
                     stop_loss_price=ref * (1 - range_pct * 2 / 100),
                     take_profit_price=ref * (1 + range_pct * 2 / 100))
    conn = ReplayConnector(bars, exchange_id=exchange, paper_usdt=investment)
    conn.cfg = cfg
    sess = ReplaySession(conn, cfg)
    sess.start()
    _SESSION["replay"] = sess
    st = sess.status()
    st["ok"] = True
    st["data_source"] = source
    return st


def _replay_advance(steps: int = 1) -> dict:
    sess = _SESSION.get("replay")
    if sess is None:
        return {"ok": False, "error": "no replay — start one first"}
    info = {}
    was_finished = sess.finished
    for _ in range(max(1, steps)):
        if sess.finished:
            break
        info = sess.step()
    st = sess.status()
    st["ok"] = True
    # Record to the journal when a run completes (only the completion event).
    if st.get("finished") and not was_finished:
        try:
            from ..journal import record_grid
            record_grid(
                st.get("symbol", "").split("/")[0],
                "time-machine replay",
                st.get("investment", 0),
                st.get("roi_pct", 0.0),
                (st.get("pnl", 0.0) or 0.0),
                st.get("round_trips", 0),
                bool(st.get("killed")),
                extra={"roi_pct": st.get("roi_pct")},
            )
        except Exception:
            pass
    return st


def _preset_save(payload: dict) -> dict:
    from ..settings import save_preset
    name = (payload.get("name") or "my preset").strip()
    return save_preset(name, payload)


def _preset_list() -> dict:
    from ..settings import list_presets
    return {"presets": list_presets()}


def _preset_delete(name: str) -> dict:
    from ..settings import delete_preset
    return delete_preset(name)


def _preset_load(name: str) -> dict:
    from ..settings import load_preset
    return load_preset(name)


def _autotune(payload: dict) -> dict:
    """Fast AI trailing optimization for the selected coin."""
    from ..learning.trailing import optimize_trailing, explain_optimization
    ticker = payload.get("ticker", "BTC")
    opt = optimize_trailing(ticker, days=700, real=False, quick=True)
    b = opt["best"]
    return {
        "ok": True,
        "ticker": ticker,
        "best": b,
        "top5": opt["top5"],
        "confirmation": opt["confirmation"],
        "explanation": explain_optimization(opt).replace("🤖", "").strip(),
    }


def _real_prepare(payload: dict) -> dict:
    from ..exchange.live_trading import prepare_real_trade
    return prepare_real_trade(
        payload.get("name", payload.get("exchange", "binance")),
        payload.get("password", ""),
        float(payload.get("max_spend", 0) or 0),
    )


def _real_arm(payload: dict) -> dict:
    from ..exchange.live_trading import arm_real_trading
    return arm_real_trading(
        payload.get("name", payload.get("exchange", "binance")),
        payload.get("password", ""),
        float(payload.get("max_spend", 0) or 0),
        payload.get("confirm", ""),
    )


def _live_status() -> dict:
    sess = _SESSION["live"]
    if sess is None or sess.stopped:
        return {"running": False}
    return {"running": True, **sess.status()}


def _live_stop() -> dict:
    sess = _SESSION["live"]
    if sess is None:
        return {"ok": False, "error": "no session"}
    sess.stop()
    final = sess.status()
    return {"ok": True, "message": "Live session stopped. Orders (paper) cancelled.", "final": final}


def _botdetails(payload: dict) -> dict:
    from ..grid.summary import bot_summary
    ticker = payload.get("ticker", "BTC")
    investment = float(payload.get("investment", 1_000))
    bars = get_series(ticker, days=int(payload.get("days", 600)), real=False)
    ref = bars[0].close
    range_pct = float(payload.get("range_pct", 12))
    grids = int(payload.get("grids", 25))
    mode = payload.get("mode", "geometric")
    fee = float(payload.get("fee", 0.1))
    cfg = GridConfig(
        symbol=f"{ticker}/USDT",
        lower=ref * (1 - range_pct / 100), upper=ref * (1 + range_pct / 100),
        grids=grids, mode=mode, investment=investment, fee_pct=fee, range_pct=range_pct,
        stop_loss_price=ref * (1 - range_pct * 2 / 100),
        take_profit_price=ref * (1 + range_pct * 2 / 100),
    )
    res = simulate_on_bars(cfg, bars)
    return bot_summary(cfg, res, bars)


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
    access_token: str | None = None  # when set, non-local requests must present it

    def log_message(self, *a):  # quiet; don't log request data
        pass

    def _authorized(self) -> bool:
        # Local requests are always allowed. Requests from another device
        # (phone over Tailscale) require a Bearer token / ?token=.
        client = self.client_address[0]
        if client in ("127.0.0.1", "::1", "localhost"):
            return True
        if not self.access_token:
            return False  # remote access disabled until a token is configured
        auth = self.headers.get("Authorization", "")
        q = parse_qs(urlparse(self.path).query).get("token", [""])[0]
        return auth == f"Bearer {self.access_token}" or q == self.access_token

    def _send(self, obj, code=200):
        if not self._authorized():
            body = json.dumps({"error": "unauthorized — provide the access token"}).encode()
            self.send_response(401)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
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
        elif u.path == "/api/live/status":
            self._send(_live_status())
        elif u.path == "/api/capabilities":
            self._send({"ccxt": _exchanges_ok()})
        elif u.path == "/api/preset/list":
            self._send(_preset_list())
        elif u.path == "/api/preset/load":
            q = parse_qs(u.query)
            self._send(_preset_load((q.get("name") or [""])[0]))
        elif u.path == "/api/live/stop":
            self._send(_live_stop())
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            payload = {}
        if u.path == "/api/market":
            self._send(_market(payload))
        elif u.path == "/api/connection-test":
            self._send(_connection_tests(payload))
        elif u.path == "/api/journal":
            self._send(_journal_history())
        elif u.path == "/api/journal/add":
            from ..journal import record
            entry = record(str(payload.get("kind", "event")), payload.get("data", {}))
            self._send(entry)
        elif u.path == "/api/ai/library":
            self._send(_ai_library())
        elif u.path == "/api/ai/install":
            self._send(_ai_install(payload))
        elif u.path == "/api/restart":
            self._send({"ok": True, "status": "restart requested"})
            import threading as _th
            def _later():
                import os, sys
                os.execv(sys.executable, [sys.executable] + sys.argv)
            _th.Thread(target=_later, daemon=True).start()
        elif u.path == "/api/simulate":
            self._send(_simulate(payload))
        elif u.path == "/api/autoset":
            self._send(_autoset(payload))
        elif u.path == "/api/connect":
            self._send(_connect(payload))
        elif u.path == "/api/ask":
            self._send(run_command(payload.get("text", "")))
        elif u.path == "/api/botdetails":
            self._send(_botdetails(payload))
        elif u.path == "/api/preview":
            self._send(_preview(payload))
        elif u.path == "/api/live/start":
            self._send(_live_start(payload))
        elif u.path == "/api/replay/start":
            self._send(_replay_start(payload))
        elif u.path == "/api/replay/advance":
            self._send(_replay_advance(int(payload.get("steps", 1))))
        elif u.path == "/api/real/prepare":
            self._send(_real_prepare(payload))
        elif u.path == "/api/real/arm":
            self._send(_real_arm(payload))
        elif u.path == "/api/autotune":
            self._send(_autotune(payload))
        elif u.path == "/api/preset/save":
            self._send(_preset_save(payload))
        elif u.path == "/api/preset/delete":
            self._send(_preset_delete(str(payload.get("name", ""))))
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


def make_server(host: str = "127.0.0.1", port: int = 8787):
    """Create (but don't start) the local HTTP server."""
    return ThreadingHTTPServer((host, port), Handler)


def run(host: str = "127.0.0.1", port: int = 8787):
    server = make_server(host, port)
    print(f"Super-AI-Trader dashboard: http://{host}:{port}")
    print("(local only — not reachable from the internet). Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
