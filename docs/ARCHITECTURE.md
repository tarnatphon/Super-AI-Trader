# Super-AI-Trader — Architecture & Usage

A multi-agent **AI trading firm** in Python. The design follows the 2026 state of
the art (see [`RESEARCH-top-ai-traders-2026.md`](./RESEARCH-top-ai-traders-2026.md)):
specialist LLM agents research and debate like a trading desk, while a **deterministic
risk module has absolute veto power** and a backtest engine executes.

> ⚠️ **Educational/research software. Not financial advice. Not for live trading with
> real money without extensive out-of-sample testing and paper trading.**

## Quick start (runs with zero dependencies, zero API keys)

```bash
# from the repo root (e.g. /Volumes/AI/super-ai-trader on your MacBook)
python3 -m super_ai_trader analyze  --ticker DEMO     # buying/selling pressure + buy/sell zones + votes
python3 -m super_ai_trader learn    --ticker DEMO     # train the ML model, validate out-of-sample, show live read
python3 -m super_ai_trader backtest --ticker DEMO     # OOS backtest (order-flow + learned model + costs)
python3 -m super_ai_trader backtest --ticker AAPL,MSFT --real   # real data: pip install yfinance
```

Run tests:
```bash
python3 tests/test_smoke.py        # no pytest needed
# or: pip install pytest && python -m pytest tests/
```

## The "learn real buying & selling" layer

The bot learns from **order flow / market microstructure**, predicts the next move,
and knows *where* to buy and sell:

- **Order flow** (`data/orderflow.py`): estimates aggressive **buy vs sell pressure**
  from the tape — Close-Location-Value signed volume, **volume delta**, **cumulative
  delta**, **order-flow imbalance**, and cumulative-delta/price **divergence** (quiet
  accumulation/distribution). The `OrderFlowAgent` only acts when buyers/sellers are
  clearly in control **and** price is at the right zone. (With tick data later, feed
  exact aggressor side through the same interface.)
- **Support / resistance zones** (`data/levels.py`): confirmed swing lows (**demand /
  buy zone**) and swing highs (**supply / sell zone**) — never using future bars — with
  suggested stops beyond the zone.
- **Learned model** (`learning/`): a dependency-free logistic regression trains on the
  first 60% of history and is **validated out-of-sample** on the rest (no look-ahead).
  Features include the order-flow, levels, momentum and volatility signals; the
  `LearnedAgent` only trades on high-confidence P(up) calls, preferring entries at
  support (buys) / resistance (sells). `backtest` trains on the past and **trades only
  the unseen window**, so results are honest.
- **Realistic costs**: a per-side cost (default 0.1%) is charged on every entry/exit,
  per the research finding that ignoring costs manufactures fake edge.

> Backtests of the simple learned model are around chance on synthetic data — that is
> the *correct* output: the system validates edge instead of overfitting it. Real edge
> comes from better data (tick/order flow, news sentiment) and careful validation.

## Objective: STEADY gains, not win-rate gambling

The project goal is **not** the highest win % — it is a consistent **~2–5% per month**
with tight drawdowns (steady compounding). The system is tuned and measured for that:

- **Take-profit at a reward:risk multiple** (`take_profit_r_multiple`, default 1.5R) so
  winners are banked at a predefined target instead of being given back.
- **`--profile steady`** (default): smaller risk per trade (0.5% to stop), 15% max
  position, max 2 positions, 1.5% daily-loss kill switch, smaller chop/bear sizing.
  `--profile aggressive` exists for comparison with looser settings.
- **Steadiness KPIs** reported each backtest (NOT win rate as the headline):
  - % profitable months, average/best/worst monthly return
  - monthly **Sharpe** and **Sortino**, **profit factor** (gross win / gross loss)
  - a `Target band` check that flags whether average monthly return lands in 2–5%.

```bash
python3 -m super_ai_trader backtest --ticker BTC --profile steady
python3 -m super_ai_trader backtest --ticker BTC --profile aggressive   # comparison
```

### Manually adjust every percentage

All key percentages are overridable on the command line (flags beat the profile):

| Flag | Meaning | Steady default |
|------|---------|----------------|
| `--risk-per-trade %` | equity risked to the stop per trade | 0.5 |
| `--max-position %` | max notional in one position | 15 |
| `--daily-loss %` | daily loss kill-switch | 1.5 |
| `--take-profit-r X` | take-profit reward:risk multiple | 1.5 |
| `--take-profit-pct %` | fixed % profit target (overrides R) | none |
| `--target-low %` / `--target-high %` | monthly target band for the check | 2 / 5 |
| `--cost %` | trading cost per side | 0.1 |

