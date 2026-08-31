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

_SESSION = {"live": None, "replay": None}

# Crash/power-cut protection: at import time, reconcile any leftover state
# from a previous run that did not close cleanly (power cut / crash). The
# dashboard fetches /api/startup to show the result before the bot can run.
try:
    from ..exchange.shutdown import reconcile_on_startup
    _STARTUP_REPORT = reconcile_on_startup(_SESSION)
except Exception as _e:  # noqa: BLE001
    _STARTUP_REPORT = {"clean_shutdown": False, "leftover_orders_cancelled": 0,
                       "note": f"startup reconcile skipped: {_e}"}


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
    from .. import config
    d = library()
    d["ollama_installed"] = ollama_present()
    cfg = config.load()
    d["ai_model"] = cfg.get("ai_model")
    d["ai_chosen"] = cfg.get("ai_chosen", False)
    d["needs_selection"] = not cfg.get("ai_chosen", False)
    return d


def _ai_select(payload: dict) -> dict:
    from .. import config
    model = payload.get("model")
    if not model:
        return {"ok": False, "error": "no model chosen"}
    cfg = config.save({"ai_model": model, "ai_chosen": True})
    return {"ok": True, "ai_model": cfg.get("ai_model"), "ai_chosen": True}


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


def _multigrid_start(payload: dict) -> dict:
    from ..exchange.multibot import get_manager
    coins = payload.get("coins") or ["BNB", "SOL", "ETH"]
    if isinstance(coins, str):
        coins = [c.strip() for c in coins.split(",") if c.strip()]
    mgr = get_manager(payload.get("exchange", "binance"))
    dd = payload.get("max_drawdown_pct", None)
    try:
        dd = float(dd) if dd not in (None, "", 0) else None
    except Exception:
        dd = None
    max_bots = payload.get("max_bots", None)
    max_allow = payload.get("max_allowance", None)
    try: max_bots = int(max_bots) if max_bots not in (None, "", 0) else None
    except Exception: max_bots = None
    try: max_allow = float(max_allow) if max_allow not in (None, "", 0) else None
    except Exception: max_allow = None
    return mgr.start(
        coins,
        investment=float(payload.get("investment", 1000)),
        range_pct=float(payload.get("range_pct", 12)),
        grids=int(payload.get("grids", 25)),
        max_drawdown_pct=dd,
        max_bots=max_bots,
        max_total_allowance=max_allow,
    )


def _multigrid_status(exchange: str = "binance") -> dict:
    from ..exchange.multibot import get_manager
    return get_manager(exchange).overview()


_DCA: dict = {}   # coin -> DCAPlan


def _dca_start(payload: dict) -> dict:
    from ..dca import DCAPlan
    from ..exchange.connector import ExchangeConnector
    from ..grid.engine import GridConfig  # noqa
    coins = payload.get("coins") or ["BTC"]
    if isinstance(coins, str):
        coins = [c.strip() for c in coins.split(",") if c.strip()]
    ex = payload.get("exchange", "binance")
    usd = float(payload.get("usd", 25))
    try:
        interval = float(payload.get("interval_hours", 24)) * 3600
    except Exception:
        interval = 24 * 3600
    max_buys = int(payload.get("max_buys", 0) or 0)
    started = []
    for coin in coins:
        sym = f"{coin}/USDT"
        try:
            price = ExchangeConnector(ex, paper=True).price(sym)
        except Exception:
            started.append({"coin": coin, "ok": False, "error": "no live data"}); continue
        plan = DCAPlan(symbol=sym, coin=coin, usd_amount=usd,
                       interval_seconds=interval, max_buys=max_buys)
        first = plan.execute_buy(price)   # immediate first buy
        _DCA[coin] = plan
        started.append({"coin": coin, "ok": True, "first_buy": first,
                        "average": plan.average_entry()})
    return {"ok": True, "exchange": ex, "started": started}


