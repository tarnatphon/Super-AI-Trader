# Grid Trading — Binance vs Gate.io and how it fits Super-AI-Trader

Grid trading = place a ladder of buy orders below price and sell orders above it;
each up-step sells the base bought one step lower, banking a small profit. It is a
**steady small-wins** strategy that fits the project goal (consistent gains, not high
win % / one big directional bet). It profits in **range/choppy** markets.

## Binance vs Gate.io (researched 2026-08)

| Factor | **Binance** (best primary) | **Gate.io** (best secondary) |
|---|---|---|
| Spot maker fee | 0.1% (≈0.075% paying with BNB) | 0.1–0.2% (discount with GT token) |
| Futures fee | 0.02% / 0.05% | 0.02% / 0.05–0.075% |
| Liquidity / fills | **Deepest, tightest spreads** (fewer missed grid fills) | Good, thinner on small caps |
| Coin/pair selection | ~1,500 | **3,500+ coins / 2,900+ pairs**, newest listings |
| Grid bots | Spot + futures grid, leverage bots | **9 bot types**: spot/futures/margin/infinite grid, martingale, rebalance, spot-futures arb |
| API | Excellent (CCXT `binance`) | Excellent (CCXT `gateio`) |
| Thailand | Licensed as **Binance TH** (Thai SEC) — regulated, tax-eligible | Offshore/global; **not** Thai-SEC licensed — verify before using |

### Recommendation (best usage combined)
- **Primary = Binance / Binance TH** for major pairs (BTC/USDT, ETH/USDT): deepest
  liquidity and lowest effective maker fee = grid fills happen at the intended prices
  and costs don't eat the small grid profit. CCXT id `binance`; use the licensed
  **Binance TH** for local/THB rails and the tax exemption.
- **Secondary = Gate.io** when you want a coin/grid variant Binance lacks (new listings,
  infinite/margin grid, martingale, spot-futures arb). Note the Thai-SEC licensing
  caveat — the app defaults to Binance for Thai users.
- The grid engine is **exchange-agnostic via CCXT**: the same strategy runs on either
  by switching `--exchange`. Backtest grids in-app first, then deploy with a
  **trade-only API key (withdraw disabled)**.

## Using the grid module

The grid runs **offline in simulation** on our synthetic/real bars with no keys, so you
can tune range/grids before risking funds:

```bash
# simulate a 25-line geometric grid on BTC over a ±15% range, Binance fees
python3 -m super_ai_trader grid --ticker BTC --exchange binance \
    --range-pct 15 --grids 25 --mode geometric --investment 10000

# wider range, Gate.io fee profile, with protection
python3 -m super_ai_trader grid --ticker ETH --exchange gateio \
    --range-pct 20 --grids 30 --fee 0.15 \
    --stop-loss 1800 --take-profit 2600

# explicit price bounds
python3 -m super_ai_trader grid --ticker BTC --lower 50000 --upper 70000 --grids 30
```

Parameters mirror the exchange bot config (Binance/Gate spot-grid):
- `--lower` / `--upper` (or `--range-pct` for auto bounds ±% from current price)
- `--grids` number of grid lines (use 15–30 sideways, more in high vol)
- `--mode geometric` (fixed-% steps, volatile) or `arithmetic` (fixed steps, low vol)
- `--stop-loss` / `--take-profit` (must sit outside the range)

## Grid risk — read this
- **Trend risk (the big one):** grids earn small gains in ranges, but in a strong
  **downtrend they keep buying into bags** (the sim shows positive realized P/L but
  large *unrealized* inventory loss). In a strong **uptrend** they sell inventory early
  and underperform buy-and-hold.
- **Always set range bounds and a stop-loss**; don't run a grid into free-fall.
- **Fees:** grid round-trips are many and small — maker fee vs grid spacing decides
  whether there's edge. Keep grid spacing comfortably larger than 2× round-trip fee.
- Next step: gate the grid with our **AI regime filter** — pause/stop the grid when the
  learned model + order flow detect a strong trend, and re-enable it in ranges.
```
