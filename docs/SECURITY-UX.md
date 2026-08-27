# Design & Security — simple for anyone, safe by default

Two priorities drive the whole app:

1. **Anyone can use it** — designed so a **10-year-old** can get it and a **70-year-old**
   can understand it. Plain words, big buttons, safe defaults, no jargon.
2. **Security & hack-protection first** — the app should never be the reason someone
   loses their funds.

## Original UX (inspired by — but not copied from — Binance & Gate.io)

We took the **best functions** from each grid app and made our own simpler design:

| Best idea | From | How we made it original & simpler |
|---|---|---|
| "Fill AI parameters" auto range | Binance | Big blue **"✨ Auto-Set For Me"** button that picks range, step count and style, then *explains in one plain sentence why* |
| Arithmetic vs geometric choice | Gate.io | Auto-chosen for the user from market volatility; hidden under "Advanced" |
| Stop-loss / take-profit | Gate.io | Auto-placed **outside** the grid; explained as "the robot stops to protect your money" |
| Clear profit/fees display | Binance | One big green/red result line + a friendly equity chart |
| Many grid types (infinite, margin, martingale, DCA) | Gate.io | Kept out of the simple view (advanced/power mode later) to avoid mistakes |
| Practice / demo before real | Both | **Practice mode is the default and biggest button**; connecting an exchange is a separate, opt-in step |

### The 3-screen flow
1. **Pick coin** (BTC pre-selected — "don't know? use Bitcoin").
2. **Choose amount** (practice money) + a simple Narrow/Normal/Wide range choice.
3. **"Try It"** → see results in plain language, or **"Auto-Set"** to let it choose.

Everything risky is behind **Advanced** or the separate **Connect Exchange** card.

## Security model ("Safety Shield")

| Control | Implementation |
|---|---|
| **Not reachable from the internet** | Web app binds to `127.0.0.1` (localhost) only. |
| **Practice by default** | No exchange keys, no orders — simulations only. |
| **Trade-only API keys** | Onboarding instructs: spot trading **ON**, withdrawals **OFF**. |
| **Keys encrypted at rest** | `security/vault.py`: scrypt key derivation (N=2^14) + HMAC-SHA256 authenticated, encrypt-then-MAC keystream cipher. Tampering/wrong password → rejected. |
| **Owner-only files** | Vault dir `~/.super-ai-trader` is `0700`; credential files `0600`. |
| **Secrets never shown/sent to browser** | The UI only ever receives a redacted fingerprint like `•••• 7890`. Logs don't print request bodies. |
| **Password lock** | Vault is locked until explicitly unlocked with the user's password. |
| **IP allowlist guidance** | Checklist recommends locking the key to the user's IP when stable. |
| **macOS Keychain (roadmap)** | On Mac, production can store keys in Keychain via `/usr/bin/security` — the strongest local option. |

The 6-point checklist is shown in the app (and returned by `GET /api/checklist`).

## Running it

```bash
python3 -m super_ai_trader web          # opens http://127.0.0.1:8787
# then open that address in your browser
```

Only the local machine can reach it. No account, no cloud, no data leaves the laptop.

## Remaining security roadmap
- [ ] macOS Keychain backend for the vault
- [ ] Live order path with an extra per-action confirm + max-spend hard cap
- [ ] Read-only API key test before enabling trading
- [ ] Local rate-limit / kill-switch switch in the UI