def _dca_status() -> dict:
    from ..exchange.connector import ExchangeConnector
    rows = []
    ex = "binance"
    for coin, plan in _DCA.items():
        try:
            price = ExchangeConnector(ex, paper=True).price(plan.symbol)
        except Exception:
            price = plan.average_entry()
        rows.append(plan.snapshot(price))
    return {"count": len(rows), "plans": rows}


def _dca_stop(payload: dict) -> dict:
    coin = payload.get("coin")
    if coin == "all" or not coin:
        for p in _DCA.values():
            p.running = False
        stopped = list(_DCA.keys())
    else:
        if coin in _DCA:
            _DCA[coin].running = False
        stopped = [coin]
    return {"stopped": stopped}


def _dca_tick() -> None:
    """Called periodically to execute due buys at live price."""
    from ..exchange.connector import ExchangeConnector
    for coin, plan in list(_DCA.items()):
        if plan.due():
            try:
                price = ExchangeConnector("binance", paper=True).price(plan.symbol)
                plan.execute_buy(price)
            except Exception:
                pass


_MORNING_STATE = {"last_sent_day": None}


def _morning_check_and_send(force: bool = False) -> dict:
    """Send the morning brief once per local day if enabled in config and
    any notification channel is configured."""
    from .. import config
    import datetime as _dt
    today = _dt.date.today().isoformat()
    if not force and _MORNING_STATE["last_sent_day"] == today:
        return {"sent": False, "reason": "already sent today", "day": today}
    if not force and not config.get("morning_brief_enabled", False):
        return {"sent": False, "reason": "morning brief not enabled", "day": today}
    res = _morning_brief({})
    if res.get("sent") or force:
        _MORNING_STATE["last_sent_day"] = today
    return res


def _morning_status() -> dict:
    from .. import config
    return {"enabled": bool(config.get("morning_brief_enabled", False))}


def _health(payload=None) -> dict:
    """Lightweight connectivity check for the header status badge."""
    from ..exchange.connector import ExchangeConnector
    ex = (payload or {}).get("exchange", "binance")
    coin = (payload or {}).get("coin", "BTC")
    try:
        conn = ExchangeConnector(ex, paper=True)
        price = conn.price(f"{coin}/USDT")
        return {"ok": True, "exchange": ex, "coin": coin, "price": price}
    except Exception as e:
        return {"ok": False, "exchange": ex, "error": type(e).__name__}


def _currency_list() -> dict:
    from ..currency import CURRENCIES, get_currency
    return {"currencies": [{"code": c, "name": n, "symbol": sy} for c, n, sy in CURRENCIES],
            "current": get_currency()}


def _currency_set(payload: dict) -> dict:
    from ..currency import set_currency, fmt_money
    code = set_currency(payload.get("currency", "USD"))
    return {"ok": True, "currency": code}


def _portfolio(payload: dict) -> dict:
    from ..exchange.multibot import get_manager
    from ..portfolio import build_portfolio
    from .. import currency
    ex = payload.get("exchange", "binance")
    overview = get_manager(ex).overview()
    try:
        period = int(payload.get("period", 0) or 0)
    except Exception:
        period = 0
    r = build_portfolio(overview, period_days=period)
    # display-currency conversion (all values are USD/USDT-native)
    code = payload.get("currency") or currency.get_currency()
    r["currency"] = code
    for k in ("total_value", "cash", "allocated", "total_pnl"):
        r[k + "_fiat"] = round(currency.convert(r.get(k, 0) or 0, code), 2)
    r["symbol"] = currency.symbol(code)
    for a in r.get("allocation", []):
        a["value_fiat"] = round(currency.convert(a["value"], code), 2)
    return r


def _morning_enable(payload: dict) -> dict:
    from .. import config
    config.save({"morning_brief_enabled": bool(payload.get("enabled", True))})
    return {"ok": True,
            "enabled": bool(config.get("morning_brief_enabled", False)),
            "note": "Sends each day to email/Telegram when a channel is configured."}


