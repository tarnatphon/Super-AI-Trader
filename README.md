# Super-AI-Trader

The best open AI trader — a **multi-agent AI trading firm** in Python. Specialist
AI agents research markets and debate like a real trading desk; a deterministic
risk manager has veto power; a backtest engine executes. Runs **out of the box with
zero dependencies and zero API keys** (synthetic data + heuristic agents), and
scales up to real data (yfinance) and real LLMs (OpenAI / DeepSeek / **local Ollama**).

> ⚠️ Educational/research software. Not financial advice. Backtests are not returns.

## Quick start

```bash
# zero install needed — uses only the Python standard library
python3 -m super_ai_trader ask "set up a safe grid for Bitcoin with 1000 USDT"
python3 -m super_ai_trader ask "analyze Ethereum — should I buy?"
python3 -m super_ai_trader ask "is my money safe?"
python3 -m super_ai_trader backtest --ticker DEMO --trades
python3 -m super_ai_trader analyze  --ticker DEMO

# real market data (optional): pip install yfinance
python3 -m super_ai_trader backtest --ticker AAPL,MSFT,NVDA --real

# real LLM agents (optional): export OPENAI_API_KEY=...  or point at local Ollama
python3 -m super_ai_trader analyze --ticker AAPL --real --llm

# spot grid bot simulation (Binance primary / Gate.io secondary; CCXT live later)
python3 -m super_ai_trader grid --ticker BTC --exchange binance --range-pct 15 --grids 25

# simple, secure local web app (kid- and senior-friendly; localhost only)
python3 -m super_ai_trader web        # then open http://127.0.0.1:8787
```

📱 **Simple web dashboard** (original design, practice mode default, "Safety Shield"):
see **[docs/SECURITY-UX.md](docs/SECURITY-UX.md)**.

Grid trading (Binance vs Gate.io choice, fees, risk): see
**[docs/GRID-TRADING.md](docs/GRID-TRADING.md)**.

## How it works

```
data → indicators → [technical · momentum · sentiment · fundamental · risk] analysts
     → bull vs bear debate → trader → portfolio manager
     → deterministic RISK MANAGER (veto + sizing + kill switch)
     → backtest / paper / live engine
```

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for full details and the research
behind the design:
- **[docs/RESEARCH-top-ai-traders-2026.md](docs/RESEARCH-top-ai-traders-2026.md)** — top
  platforms, open-source frameworks, and creators (Trade Ideas, TradingAgents,
  ai-hedge-fund, FinRL, Freqtrade, Moon Dev, Kevin Davey, …).
- **[docs/RESEARCH-deep-dive-2026.md](docs/RESEARCH-deep-dive-2026.md)** — does AI
  trading actually make money, where LLMs have real edge (academic evidence), costs,
  retail-accessible edges, backtesting pitfalls, and **Thailand regulation/brokers/tax**.

## Tests

```bash
python3 tests/test_smoke.py
```

## Core principle

> The AI *advises* — a hard, deterministic risk layer *vetoes* — a battle-tested
> engine *executes*. Always: backtest → paper trade → small live. Never hand an
> LLM unchecked order execution.
