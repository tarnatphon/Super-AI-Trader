# Plan: a fully-local, AI-run trading app on every device

_Goal: one app for **Mac, Windows, Linux, iPhone, Android & tablet**, **not
cloud-based**, with a **local AI that does the work** — and security first._
_Verified against 2026 facts._

---

## 1. Short answer
**Yes, it's possible.** Everything needed exists today:
- **On-device LLMs** run offline on phones and laptops in 2026: `llama.cpp` (GGUF
  models like Qwen 3 1.7B–4B, Phi-4-mini, Gemma 3 1B) at ~10–40 tokens/sec on a
  modern phone; Apple's built-in **Foundation Models (~3B, iOS 26+)** and Google's
  **Gemini Nano** on Android; bigger models (7B–70B) on a Mac via **Ollama / MLX**.
  ([local LLM on phones 2026](https://localaimaster.com/blog/run-llm-on-phone), [on-device mobile LLMs](https://ztabs.co/blog/on-device-llms-mobile-2026))
- **One codebase for all 5 platforms**: **Tauri 2** (Rust backend + web UI) ships
  Mac/Windows/Linux/Android/iOS; **Flutter + Rust core** is the alternative if
  mobile is the priority. ([Tauri 2](https://www.mayhemcode.com/2026/07/build-mobile-and-desktop-apps-from-one-codebase.html))

**But two honest constraints:**
1. **A trading bot must be "always-on".** Phones/tablets suspend apps when idle, so
   they *cannot* run a 24/7 bot reliably. → The **always-on trading node is a
   computer** (your MacBook/Windows/Linux machine at home). The **phone/tablet is the
   remote control & dashboard**.
2. **"Local" does not mean offline from the exchange.** Placing orders on
   Binance/Gate.io *requires* the internet. "Local" here means: **no cloud AI, no
   cloud server holding keys — keys, data and AI all live on your own devices.**

---

## 2. Recommended architecture

```
   ┌──────────────────────────── LOCAL HOME NODE (always-on) ───────────────────────────┐
   │  Mac mini / MacBook / Windows / Linux box                                          │
   │                                                                                     │
   │   Local AI brain (no cloud):                                                        │
   │     • Desktop: Ollama or llama.cpp / MLX  (Qwen / Llama / Phi 7B–70B)               │
   │     • Understands: "trade 1,000 USDT on Bitcoin, safe mode" → sets grid             │
   │                                                                                     │
   │   Trading engine (Rust core / our Python now):                                      │
   │     grid · order-flow · learned model · risk manager · kill switch                 │
   │                                                                                     │
   │   Key vault: OS Keychain / Keystore (encrypted, never sent anywhere)                │
   │   Exchange link: CCXT/REST/WebSocket → Binance · Gate.io · others  (trade-only)    │
   └───────────────▲───────────────────────────────────────────────┬────────────────────┘
                   │  encrypted local network (or Tailscale VPN,    │  internet (orders/market data)
                   │  end-to-end; NOT a public cloud)              ▼
        ┌──────────┴───────────┐                              ┌───────────────┐
        │  Phone / Tablet      │                              │  Exchanges    │
        │  iPhone · Android    │                              │ Binance, Gate │
        │  - remote dashboard  │                              │ (funds stay   │
        │  - start/stop, P&L   │                              │  on exchange) │
        │  - talk to the AI    │                              └───────────────┘
        │  - small on-device   │
        │    model (1–3B) for  │
        │    chat when away    │
        └──────────────────────┘
```

- **Local AI does all the thinking**: you talk to it in plain language; it configures
  grids, reads order-flow, explains decisions, and runs the safety checks. It never
  sends your data to OpenAI/Google. (Optional "use a cloud model" toggle for harder
  reasoning — off by default.)
- **The deterministic engine + risk manager still holds the keys to order flow.**
  The AI *proposes*, the safety layer *disposes* — same principle we already built.
- **Phones** either (a) remote-control the home node, or (b) run a tiny 1–3B local
  model for chat/Q&A — but the actual trading lives on the always-on node.

## 3. Platform matrix

| Platform | App | Runs the bot 24/7? | Local AI | Key storage |
|---|---|---|---|---|
| **macOS** | Tauri/Flutter app | ✅ yes (ideal node) | Ollama/MLX, 7B–70B | Keychain |
| **Windows** | Tauri/Flutter app | ✅ yes | Ollama/llama.cpp, up to big models | Credential Manager |
| **Linux** | Tauri/Flutter app | ✅ yes (great on a cheap mini-PC/VPS you own) | Ollama/llama.cpp | libsecret/keyring |
| **iPhone / iPad** | Tauri/Flutter app | ⚠️ remote + light AI | Apple Foundation Models / 1–3B GGUF | iOS Keychain |
| **Android** | Tauri/Flutter app | ⚠️ remote + light AI | Gemini Nano / llama.cpp 1–4B | Android Keystore |

A **cheap always-on option**: a Mac mini, a Windows mini-PC, or a small Linux box at
home runs the node; your phone controls it from anywhere via end-to-end VPN
(Tailscale/Headscale — peer-to-peer, not a cloud you must trust).

## 4. Tech stack (one codebase)
- **Core engine:** **Rust** for the shipping product (fast, memory-safe, runs on every
  OS incl. iOS/Android; can embed `llama.cpp` and the exchange logic). _Our current
  Python engine is the prototype and runs great on desktop today._
- **UI:** **Tauri 2** (Rust + simple HTML/UI, tiny secure binaries, all 5 platforms),
  or **Flutter** if you want a fully-native mobile feel.
- **Local AI:** `llama.cpp`/GGUF models everywhere; **Ollama/MLX** on desktop;
  Apple Foundation / Google Gemini Nano on mobile for zero-download on-device AI.
- **Exchanges:** one abstraction over **CCXT** (100+ venues) or native Rust clients.
- **Secrets:** native keystores per OS (Keychain / Credential Manager / Android
  Keystore / libsecret) — no plaintext, no cloud.
- **Network:** TLS, trade-only keys, IP allowlist, end-to-end local remote channel.

## 5. Security (still priority #1) in a local-full-stack world
- Keys **never leave the device**; stored in the OS key vault; not in logs/screens.
- **Trade-only + withdrawals OFF + IP allowlist**; per-user caps and kill switch.
- The node binds to localhost; remote control goes over an authenticated,
  end-to-end-encrypted channel (Tailscale or your own WireGuard) — never open a port
  to the internet.
- Local-only means **no vendor database to breach** (the 3Commas lesson): even if
  your app is attacked, there's no central store of other people's keys.

## 6. App-store reality
- **Desktop**: distribute installers directly (and optionally signed/notarized) — easy.
- **iOS/Android app stores**: apps that *place trades* can face review and may expect
  brokerage/compliance disclosures; many crypto apps distribute on Android more
  freely and use TestFlight/Enterprise on iOS. Plan for a "companion/monitor"
  mobile app first (view + approve), live trading on the desktop node.

## 7. Phased roadmap (local, all platforms)
- **Now (prototype, done in Python):** local engine, grid, order-flow learning,
  encrypted vault, simple localhost web UI.
- **Step 1:** add **CCXT live/paper** trading + a local-Ollama assistant that takes
  plain-English instructions on the desktop node.
- **Step 2:** package the desktop node as a **Mac/Windows/Linux app (Tauri/Rust)** with
  keychain storage and a mobile **remote-control companion** (same account, E2E).
- **Step 3:** on-device mobile model for chat; full installers; TestFlight/Play beta.
- **Step 4:** hardening, independent security review, then public release.

**Bottom line:** local-AI, no-cloud, all-platform is achievable. Keep the *brain and
the 24/7 trading on an always-on computer*, make phones/tablets the friendly remote
control, store keys in OS keystores, and let the local AI drive everything through
our existing safety layer.