def _morning_brief(payload: dict) -> dict:
    """Compose the daily watcher/briefing and push it to email/Telegram if
    configured. Also returns the text so the UI can show it."""
    try:
        watch = _watcher()
    except Exception as e:  # noqa
        watch = {"summary": [f"watcher unavailable: {e}"]}
    from ..notify import notify
    lines = []
    lines.append("Good morning. 24/7 watcher — best moments now:")
    for l in watch.get("summary", []):
        lines.append("• " + l)
    for v in (watch.get("ranked") or [])[:5]:
        lines.append(f"  - {v['coin']}: {v['state'].replace('_',' ')} ({v['score']}/100) "
                     f"price {v['price']} | buy~{v.get('next_buy')} sell~{v.get('next_sell')}")
    lines.append("")
    lines.append("Golden rule: BUY LOW, SELL HIGH. Paused coins are protected; never chase.")
    body = "\n".join(lines)
    res = notify("Super-AI-Trader daily briefing", body)
    return {"sent": res.get("sent", False), "channels": res, "body": body}


def _watcher(payload=None) -> dict:
    """24/7 watcher: run over any live multi-grid sessions and rank
    best buy / sell moments across watched coins (paper; no orders)."""
    from ..exchange.multibot import get_manager
    from ..watcher import run_watch
    from .. import config
    lang = (payload or {}).get("lang") or config.get("lang", "en")
    ex = (payload or {}).get("exchange", "binance")
    mgr = get_manager(ex)
    summ = mgr.summary()
    coins = summ.get("coins") or []
    obs = []
    for coin in mgr.sessions:
        sess = mgr.sessions.get(coin)
        if sess is None:
            continue
        try:
            price = sess.conn.price(sess.cfg.symbol)
        except Exception:
            continue
        st = sess.status()
        obs.append({"coin": coin, "price": price, "cfg": sess.cfg,
                    "regime": st.get("regime"), "trail": st.get("trail")})
    return run_watch(obs, lang=lang)


def _briefing(payload: dict) -> dict:
    from ..exchange.multibot import get_manager
    from ..briefing import build_briefing
    from .. import config
    ex = payload.get("exchange", "binance")
    lang = payload.get("lang") or config.get("lang", "en")
    summ = get_manager(ex).summary()
    b = build_briefing(summ)
    # localize the golden rule line if present
    from ..messages import msg
    if b.get("lines"):
        b["lines"][0] = msg("golden_rule", lang)
    return b


def _multigrid_drawdown() -> dict:
    from ..exchange.multibot import get_manager
    return get_manager().check_drawdown()


def _multigrid_stop() -> dict:
    from ..exchange.multibot import get_manager
    return get_manager().stop()


def _notify_get() -> dict:
    from ..notify import load_notify
    return load_notify()


def _notify_save(payload: dict) -> dict:
    from ..notify import save_notify
    return save_notify(payload)


def _notify_test(payload: dict) -> dict:
    from ..notify import test_channels
    return test_channels(payload)


def _multigrid_retune(payload: dict) -> dict:
    from ..exchange.multibot import get_manager
    mgr = get_manager(payload.get("exchange", "binance"))
    coins = payload.get("coins")
    if isinstance(coins, str):
        coins = [c.strip() for c in coins.split(",") if c.strip()]
    return {"results": mgr.auto_retune(coins)}


def _multigrid_daily_retune(exchange: str = "binance") -> dict:
    from ..exchange.multibot import get_manager
    return get_manager(exchange).maybe_daily_retune()


def _live_open_orders(payload: dict) -> dict:
    """Read-only list of resting orders for a symbol (uses the unlocked key)."""
    from ..security.vault import Vault
    name = payload.get("name", "binance")
    password = payload.get("password", "")
    coin = payload.get("coin", "BNB")
    exchange = payload.get("exchange", "binance")
    try:
        cred = Vault().load(name, password)
    except Exception as e:
        return {"ok": False, "error": f"Could not unlock key: {e}"}
    try:
        from ..exchange.connector import ExchangeConnector
        conn = ExchangeConnector(cred["exchange"], paper=False,
                                 api_key=cred["api_key"], api_secret=cred["api_secret"])
        symbol = f"{coin}/USDT"
        orders = conn.fetch_open_orders(symbol)
        return {"ok": True, "exchange": cred.get("exchange", exchange),
                "symbol": symbol, "orders": orders, "count": len(orders)}
    except Exception as e:
        return {"ok": False, "error": f"Could not fetch orders: {type(e).__name__} {e}"}


