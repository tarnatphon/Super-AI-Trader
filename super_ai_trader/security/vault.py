"""Local encrypted vault for exchange API keys (standard library only).

Security principles baked in:
- Keys NEVER touch the screen, logs, or the browser; they are stored encrypted.
- Encrypted at rest with scrypt key derivation + authenticated cipher
  (HMAC-SHA256, encrypt-then-MAC). Tampering is detected.
- Files are written with owner-only permissions (0600) in an owner-only dir.
- Vault is locked by default; it must be explicitly unlocked with a password.
- We only ever request TRADE-ONLY exchange keys (withdrawals disabled on the
  exchange). A redacted fingerprint (last 4 chars) is all that is displayed.

This is intentionally dependency-free and auditable. On macOS in production,
macOS Keychain (via `/usr/bin/security`) is an even better storage backend — see
docs/SECURITY-UX.md.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
import secrets
import time
from dataclasses import dataclass

SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAXMEM = 64 * 1024 * 1024  # 64 MB work memory


def _vault_dir() -> str:
    home = os.path.expanduser("~")
    d = os.path.join(home, ".super-ai-trader")
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def _vault_path(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in "-_")
    return os.path.join(_vault_dir(), f"vault-{safe}.enc")


def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt,
                          n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=64,
                          maxmem=SCRYPT_MAXMEM)


def _keystream(key: bytes, nonce: bytes, n: int) -> bytes:
    out = b""
    counter = 0
    while len(out) < n:
        block = hmac.new(key, nonce + counter.to_bytes(8, "big"),
                         hashlib.sha256).digest()
        out += block
        counter += 1
    return out[:n]


@dataclass
class StoredCredential:
    exchange: str
    api_key_fp: str       # last 4 of key only
    api_secret_fp: str    # last 4 of secret only
    label: str
    created: int


class Vault:
    """Encrypted, password-protected credential store (owner-only files)."""

    def store(self, name: str, exchange: str, api_key: str, api_secret: str,
              password: str, label: str = "") -> StoredCredential:
        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(16)
        payload = json.dumps({
            "exchange": exchange,
            "api_key": api_key,
            "api_secret": api_secret,
            "label": label or exchange,
            "created": int(time.time()),
        }).encode("utf-8")
        enc_key = _derive_key(password, salt)
        ks = _keystream(enc_key, nonce, len(payload))
        cipher = bytes(a ^ b for a, b in zip(payload, ks))
        mac = hmac.new(enc_key, salt + nonce + cipher, hashlib.sha256).digest()
        blob = {"v": 1, "salt": salt.hex(), "nonce": nonce.hex(),
                "cipher": cipher.hex(), "mac": mac.hex()}
        path = _vault_path(name)
        with open(path, "w") as f:
            json.dump(blob, f)
        os.chmod(path, 0o600)
        return StoredCredential(exchange, api_key[-4:], api_secret[-4:],
                                label or exchange, int(time.time()))

    def load(self, name: str, password: str) -> dict:
        """Unlock and decrypt. Raises ValueError on wrong password or tampering."""
        path = _vault_path(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"no saved credentials for '{name}'")
        with open(path) as f:
            blob = json.load(f)
        salt = bytes.fromhex(blob["salt"])
        nonce = bytes.fromhex(blob["nonce"])
        cipher = bytes.fromhex(blob["cipher"])
        mac = bytes.fromhex(blob["mac"])
        enc_key = _derive_key(password, salt)
        expected = hmac.new(enc_key, salt + nonce + cipher, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected):
            raise ValueError("wrong password or the credential file was altered")
        ks = _keystream(enc_key, nonce, len(cipher))
        payload = bytes(a ^ b for a, b in zip(cipher, ks))
        data = json.loads(payload.decode("utf-8"))
        data["_source"] = _vault_path(name)
        return data

    def list_names(self) -> list[str]:
        d = _vault_dir()
        return [f[6:-4] for f in os.listdir(d) if f.startswith("vault-") and f.endswith(".enc")]

    def delete(self, name: str) -> bool:
        path = _vault_path(name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False


# --------------------------------------------------------------------------- #
# Human-readable security checklist — the app's "Safety Shield".
# --------------------------------------------------------------------------- #
def security_checklist() -> list[dict]:
    return [
        {"id": "trade_only",
         "title": "Trade-only key",
         "detail": "Create the exchange key with spot trading ON but withdrawals OFF.",
         "must": True},
        {"id": "no_withdraw",
         "title": "Withdrawals disabled",
         "detail": "Even if the key leaks, nobody can move coins out of the exchange.",
         "must": True},
        {"id": "ip_whitelist",
         "title": "IP allowlist (optional, strong)",
         "detail": "Lock the key to your home IP on Binance/Gate if your IP is stable.",
         "must": False},
        {"id": "encryption",
         "title": "Keys encrypted on your computer",
         "detail": f"Stored in {_vault_dir()} with owner-only access; never sent anywhere.",
         "must": True},
        {"id": "practice_first",
         "title": "Practice mode first",
         "detail": "The app starts in PRACTICE mode; real trading needs an explicit unlock.",
         "must": True},
        {"id": "localhost",
         "title": "Runs only on your computer",
         "detail": "The web app binds to 127.0.0.1 — not reachable from the internet.",
         "must": True},
    ]


def platform_security_note() -> str:
    sys = platform.system()
    if sys == "Darwin":
        return ("On macOS, production builds can store keys in Keychain "
                "(/usr/bin/security) — the strongest option.")
    return f"Detected {sys}; encrypted local vault is active."
