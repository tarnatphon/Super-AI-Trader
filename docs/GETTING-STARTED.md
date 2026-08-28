# Super-AI-Trader — Getting Started (one page)

A local, private grid-trading assistant with an AI that reads markets,
pauses in crashes, trails winners, and can (later) trade real money behind a
hard safety wall. **Everything runs on your computer; keys never leave it.**

## 1. Install / update

```bash
cd /Volumes/AI/super-ai-trader        # (or wherever you cloned it)
git pull origin arena/01a0428c-super-ai-trader

# first time only — private environment
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install ccxt pywebview pystray pillow
```

## 2. Open the app

- **Easiest:** double-click `desktop/Super-AI-Trader.command` (Mac) / `.bat` (Windows).
- Or from the terminal (venv active): `python start_app.py`
- Opens at **http://127.0.0.1:8787** in your browser. Local only.

## 3. First launch

1. **Choose your AI brain** — pick *Built-in AI* (no download) or a local
   Ollama model. Change later in **Local AI brain**.
2. Tap **🔌 Test connection** — all checks should be green (ccxt + live price).
   If Binance is restricted in your region, use **Gate.io**.

## 4. Practice (recommended: do this first)

- **📈 Live market** — real price, EMAs 7/25/99, green/red buy-sell grid.
- **🤖 Multi-coin grids** — type `BNB,SOL,ETH`, **Start grids** (practice money),
  watch each coin: price, P/L, Grid ON / ⏸ paused, and alerts.
- **⏪ Time Machine** — replay past candles bar-by-bar; **Auto-play** to watch fills.
- **🤖 Bot Details** — profit curve, buy/sell ladder, and the **HOLDING / LOCKED**
  smart-exit trail (locks ~7% on a 5%+ runner that reverses ~1%).

## 5. Understand the safety shields (always on)

- **Grid PAUSES in strong trends** (doesn't buy into a crash).
- **Smart trailing exit** rides winners and banks profit on reversal.
- **Crash/power-cut:** on restart it reconciles/cancels stray orders and
  stays stopped until you press start.
- **🛑 SAFE STOP / Stop all** cancels every open order. No restart happens
  while the bot holds orders.
- Alerts also go to your **phone/email** if you set those up (optional).

## 6. First REAL-money trade (only when ready)

Do these in order — the app's **✅ Run safety checklist** enforces them:

1. On the exchange, create a key that is **trade-only, withdrawals OFF, IP allowlisted**.
2. **Connect an exchange** → paste the key, set a vault password (encrypted locally).
3. **REAL-MONEY grids → Run safety checklist**. Must be all green:
   key saved, vault unlocks, **small cap** (start 20–50 USDT/coin), paper-practice done.
4. **Build real grids (no orders yet)** → review the coins and **total cap**.
5. Type **I AGREE** → **ARM REAL GRIDS**. Buys are hard-capped; withdrawals impossible.
6. Watch the first small cycle, then **Stop & cancel all real orders** when done.

## Useful commands

```bash
python -m super_ai_trader doctor   # self-check: python, packages, live Binance price
python -m super_ai_trader ask "set up a safe grid for bitcoin with 500 USDT"
python -m super_ai_trader web      # run the dashboard
```

## Rules to keep you safe

- Treat this as educational; grids can lose money in strong downtrends.
- Start with **paper**, then tiny real caps; never withdraw-enable the key.
- If anything looks wrong, **Stop all** first, then close — reconciles on restart.
- Local data/keys live in `~/.super-ai-trader` (owner-only).