def _live_balances(payload: dict) -> dict:
    """Read-only balance check with the unlocked trade-only key. Places NO orders."""
    from ..security.vault import Vault
    name = payload.get("name", "binance")
    password = payload.get("password", "")
    coins = payload.get("coins") or ["USDT", "BNB"]
    if isinstance(coins, str):
        coins = [c.strip() for c in coins.split(",") if c.strip()]
    exchange = payload.get("exchange", "binance")
    try:
        cred = Vault().load(name, password)
        exchange = cred.get("exchange", exchange)
    except Exception as e:
        return {"ok": False, "error": f"Could not unlock key: {e}"}
    try:
        from ..exchange.connector import ExchangeConnector
        conn = ExchangeConnector(cred["exchange"], paper=False,
                                 api_key=cred["api_key"], api_secret=cred["api_secret"])
        assets = ["USDT"] + [c for c in coins if c != "USDT"]
        bals = conn.fetch_balances(assets)
        return {"ok": True, "exchange": exchange, "balances": bals}
    except Exception as e:
        return {"ok": False, "error": f"Balance read failed: {type(e).__name__} {e}"}


def _live_preflight(payload: dict) -> dict:
    """Readiness checks before arming REAL grids. Returns steps with ok flags."""
    from ..security.vault import Vault
    name = payload.get("name", payload.get("exchange", "binance"))
    password = payload.get("password", "")
    try:
        cap = float(payload.get("max_spend", 0) or 0)
    except Exception:
        cap = 0.0
    steps = []

    # 1) a saved key exists (and can be unlocked if password given)
    names = Vault().list_names()
    key_saved = name in names
    steps.append({"id": "key", "label": "A trade-only exchange key is saved",
                  "ok": key_saved,
                  "fix": "Save a key in 'Connect an exchange' (trade-only, withdrawals OFF)."})
    key_ok = False
    if key_saved and password:
        try:
            Vault().load(name, password)
            key_ok = True
        except Exception:
            key_ok = False
    steps.append({"id": "unlock", "label": "Vault password unlocks the key",
                  "ok": key_ok,
                  "fix": "Enter your vault password."})

    # 2) small cap (encourage starting tiny)
    steps.append({"id": "cap",
                  "label": f"Spend cap is set and small (suggested &le; 100 USDT to start; you set {cap:g})",
                  "ok": 0 < cap <= 500,
                  "fix": "Set a small Max spend per coin (e.g. 50)."})

    # 3) paper tested (journal has runs)
    try:
        from ..journal import stats
        st = stats()
        paper_runs = st.get("runs", 0)
    except Exception:
        paper_runs = 0
    steps.append({"id": "paper",
                  "label": f"You practiced in paper/time-machine (runs recorded: {paper_runs})",
                  "ok": paper_runs > 0,
                  "fix": "Run a Time Machine or paper grid first to build trust."})

    # 4) the 'I AGREE' confirmation
    steps.append({"id": "agree", "label": "You will type I AGREE to arm (withdrawals stay impossible)",
                  "ok": str(payload.get("confirm", "")).strip().upper() == "I AGREE",
                  "fix": "Type I AGREE when you're ready."})
    ready = all(x["ok"] for x in steps)
    return {"ready": ready, "steps": steps}


