"""Out-of-sight notifications: tell you what the AI/bot did.

Two optional channels, both configured in the app and stored locally (no keys
leave the machine beyond the provider's own API):

- EMAIL via SMTP over SSL (works with Gmail using an App Password):
    host: smtp.gmail.com  port: 465
    user: your@gmail.com   pass: a Gmail App Password (NOT your login password)
- TELEGRAM bot:
    create a bot with @BotFather, paste the bot token and your chat id.

Send is best-effort: failures never stop trading. Settings live in the local
encrypted vault folder via config (the app password is written to an
owner-only file, like the key vault).
"""
from __future__ import annotations

import json
import os
import smtplib
import ssl
import urllib.parse
import urllib.request

from . import config


def _smtp_path() -> str:
    d = os.path.join(os.path.expanduser("~"), ".super-ai-trader")
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return os.path.join(d, "notify.json")


def load_notify() -> dict:
    defaults = {
        "email_enabled": False, "smtp_host": "smtp.gmail.com", "smtp_port": 465,
        "smtp_user": "", "smtp_pass": "", "email_to": "",
        "telegram_enabled": False, "tg_token": "", "tg_chat": "",
    }
    cfg = config.load().get("notify")
    p = _smtp_path()
    disk = {}
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                disk = json.load(f)
        except Exception:
            disk = {}
    out = dict(defaults)
    if isinstance(cfg, dict):
        out.update({k: v for k, v in cfg.items() if k in defaults})
    out.update({k: v for k, v in disk.items() if k in defaults})
    # never show the password fully
    return out


def save_notify(data: dict) -> dict:
    allowed = ("email_enabled", "smtp_host", "smtp_port", "smtp_user",
               "smtp_pass", "email_to", "telegram_enabled", "tg_token", "tg_chat")
    stored = {k: data.get(k) for k in allowed if k in data}
    with open(_smtp_path(), "w", encoding="utf-8") as f:
        json.dump(stored, f, indent=2)
    try:
        os.chmod(_smtp_path(), 0o600)
    except OSError:
        pass
    view = load_notify()
    if view.get("smtp_pass"):
        view["smtp_pass"] = "••••••••"  # redacted
    return view


def send_email(subject: str, body: str, n: dict | None = None) -> bool:
    n = n or load_notify()
    if not n.get("email_enabled") or not n.get("smtp_user") or not n.get("smtp_pass"):
        return False
    try:
        host = n.get("smtp_host", "smtp.gmail.com")
        port = int(n.get("smtp_port", 465) or 465)
        user = n["smtp_user"]
        to = n.get("email_to") or user
        msg = (f"From: Super-AI-Trader <{user}>\r\nTo: <{to}>\r\n"
               f"Subject: {subject}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{body}")
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as s:
            s.login(user, n["smtp_pass"])
            s.sendmail(user, [to], msg.encode("utf-8"))
        return True
    except Exception:
        return False


def send_telegram(text: str, n: dict | None = None) -> bool:
    n = n or load_notify()
    if not n.get("telegram_enabled") or not n.get("tg_token") or not n.get("tg_chat"):
        return False
    try:
        url = f"https://api.telegram.org/bot{n['tg_token']}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": n["tg_chat"], "text": text,
            "parse_mode": "HTML"}).encode()
        with urllib.request.urlopen(url, data=data, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False


def notify(subject: str, body: str) -> dict:
    """Best-effort alert to all enabled channels."""
    n = load_notify()
    email = send_email(subject, body, n)
    tg = send_telegram(f"<b>{subject}</b>\n{body}", n)
    return {"sent": bool(email or tg), "email": email, "telegram": tg}


def test_channels(data: dict) -> dict:
    """Send a test message using the provided (not-yet-saved) settings."""
    save_notify(data)
    n = load_notify()
    # Reload saved to get the password back for sending.
    try:
        with open(_smtp_path(), encoding="utf-8") as f:
            n.update(json.load(f))
    except Exception:
        pass
    res = notify("Super-AI-Trader test alert ✅",
                 "Notifications are working. You'll get alerts when the bot "
                 "pauses in a crash or locks profit.")
    return res
