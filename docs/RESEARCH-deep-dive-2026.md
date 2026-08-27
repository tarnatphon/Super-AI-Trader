# Deep-Dive Research Before Building: Does AI Trading Actually Work?

> Compiled 2026-08-27. This is the "do the homework before risking a baht" report.
> It covers: (1) whether AI agents make money, (2) where LLMs *actually* have edge per
> peer-reviewed research, (3) real costs, (4) which edges a retail trader can/can't
> capture, (5) **Thailand-specific regulation, exchanges, brokers and tax**, and
> (6) the failure modes that kill most bots. Read alongside
> [`RESEARCH-top-ai-traders-2026.md`](./RESEARCH-top-ai-traders-2026.md).

---

## 1. The honest answer: do AI trading agents make money?

**Sometimes in backtesting, occasionally in live trading, rarely with the consistency
the demos suggest.** This is the near-universal conclusion across independent reviews
and the frameworks' own maintainers.

- **The backtest→live gap is the central problem.** A strategy showing ~50% annual in
  backtest may deliver **10–15% live** after spreads, slippage, commissions, market
  impact, and regime change. If the backtested Sharpe was marginal, live results "can
  easily turn negative." ([Pinggy](https://pinggy.io/blog/best_ai_trading_agents/),
  [dev.to](https://dev.to/lightningdev123/best-ai-trading-agents-in-2026-can-they-really-deliver-consistent-returns-2fgl))
- **TradingAgents' own numbers are caveat-heavy.** The paper reports ~26.6% on AAPL in a
  3-month 2024 backtest vs ~2% baselines, but flags a **Sharpe of 8.21 as implausible**
  ("SR above 2 is very good, above 3 is excellent") and admits the backtest assumes
  **no slippage, no spread, execution at the close, no market impact**, and uses
  **11 LLM + 20+ tool calls per decision**. ([paper walkthrough](https://publication.hikmahtechnologies.com/building-trading-bots-that-think-like-a-trading-firm-unpacking-the-tradingagents-paper-f975ae5b42df))
- **A documented 30-day live run** returned ~7% vs S&P's 4.5% — but with a **22%
  drawdown** most retail couldn't tolerate, and no repeatability guarantee.
  ([Pinggy](https://pinggy.io/blog/best_ai_trading_agents/))
- **Rigorous benchmark (StockBench, arXiv:2510.02209):** LLM agents *can* trade
  profitably and **all models had lower drawdown than buy-and-hold**, but they
  "**rarely outperform simple baselines**." ([StockBench](https://arxiv.org/html/2510.02209v2))
- **Retail reality (CNBC, July 2026):** a retail founder testing agents said he "was
  just losing money consistently" — *"to blindly give an agent and say 'make me
  money' is kind of dumb."* ([CNBC](https://www.cnbc.com/2026/07/28/ai-agents-build-to-trade-24-7-the-future-of-wall-street.html))
- **The correct framing (TradingAgents reviewers):** it's a **structured research
  analyst that forces a bull and bear case — not something to wire to a brokerage.**
  Outputs are **non-deterministic by design** (same ticker/date can give different
  calls), it reasons over public data already priced in, and "eloquence is not alpha."
  ([Twisters AI honest review](https://twistersai.blogspot.com/2026/06/tradingagents-open-source-ai-hedge-fund.html))

> ⚠️ Note: the "I tested 47 agents and lost $11,240" style Medium posts are content
> marketing and their numbers are unverifiable — but their *consistent lessons* (costs,
> slippage, overfitting, regime change) match the credible sources above.

**Implication for our build:** position Super-AI-Trader as a **research + rigorous
validation + decision-support** system with a hard risk layer — *not* an autopilot.
That matches what actually survives live.

---

## 2. Where LLMs genuinely add edge (peer-reviewed evidence)

LLMs are **not** good at predicting price from numbers. They *are* good at reading
text. The research is clear on the split:

| Study | Finding |
|---|---|
| **Lopez-Lira & Tang** ([arXiv:2304.07619](https://arxiv.org/abs/2304.07619), later *Journal of Financial Economics*) | GPT-4 scores news headlines with ~90% hit rate on initial market reaction and predicts 1–2 days of drift, strongest for **small caps and negative news**. But: edge exists only above a **model-capability threshold** (GPT-1/2/Llama2 fail), and **decays as LLM adoption rises**. Costs are decisive: a long-short strategy made ~350% cumulative at **10 bps** costs but only ~50% at **25 bps**. Speed matters — act within ~15 min of news. |
| **Sentiment trading with LLMs** (*Finance Research Letters*, [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1544612324002575)) | Advanced LLM (OPT/GPT-class) predicted next-day returns with **74.4% accuracy**; long-short after 10 bps costs → **Sharpe 3.05**, ~355% over 2 years. Dictionary/FinBERT far weaker. |
| **Hybrid ML + LLM for NASDAQ-100** ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12191900/)) | For **technical/price signals, pure ML beat adding the LLM**; for **fundamental & entropy/complex-context signals, the LLM added substantial value**. Blend weights matter. |
| **LLM forecast biases** ([AEA 2026 paper](https://www.aeaweb.org/conference/2026/program/paper/zNrQ4Yn6)) | GPT-4o is **systematically over-optimistic**, over-extrapolates recent returns, and its confidence intervals are **too narrow** (underestimates tail moves). Bias is resistant to prompt engineering. |

**The takeaway for architecture:**
- Use the LLM on **unstructured text** — news headlines, earnings, filings, sentiment —
  where the literature shows durable (if decaying) edge.
- Use **deterministic/quant methods** (or classical ML) for price/technical signals.
- Treat LLM directional calls as **biased toward optimism** → size conservatively, and
  the risk layer must distrust conviction.
- Edge is **small, fast, and cost-sensitive** — after 25 bps round-trip most retail
  text-signal edge vanishes.

---

## 3. The real costs (most backtests ignore these)

**LLM inference:**
- A full TradingAgents ticker run = 11 LLM + 20 tool calls; frontier-model runs cost
  **~$0.30–0.50 per ticker per decision**. Backtesting a year × 10 stocks daily is
  expensive. ([Hikmah](https://publication.hikmahtechnologies.com/building-trading-bots-that-think-like-a-trading-firm-unpacking-the-tradingagents-paper-f975ae5b42df), [Pinggy](https://pinggy.io/blog/best_ai_trading_agents/))
- **Mitigation:** use **DeepSeek API or local Ollama** (cuts LLM cost ~80–90%), cache
  responses, compress prompts, only call the LLM for the text layer not every bar.

**Trading frictions (the ones that actually kill edge):**
- Model **slippage of ~0.3% per trade** as a baseline for liquid markets; DEX trades can
  lose up to **~3% to slippage**; add commission + spread on top.
- Real example: an XLE strategy looked fine at zero costs but at **2 ticks slippage +
  commission its profit factor fell to ~0.95** — i.e. the "edge" was just costs, and the
  strategy was a loser. ([AlphaInsider](https://blog.alphainsider.com/how-i-used-ai-to-build-a-hedge-fund-of-trading-strategies/))
- Rule of thumb from the research: **if gross edge per trade isn't comfortably larger
  than ~2× your round-trip cost, there is no trade.**

**Infrastructure:** a VPS for 24/7 uptime is ~$5–10/mo; data feeds (tick/level-2) can
cost far more. Our build runs free locally on the MacBook for research; paid only when
going live.

---

## 4. Which edges can a retail trader actually capture in 2026?

**Effectively impossible for retail (don't bother):** sub-second latency arbitrage,
HFT scalping, deep-book market making, institutional order-flow / news-feed arb,
index-rebalance front-running. ([Everstrike](https://blog.everstrike.io/7-arbitrage-strategies-are-still-accessible-to-retail-quants-in-2025/), [Algotradingspace](https://algotradingspace.com/top-forex-algorithmic-trading-strategies))

**Accessible but small / competitive (verify net of fees):**
- **Funding-rate / cash-and-carry (crypto)** — delta-neutral spot+perp to harvest
  funding; returns depend on funding staying positive; main risks are exchange
  counterparty and liquidation. Hummingbot automates parts.
- **Cross-exchange / triangular arb (crypto)** — real but **expect to hand ~half of
  profit to fees** unless you have fee tiers; fragmented crypto venues help.
- **Statistical arbitrage at moderate frequency** — pairs/cointegration; correlation
  breaks are the risk; fees matter.
- **Prediction-market cross-platform arb (Kalshi/Polymarket)** — net edge usually only
  **1–5¢ per contract after fees**, long dry spells. ([tech-insider](https://tech-insider.org/prediction-markets/prediction-market-strategy/))

**Most robust for serious retail (per veteran r/algotrading practitioners):**
- **Trend following** and **mean reversion** — but study *when each works* and combine
  them; they're complementary across regimes.
- **Diversify across uncorrelated markets/systems** (e.g. rates vs equity index).
- **Position sizing & risk are the real edge** — "single-signal strategies with an edge
  to screen out likely losers," defined-risk structures.
- **Realistic benchmark:** world-class *retail* algo performance is roughly
  **10–25% annual with Sharpe > 1.0**; expect **2,000–3,000 hours** and many failures.
  Anyone promising 100%+ is taking huge risk or marketing. ([r/algotrading](https://www.reddit.com/r/algotrading/comments/1jia5ng/looking_for_realistic_advice_for_chance_of/), [InvestingWithAI](https://investingwithai.com/algorithmic-trading-beginners-guide/))

---

## 5. 🇹🇭 Thailand-specific: what you can actually trade and the rules

This matters because your legal venue, API access, and tax treatment decide the build.

### Crypto — legal, regulated, and tax-advantaged
- **Legal & regulated** by the **Thai SEC**. Since **Jan 2025 only SEC-licensed
  exchanges may legally serve Thai residents**; unlicensed offshore platforms risk
  government blocking under the 2026 cybercrime law. ~52% of crypto complaints involve
  offshore exchanges. ([OSL](https://www.osl.com/hk-en/bits/article/crypto-investing-in-thailand), [Zipmex TH guide](https://zipmex.com/blog/is-crypto-legal-in-thailand/))
- **Licensed exchanges** (THB rails): **Bitkub** (local leader, ~163 coins, **spot only,
  THB pairs, ~0.25% fee, has an API**), **Binance TH** (Gulf Binance), **Upbit Thailand**,
  **Orbix** (SCB-backed), **KuCoin Thailand**, **MEXC Thailand**, Bitazza, InnovestX,
  WaanX, TDX. ([Bitzup 2026 guide](https://bitzup.com/blog/crypto-trading-exchanges-in-thailand/), [TradingFinder Bitkub](https://tradingfinder.com/exchanges/bitkub/))
- **Tax:** individual investors get a **capital-gains tax waiver on crypto profits via
  licensed domestic exchanges until 31 Dec 2029** (previously 15% withholding).
  Corporates are excluded. Foreigners/expats qualify under the same KYC (may require
  in-person "dip-chip" ID). ([Zipmex](https://zipmex.com/blog/is-crypto-legal-in-thailand/))
- SEC keeps an **approved-coin list** (BTC, ETH, XRP, XLM, USDC, USDT, …) — verify at
  sec.or.th before trading anything exotic. Crypto lending is prohibited; crypto
  derivatives are being brought under the Derivatives Act.

### Thai equities (SET / TFEX) — program trading is gated
- Using algorithms/"Program Trading" on SET requires **prior exchange approval** and is
  oriented to members/market makers — not a casual retail-API setup. Market making needs
  licensing. ([Chambers Fintech 2026: Thailand](https://practiceguides.chambers.com/practice-guides/fintech-2026/thailand/trends-and-developments))
- Practical implication: **don't target SET for your first algo build.**

### US/global markets from Thailand — API-friendly retail path
- Independent broker testing ranks **Alpaca** as the best algo broker for Thailand
  (excellent API, free US stock/ETF trading, **paper trading**, Python/JS/Go, $0 min),
  followed by **OANDA** (FX) and **Interactive Brokers** (widest products, TWS API).
  ([BrokerChooser Thailand 2026](https://brokerchooser.com/best-brokers/best-brokers-for-algo-trading-in-thailand))

### Recommended venue for our build
1. **Crypto via CCXT** against a **Thai-licensed venue** (Binance TH / Bitkub API) —
   24/7 markets, API-native, tax-advantaged for you, non-custodial trade-only keys.
2. **US equities via Alpaca paper API** for the stock-multi-agent strategies (free,
   great for research; switch to live only after validation).
3. **Avoid** routing real money through unlicensed offshore exchanges.

---

## 6. Failure modes to design against (backtesting pitfalls)

From the practitioner and academic sources:

1. **Overfitting / curve-fitting** — parameters tuned to history that never repeat.
   Mitigate with walk-forward and out-of-sample testing; keep strategies simple.
2. **Data-snooping** — running 100 backtests until one looks good finds coincidence,
   not edge. Pre-register the hypothesis.
3. **Look-ahead bias** — using data not available at decision time (use Jesse/Lean-style
   engines that prevent it). Mind LLM data-cutoff leakage (StockBench caught GPT-5
   "predicting" 2021 AAPL from memorized history).
4. **Survivorship bias** — datasets that exclude delisted companies.
5. **Ignoring costs & slippage** — the #1 reason backtests lie (Section 3).
6. **Regime change** — a strategy fit to one bull/chop/bear regime fails in the next;
   classify regime and scale exposure (our risk layer does this).
7. **LLM non-determinism** — same input, different call. Log decisions; don't treat LLM
   output as a stable signal; gate it behind rules.
8. **Mindset:** *"Backtesting is not about proving you're right — it's about trying to
   prove your strategy wrong."* If you can't break it in sim, you might have something.

**Validation gates before any live capital:**
backtest (out-of-sample, with realistic costs) → **paper trade ≥30–90 days** with logged
decisions → compare *what the agent said vs what the market did* → live at 10–25% size →
scale only after proven edge in your own market.

---

## 7. What this means for the Super-AI-Trader roadmap

Concrete, evidence-based adjustments to our plan:

- ✅ Keep the **multi-agent research desk + hard deterministic risk layer** (matches what
  works: research aid, not autopilot).
- 🎯 Put the **LLM on the text/sentiment/news/fundamentals layer** (where academia shows
  edge); keep **price/technical signals deterministic or classical-ML**.
- 💸 Run the LLM **locally via Ollama (or DeepSeek)** to cut cost 80–90%; only call it for
  the text layer, never per bar; cache aggressively.
- 📉 **Model realistic costs** (≥0.3% slippage + commission) in the backtest engine —
  without this the backtest is fiction. Add a walk-forward / out-of-sample mode.
- 🧭 Add a **regime filter** and **decision logging + replay** (already partly present).
- 🇹🇭 Target **crypto via CCXT on a Thai-licensed exchange** first (tax-advantaged,
  API-friendly), and **Alpaca paper** for equities. Skip SET program trading for now.
- 🧪 Build the **"RBI" research→backtest agent** so the AI proposes strategies but the
  *engine* validates them out-of-sample with costs — humans only promote proven ones.
- 🚫 Never market it as guaranteed/passive income; the CFTC warns such claims are fraud.

---

### Sources
- Profitability: [Pinggy](https://pinggy.io/blog/best_ai_trading_agents/) · [TradingAgents honest review](https://twistersai.blogspot.com/2026/06/tradingagents-open-source-ai-hedge-fund.html) · [paper walkthrough](https://publication.hikmahtechnologies.com/building-trading-bots-that-think-like-a-trading-firm-unpacking-the-tradingagents-paper-f975ae5b42df) · [StockBench](https://arxiv.org/html/2510.02209v2) · [CNBC](https://www.cnbc.com/2026/07/28/ai-agents-build-to-trade-24-7-the-future-of-wall-street.html)
- Academic edge: [Lopez-Lira & Tang](https://arxiv.org/abs/2304.07619) · [LLM sentiment (Finance Research Letters)](https://www.sciencedirect.com/science/article/pii/S1544612324002575) · [hybrid ML/LLM NASDAQ-100](https://pmc.ncbi.nlm.nih.gov/articles/PMC12191900/) · [LLM forecast bias (AEA)](https://www.aeaweb.org/conference/2026/program/paper/zNrQ4Yn6)
- Costs: [AlphaInsider strategy costs](https://blog.alphainsider.com/how-i-used-ai-to-build-a-hedge-fund-of-trading-strategies/)
- Retail edges: [Everstrike arb](https://blog.everstrike.io/7-arbitrage-strategies-are-still-accessible-to-retail-quants-in-2025/) · [r/algotrading realistic advice](https://www.reddit.com/r/algotrading/comments/1jia5ng/looking_for_realistic_advice_for_chance_of/) · [InvestingWithAI guide](https://investingwithai.com/algorithmic-trading-beginners-guide/)
- Thailand: [Chambers Fintech 2026 TH](https://practiceguides.chambers.com/practice-guides/fintech-2026/thailand/trends-and-developments) · [BrokerChooser algo brokers TH](https://brokerchooser.com/best-brokers/best-brokers-for-algo-trading-in-thailand) · [Bitzup exchanges 2026](https://bitzup.com/blog/crypto-trading-exchanges-in-thailand/) · [Zipmex legality/tax](https://zipmex.com/blog/is-crypto-legal-in-thailand/) · [OSL TH](https://www.osl.com/hk-en/bits/article/crypto-investing-in-thailand) · [Bitkub review](https://tradingfinder.com/exchanges/bitkub/)