def _live_grid_prepare(payload: dict) -> dict:
    from ..exchange.live_multigrid import get_live_manager
    lm = get_live_manager()
    coins = payload.get("coins") or ["BTC"]
    if isinstance(coins, str):
        coins = [c.strip() for c in coins.split(",") if c.strip()]
    result = lm.prepare(
        payload.get("name", payload.get("exchange", "binance")),
        payload.get("password", ""),
        coins,
        float(payload.get("investment", 100) or 100),
        float(payload.get("range_pct", 12)),
        int(payload.get("grids", 25)),
        float(payload.get("max_spend", 50) or 50),
    )
    # Attach the AI's recommended trailing/exit settings per coin (from
    # daily/auto tuning) so the live run uses paper-validated values.
    try:
        from ..journal import history
        tunes = [e for e in history(200) if e.get("kind") == "tune"]
        latest = {}
        for e in tunes:
            d = e.get("data", {})
            c = d.get("coin")
            if c:
                latest[c] = d  # history is chronological; last wins
        result["ai_tuned"] = {c: {"trail_arm": latest.get(c, {}).get("trail_arm"),
                                   "trail_giveback": latest.get(c, {}).get("trail_giveback"),
                                   "note": latest.get(c, {}).get("note"),
                                   "tuned": c in latest}
                              for c in coins}
    except Exception:
        result["ai_tuned"] = {}
    return result


def _live_grid_arm(payload: dict) -> dict:
    from ..exchange.live_multigrid import get_live_manager
    return get_live_manager().arm(payload.get("confirm", ""))


def _live_grid_stop() -> dict:
    from ..exchange.live_multigrid import get_live_manager
    return get_live_manager().stop_all()


def _live_grid_status() -> dict:
    from ..exchange.live_multigrid import get_live_manager
    return get_live_manager().overview()


def _autostart_get() -> dict:
    from .. import config
    return {k: config.get(k) for k in (
        "autostart_enabled", "autostart_coins", "autostart_exchange",
        "autostart_investment", "autostart_range", "autostart_grid_count")}


def _autostart_set(payload: dict) -> dict:
    from .. import config
    keys = ["autostart_enabled", "autostart_coins", "autostart_exchange",
            "autostart_investment", "autostart_range", "autostart_grid_count"]
    updates = {k: payload[k] for k in keys if k in payload}
    config.save(updates)
    return {"ok": True, **_autostart_get()}


def _autostart_apply() -> dict:
    """On dashboard load, if enabled, start the saved paper grids."""
    from .. import config
    if not config.get("autostart_enabled", False):
        return {"started": False}
    coins = [c.strip() for c in (config.get("autostart_coins") or "BNB").split(",") if c.strip()]
    ex = config.get("autostart_exchange", "binance")
    from ..exchange.multibot import get_manager
    try:
        r = get_manager(ex).start(
            coins,
            investment=float(config.get("autostart_investment", 1000)),
            range_pct=float(config.get("autostart_range", 12)),
            grids=int(config.get("autostart_grid_count", 25)),
        )
        return {"started": True, "exchange": ex, **r}
    except Exception as e:
        return {"started": False, "error": str(e)}


def _languages() -> dict:
    from ..i18n import supported
    from .. import config
    return {"languages": [{"code": c, "name": n} for c, n in supported()],
            "current": config.get("lang", "en")}


def _set_language(payload: dict) -> dict:
    from .. import config
    from ..i18n import t as _t
    lang = payload.get("lang", "en")
    config.save({"lang": lang})
    # return the full label dictionary so the page can localize.
    from ..i18n import LANG
    return {"ok": True, "lang": lang, "labels": LANG.get(lang, LANG["en"])}


