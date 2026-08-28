"""Optional dependency installer with auto-restart on success.

Lets the app pull a local AI model (Ollama) or pip-install a package, then
restarts itself so the new capability is active. Runs only on your machine.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request

from .ai.models import OLLAMA


def ollama_present() -> bool:
    return shutil.which("ollama") is not None


def pip_present() -> bool:
    return shutil.which("pip3") is not None or shutil.which("pip") is not None


def install_package(pkg: str) -> dict:
    """pip install into the current Python environment."""
    py = sys.executable or "python3"
    try:
        p = subprocess.run([py, "-m", "pip", "install", "--user", pkg],
                           capture_output=True, text=True, timeout=300)
        ok = p.returncode == 0
        return {"ok": ok, "output": (p.stdout + p.stderr)[-2000:]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "output": str(e)}


def pull_model(model: str, timeout: float = 900) -> dict:
    """Pull an Ollama model via its local streaming API."""
    payload = json.dumps({"model": model, "stream": True}).encode()
    req = urllib.request.Request(OLLAMA + "/api/pull", data=payload,
                                 headers={"Content-Type": "application/json"})
    last = ""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for raw in r:
                try:
                    last = json.loads(raw.decode()).get("status", last)
                except Exception:
                    continue
        return {"ok": True, "status": f"{model} ready ({last})"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": f"pull failed: {e}. Is Ollama running?"}


def restart_app():
    """Restart the whole app so freshly installed modules/models load."""
    # Re-exec the current process with the same args; in the launcher this
    # also re-opens the window/browser.
    os.execv(sys.executable, [sys.executable] + sys.argv)


def do_setup(action: str, target: str, auto_restart: bool = True) -> dict:
    """Run a setup task; optionally restart on success."""
    if action == "pip":
        res = install_package(target)
    elif action == "pull_model":
        res = pull_model(target)
    else:
        return {"ok": False, "status": "unknown action"}
    if res.get("ok") and auto_restart:
        # Hand the restart back to the caller where appropriate; in a
        # background CLI call this restarts the launcher directly.
        res["restarting"] = True
    return res
