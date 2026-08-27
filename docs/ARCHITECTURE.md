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
python3 -m super_ai_trader backtest --ticker DEMO --trades
python3 -m super_ai_trader backtest --ticker AAPL,MSFT,NVDA --real   # needs: pip install yfinance
python3 -m super_ai_trader analyze  --ticker DEMO                     # print one AI-firm decision as JSON
```

Run tests:
```bash
python3 tests/test_smoke.py        # no pytest needed
# or: pip install pytest && python -m pytest tests/
```

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
- [ ] Paper-trading mode against live quotes (Alpaca / CCXT)
- [ ] Live execution connector (non-custodial, trade-only API keys)
- [ ] Strategy R&D agent ("RBI": research → AI writes backtest → validate, Moon-Dev style)
- [ ] Web dashboard + Telegram bot
- [ ] Portfolio optimization across multiple tickers