def _emergency_stop(payload: dict) -> dict:
    """Global kill: cancel every paper grid across all venues and, if a
    vault password is supplied, cancel open real orders for the saved key.
    """
    report = {"paper": 0, "live_attempted": False, "live": None, "errors": []}
    # 1) stop all paper multi-grid managers (binance + gateio)
    try:
        from ..exchange.multibot import _MANAGERS
        for ex, mgr in _MANAGERS.items():
            try:
                r = mgr.stop()
                report["paper"] += int(r.get("stopped", 0))
            except Exception as e:
                report["errors"].append(f"{ex}: {e}")
    except Exception:
        pass
    # 2) any live paper session in _SESSION
    try:
        from ..exchange.shutdown import stop_all
        rep = stop_all(_SESSION)
        report["paper"] += rep.get("open_orders_before", 0) and 0  # don't double count
    except Exception:
        pass
    # 3) real exchange orders — only if the user unlocks a key right here.
    name = payload.get("name")
    password = payload.get("password")
    coins = payload.get("coins") or []
    if isinstance(coins, str):
        coins = [c.strip() for c in coins.split(",") if c.strip()]
    if name and password:
        try:
            from ..security.vault import Vault
            cred = Vault().load(name, password)
            from ..exchange.connector import ExchangeConnector
            conn = ExchangeConnector(cred["exchange"], paper=False,
                                     api_key=cred["api_key"], api_secret=cred["api_secret"])
            total = 0
            for coin in (coins or []):
                try:
                    total += int(conn.cancel_all_open_orders(f"{coin}/USDT"))
                except Exception as e:
                    report["errors"].append(f"{coin}: {e}")
            report["live_attempted"] = True
            report["live"] = {"exchange": cred["exchange"], "cancelled": total}
        except Exception as e:
            report["errors"].append(str(e))
    from ..journal import record_event
    record_event("EMERGENCY STOP triggered", "ALL")
    return {"ok": True, **report}


def _safe_stop_then_restart() -> dict:
    """PRIORITY: fully stop the bot before any restart."""
    import time as _time
    from ..exchange.shutdown import stop_all
    import threading as _th, os as _os, sys as _sys
    report = stop_all(_SESSION)
    # give the loop up to ~5s to actually stop
    deadline = _time.time() + 5
    while any(getattr(s, "running", False) for s in [_SESSION.get("live"), _SESSION.get("replay")] if s) and _time.time() < deadline:
        _time.sleep(0.2)
    _SESSION["live"] = None
    _SESSION["replay"] = None
    if not report["safe_to_restart"]:
        return {"ok": False, "message": report["message"], "report": report}

    def _restart():
        _time.sleep(1.0)
        _os.execv(_sys.executable, [_sys.executable] + _sys.argv)
    _th.Thread(target=_restart, daemon=True).start()
    return {"ok": True, "message": report["message"] + " Restarting now.", "report": report}


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


def _candles(payload: dict) -> dict:
    """OHLC candles for the big chart (real exchange, else practice)."""
    ticker = payload.get("ticker", "BTC")
    exchange = payload.get("exchange", "binance")
    timeframe = payload.get("timeframe", "1h")
    limit = int(payload.get("limit", 200))
    from ..data.indicators import closes, ema
    try:
        from ..exchange.connector import ExchangeConnector
        conn = ExchangeConnector(exchange, paper=True)
        bars = conn.ohlcv(f"{ticker}/USDT", timeframe=timeframe, limit=limit)
        source = f"LIVE {exchange}"
    except Exception as e:
        bars = get_series(ticker, days=max(300, limit), real=False)
        source = f"practice ({type(e).__name__})"
    # candles [t,o,h,l,c,v] (t = seconds)
    def ts(b):
        return int(b.date) if str(b.date).isdigit() else None
    out = []
    for i, b in enumerate(bars[-limit:]):
        out.append({"t": i, "o": round(b.open, 6), "h": round(b.high, 6),
                    "l": round(b.low, 6), "c": round(b.close, 6), "v": round(b.volume, 4)})
    c = closes(bars)
    ema7, ema25, ema99 = ema(c, 7), ema(c, 25), ema(c, 99)
    grid = None
    if payload.get("show_grid", True):
        last = c[-1]
        rp = float(payload.get("range_pct", 12))
        lvl_buy, lvl_sell = [], []
        step_gap = max((last * (rp/100))/25, last * 0.004)
        p = last
        while lvl_buy.__len__() < 12 and p >= last * (1 - rp/100):
            lvl_buy.append(round(p, 6)); p -= step_gap
        p = last
        while lvl_sell.__len__() < 12 and p <= last * (1 + rp/100):
            lvl_sell.append(round(p, 6)); p += step_gap
        grid = {"buy_levels": lvl_buy, "sell_levels": lvl_sell}
    # AI next buy-low / sell-high for the current range
    next_buy = next_sell = None
    action = None
    try:
        from ..grid.instructions import grid_instruction
        rng = float(payload.get("range_pct", 12))
        last = c[-1]
        cfg = type("C", (), {"lower": last*(1-rng/100), "upper": last*(1+rng/100),
                              "grids": 25})()
        inst = grid_instruction(last, cfg)
        next_buy = inst.get("next_buy"); next_sell = inst.get("next_sell")
        action = inst.get("action")
    except Exception:
        pass
    return {"symbol": f"{ticker}/USDT", "timeframe": timeframe,
            "source": source, "candles": out,
            "next_buy": next_buy, "next_sell": next_sell, "action": action,
            "ema7": [round(x,6) if x else None for x in ema7[-len(out):]],
            "ema25": [round(x,6) if x else None for x in ema25[-len(out):]],
            "ema99": [round(x,6) if x else None for x in ema99[-len(out):]],
            "grid": grid, "last": round(c[-1], 6)}


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