```bash
# Example: slightly more aggressive steady tuning
python3 -m super_ai_trader backtest --ticker BTC --risk-per-trade 0.75 \
    --max-position 20 --daily-loss 2 --take-profit-r 2 --target-low 2 --target-high 6
```

> ⚠️ Watch the **profit factor** and **costs**, not win rate. A small fixed take-profit
> with frequent trading can show a high win % but lose money once costs are included.

> On random synthetic data the steady profile correctly produces near-flat returns with
> sub-1.5% drawdowns and a profit factor >1 — i.e. it does not *manufacture* fake yield.
> Hitting a real 2–5%/mo requires genuine edge from live order-flow/tick data and
> validated strategies; the framework measures exactly that as we add real data feeds.

## The agent desk

```
data (synthetic / yfinance)
   └─> indicators (SMA, EMA, RSI, MACD, ATR, Bollinger)
         └─> RESEARCH ANALYSTS (each emits a Signal: action + conviction + rationale)
               ├─ TechnicalAnalyst   (RSI, trend, Bollinger, MACD)
               ├─ MomentumAnalyst    (20d/60d returns)
               ├─ SentimentAnalyst   (headlines via LLM, else tape proxy)
               ├─ FundamentalAnalyst (financials via LLM, else long-trend proxy)
               └─ RiskAnalyst        (volatility regime warning)
                     └─> BULL vs BEAR researchers debate
                           └─> TRADER proposes (net conviction, ATR stop)
                                 └─> PORTFOLIO MANAGER decides action + regime
                                       └─> RISK MANAGER (deterministic) vetoes / sizes
                                             └─> BACKTEST ENGINE executes (or paper/live)
```

Every agent has a **transparent heuristic brain** (works offline) and an optional
**LLM brain** (set `--llm` + an API key). The LLM only *advises* — it never places
orders directly.

## Enabling real AI (LLM) agents

The LLM client is OpenAI-compatible, so it works with OpenAI, DeepSeek, Groq,
OpenRouter, or a **fully local** model via Ollama:

```bash
# Cloud (example: OpenAI)
export OPENAI_API_KEY=sk-...
python3 -m super_ai_trader analyze --ticker DEMO --llm

# Fully local with Ollama (no data leaves your MacBook)
ollama pull llama3.1
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=llama3.1
export LLM_API_KEY=ollama          # any non-empty string
python3 -m super_ai_trader analyze --ticker DEMO --llm
```

## The risk layer (`risk/manager.py`) — no LLM, hard rules

Layered controls (the community-proven checklist from the research):
1. **Per-trade sizing** from stop distance — risk a fixed % of equity (default 1%).
2. **Max position notional** (25%) and **max concurrent positions** (3).
3. **Daily-loss kill switch** (default -3% → flatten & halt until reset).
4. **Volatility/stale-data checks** (ATR too high or too low → block entry).
5. **Regime-based sizing** — smaller positions in chop/bear.

## Roadmap

- [x] Synthetic + real (yfinance) data, standard indicators
- [x] 5 analyst agents + bull/bear debate + trader + portfolio manager
- [x] Deterministic risk manager (sizing, kill switch, circuit breakers, regime scaling)
- [x] Event-driven long/short backtest with equity curve & trade log
- [x] Optional LLM agents (cloud or local Ollama), heuristic fallback
- [x] **Order-flow / buy-vs-sell pressure** (volume delta, cumulative delta, divergence)
- [x] **Support/resistance buy & sell zones** with zone-aware stops
- [x] **Learned ML model** trained out-of-sample to predict the next move (pure Python)
- [x] **Realistic per-trade costs** and out-of-sample-only backtest window
- [ ] Real tick/Level-2 order-flow feed (Bitkub/Binance TH via CCXT; Alpaca for stocks)
- [ ] Paper-trading mode against live quotes (Alpaca / CCXT)
- [ ] Live execution connector (non-custodial, trade-only API keys)
- [ ] Strategy R&D agent ("RBI": research → AI writes backtest → validate, Moon-Dev style)
- [ ] Web dashboard + Telegram bot
- [ ] Portfolio optimization across multiple tickers