def _real_cancel_all(payload: dict) -> dict:
    """Connect with the unlocked trade-only key and cancel ALL open orders
    on the exchange (post-crash cleanup / pre-start safety). Non-destructive:
    removes resting limit orders; does not sell held balance."""
    from ..security.vault import Vault
    name = payload.get("name", "binance")
    password = payload.get("password", "")
    symbol = payload.get("symbol")  # optional specific symbol
    try:
        cred = Vault().load(name, password)
    except FileNotFoundError:
        return {"ok": False, "error": "No saved key for that name."}
    except ValueError:
        return {"ok": False, "error": "Wrong vault password."}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}

    from ..exchange.connector import ExchangeConnector
    try:
        conn = ExchangeConnector(cred["exchange"], paper=False,
                                 api_key=cred["api_key"], api_secret=cred["api_secret"])
        symbols = [symbol] if symbol else [f"{p.get('ticker','BTC')}/USDT"]
        total = 0
        per = {}
        for sym in symbols:
            try:
                n = conn.cancel_all_open_orders(sym)
                per[sym] = n
                total += int(n)
            except Exception as e:  # noqa: BLE001
                per[sym] = f"error: {type(e).__name__}"
        return {"ok": True, "exchange": cred["exchange"], "cancelled": total,
                "by_symbol": per,
                "message": f"Cancelled {total} open order(s) on {cred['exchange']}. The exchange is now clear."}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"Could not connect/cancel: {e}"}


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
    if exchange not in ("binance","gateio","bybit","okx","kucoin","kraken"):
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
        if u.path == "/api/export.csv":
            from ..export import export_csv
            csv_text = export_csv()
            body = csv_text.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition",
                             'attachment; filename="super-ai-trader-journal.csv"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if u.path in ("/", "/index.html"):
            self._page()
        elif u.path == "/api/checklist":
            self._send({"checklist": security_checklist()})
        elif u.path == "/api/connections":
            self._send(_list_connections())
        elif u.path == "/api/languages":
            self._send(_languages())
        elif u.path == "/api/live/status":
            self._send(_live_status())
        elif u.path == "/api/multigrid/status":
            q = parse_qs(urlparse(u.path).query)
            ex = (q.get("exchange") or ["binance"])[0]
            self._send(_multigrid_status(ex))
        elif u.path == "/api/livegrid/status":
            self._send(_live_grid_status())
        elif u.path == "/api/dca/status":
            self._send(_dca_status())
        elif u.path == "/api/multigrid/summary":
            q = parse_qs(urlparse(u.path).query)
            ex = (q.get("exchange") or ["binance"])[0]
            from ..exchange.multibot import get_manager
            self._send(get_manager(ex).summary())
        elif u.path == "/api/capabilities":
            self._send({"ccxt": _exchanges_ok()})
        elif u.path == "/api/startup":
            self._send(_STARTUP_REPORT or {"clean_shutdown": True,
                                           "note": "no previous session",
                                           "leftover_orders_cancelled": 0})
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
        if u.path == "/api/startup/ack":
            self._send({"ok": True, "acknowledged": True})
        elif u.path == "/api/startup":
            self._send(_STARTUP_REPORT or {"clean_shutdown": True,
                                           "note": "no previous session",
                                           "leftover_orders_cancelled": 0})
        elif u.path == "/api/market":
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
        elif u.path == "/api/ai/select":
            self._send(_ai_select(payload))
        elif u.path == "/api/ai/install":
            self._send(_ai_install(payload))
        elif u.path == "/api/restart":
            self._send(_safe_stop_then_restart())
        elif u.path == "/api/dca/start":
            self._send(_dca_start(payload))
        elif u.path == "/api/dca/stop":
            self._send(_dca_stop(payload))
        elif u.path == "/api/morning-brief":
            self._send(_morning_brief(payload))
        elif u.path == "/api/morning/enable":
            self._send(_morning_enable(payload))
        elif u.path == "/api/portfolio":
            self._send(_portfolio(payload))
        elif u.path == "/api/health":
            self._send(_health(payload))
        elif u.path == "/api/currency":
            self._send(_currency_list())
        elif u.path == "/api/currency/set":
            self._send(_currency_set(payload))
        elif u.path == "/api/morning/status":
            self._send(_morning_status())
        elif u.path == "/api/morning/tick":
            self._send(_morning_check_and_send(False))
        elif u.path == "/api/watcher":
            self._send(_watcher(payload))
        elif u.path == "/api/briefing":
            self._send(_briefing(payload))
        elif u.path == "/api/multigrid/drawdown":
            self._send(_multigrid_drawdown())
        elif u.path == "/api/multigrid/start":
            self._send(_multigrid_start(payload))
        elif u.path == "/api/notify/get":
            self._send(_notify_get())
        elif u.path == "/api/notify/save":
            self._send(_notify_save(payload))
        elif u.path == "/api/notify/test":
            self._send(_notify_test(payload))
        elif u.path == "/api/multigrid/daily-retune":
            self._send(_multigrid_daily_retune(payload.get("exchange", "binance")))
        elif u.path == "/api/live/open-orders":
            self._send(_live_open_orders(payload))
        elif u.path == "/api/live/balances":
            self._send(_live_balances(payload))
        elif u.path == "/api/livegrid/preflight":
            self._send(_live_preflight(payload))
        elif u.path == "/api/livegrid/prepare":
            self._send(_live_grid_prepare(payload))
        elif u.path == "/api/livegrid/arm":
            self._send(_live_grid_arm(payload))
        elif u.path == "/api/livegrid/stop":
            self._send(_live_grid_stop())
        elif u.path == "/api/multigrid/retune":
            self._send(_multigrid_retune(payload))
        elif u.path == "/api/multigrid/stop":
            self._send(_multigrid_stop())
        elif u.path == "/api/autostart/get":
            self._send(_autostart_get())
        elif u.path == "/api/autostart/set":
            self._send(_autostart_set(payload))
        elif u.path == "/api/autostart/apply":
            self._send(_autostart_apply())
        elif u.path == "/api/languages":
            self._send(_languages())
        elif u.path == "/api/language/set":
            self._send(_set_language(payload))
        elif u.path == "/api/emergency-stop":
            self._send(_emergency_stop(payload))
        elif u.path == "/api/safe-stop":
            from ..exchange.shutdown import stop_all
            from ..journal import mark_clean_shutdown
            report = stop_all(_SESSION)
            if report.get("safe_to_restart"):
                mark_clean_shutdown(True)
            self._send(report)
        elif u.path == "/api/simulate":
            self._send(_simulate(payload))
        elif u.path == "/api/autoset":
            self._send(_autoset(payload))
        elif u.path == "/api/connect":
            self._send(_connect(payload))
        elif u.path == "/api/ask":
            from .. import config
            from ..ai.commands import _reply_in_lang
            res = run_command(payload.get("text", ""), lang=config.get("lang", "en"))
            res["reply"] = _reply_in_lang(res.get("reply", ""), config.get("lang", "en"))
            self._send(res)
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
        elif u.path == "/api/real/cancel-all":
            self._send(_real_cancel_all(payload))
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
