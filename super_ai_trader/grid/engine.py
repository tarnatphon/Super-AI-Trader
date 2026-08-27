"""Grid trading engine (buy low / sell high inside a range).

Grids place a ladder of buy orders below price and sell orders above price; each
up-step sells the base bought one step lower, banking a small profit. This matches
the owner's goal of MANY small, steady wins rather than one big directional bet.

- arithmetic grid: fixed price step     (best for low-vol / tight ranges)
- geometric grid:  fixed % step         (best for volatile / wide ranges)

Can run in:
- simulation on historical bars (offline, no dependencies) via `simulate_on_bars`
- paper/live against any CCXT exchange ('binance' / 'gateio') via GridTrader

Grid risk note: grids PROFIT in ranges/choppy markets and LOSE in strong trends
(they keep buying as price falls = bags; or sell inventory as it rallies). Always
set range bounds + stop-loss. The risk layer / AI regime filter should pause the
grid in a strong trend.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GridConfig:
    symbol: str = "BTC/USDT"
    lower: float = 0.0           # bottom of grid (set 0 to auto from price ± range_pct)
    upper: float = 0.0
    grids: int = 20              # number of grid lines
    mode: str = "geometric"      # "arithmetic" | "geometric"
    investment: float = 10_000.0 # quote currency (e.g. USDT) deployed
    fee_pct: float = 0.1         # maker fee per side in %
    range_pct: float = 10.0      # auto bounds: ± this % from price if lower/upper unset
    stop_loss_price: float | None = None
    take_profit_price: float | None = None


@dataclass
class GridResult:
    symbol: str
    start_price: float
    end_price: float
    grid_profit: float
    fees_paid: float
    unrealized_pnl: float
    inventory_base: float
    inventory_cost: float
    filled_round_trips: int
    touches: int
    stopped: bool
    final_equity: float
    initial: float = 0.0
    equity_curve: list = field(default_factory=list)

    def summary(self) -> str:
        ret = (self.final_equity / self.initial - 1) * 100 if self.initial else 0.0
        return (
            f"--- GRID {self.symbol} (sim) ---\n"
            f"  Price            : {self.start_price:.2f} -> {self.end_price:.2f} "
            f"({(self.end_price/self.start_price-1)*100:+.2f}%)\n"
            f"  Realized grid P/L: {self.grid_profit:+,.2f}  (fees {self.fees_paid:,.2f})\n"
            f"  Unrealized inv.  : {self.unrealized_pnl:+,.2f}  (holds {self.inventory_base:.6f} base)\n"
            f"  Round-trip fills : {self.filled_round_trips}  (grid touches {self.touches})\n"
            f"  End equity       : {self.final_equity:,.2f} of {self.initial:,.2f} "
            f"({ret:+.2f}%)\n"
            f"  Stopped out      : {self.stopped}\n"
        )


def grid_lines(cfg: GridConfig, ref_price: float) -> list[float]:
    lower = cfg.lower or ref_price * (1 - cfg.range_pct / 100)
    upper = cfg.upper or ref_price * (1 + cfg.range_pct / 100)
    n = cfg.grids
    lines = []
    for i in range(n + 1):
        if cfg.mode == "arithmetic":
            p = lower + (upper - lower) * i / n
        else:  # geometric (equal % spacing)
            p = lower * (upper / lower) ** (i / n)
        lines.append(p)
    return sorted(lines)


def simulate_on_bars(cfg: GridConfig, bars) -> GridResult:
    """Walk historical bars; simulate grid fills using bar high/low crossings.

    We track an inventory slot per grid step: base currency bought at that step and
    waiting to be sold one step higher. Fees charged on each notional.
    """
    ref = bars[0].close
    lines = grid_lines(cfg, ref)
    start_price = bars[0].close
    end_price = bars[-1].close
    step = 1
    fee = cfg.fee_pct / 100

    # Equal quote allocation per buy slot across the lower half of the grid.
    buy_lines = lines[:-1]  # you can buy at every line except the very top
    per_slot_quote = cfg.investment / max(1, len(buy_lines))

    # slot holds base qty that was bought at `lines[k]`, awaiting sale at lines[k+1].
    slot_qty: dict[int, float] = {k: 0.0 for k in range(len(lines) - 1)}
    cash = cfg.investment
    fees_paid = 0.0
    round_trips = 0
    touches = 0
    stopped = False

    def buy_slot(k, price):
        nonlocal fees_paid, cash
        if slot_qty[k] > 0:
            return
        notional = per_slot_quote
        qty = notional / price
        f = notional * fee
        slot_qty[k] = qty
        fees_paid += f
        cash -= notional + f

    def sell_slot(k, price):
        nonlocal fees_paid, cash, round_trips
        qty = slot_qty[k]
        if qty <= 0:
            return 0.0
        proceeds = qty * price
        f = proceeds * fee
        fees_paid += f
        cash += proceeds - f
        slot_qty[k] = 0
        round_trips += 1
        return proceeds

    # Initial state: seed buys on lines below the starting price.
    for k, p in enumerate(buy_lines):
        if p <= start_price:
            buy_slot(k, min(p, start_price))

    equity_curve = []

    def mark_equity(price, date):
        inv_val = sum(slot_qty[k] * price for k in slot_qty)
        equity_curve.append((date, round(cash + inv_val, 2)))

    for bar in bars:
        lo, hi = bar.low, bar.high
        # Stop loss / take profit at grid level.
        if cfg.stop_loss_price and lo <= cfg.stop_loss_price:
            stopped = True
            mark_equity(cfg.stop_loss_price, bar.date)
            break
        if cfg.take_profit_price and hi >= cfg.take_profit_price:
            stopped = True
            mark_equity(cfg.take_profit_price, bar.date)
            break

        # If price dipped to a buy line -> buy that slot.
        for k, p in enumerate(buy_lines):
            if lo <= p and slot_qty[k] == 0:
                buy_slot(k, p)
                touches += 1
        # If price rose to a sell line -> sell the slot one step below.
        for k in range(len(lines) - 1):
            sell_price = lines[k + 1]
            if hi >= sell_price and slot_qty[k] > 0:
                sell_slot(k, sell_price)
                touches += 1
        mark_equity(bar.close, bar.date)

    # If stopped out, mark at the trigger price instead of last bar close.
    if stopped:
        end_price = cfg.stop_loss_price or cfg.take_profit_price or end_price

    # Mark remaining inventory at end price.
    inv_base = sum(slot_qty.values())
    inv_cost = sum(slot_qty[k] * buy_lines[k] for k in slot_qty)
    inv_value = sum(slot_qty[k] * end_price for k in slot_qty)
    unrealized = inv_value - inv_cost
    # Final account value = running cash balance (includes all buy spend, sell
    # proceeds and fees) plus held inventory marked to market.
    final_equity = cash + inv_value
    realized = final_equity - cfg.investment - unrealized
    if equity_curve:
        equity_curve[-1] = (equity_curve[-1][0], round(final_equity, 2))

    return GridResult(
        symbol=cfg.symbol,
        start_price=start_price,
        end_price=end_price,
        grid_profit=round(realized, 2),
        fees_paid=round(fees_paid, 2),
        unrealized_pnl=round(unrealized, 2),
        inventory_base=round(inv_base, 8),
        inventory_cost=round(inv_cost, 2),
        filled_round_trips=round_trips,
        touches=touches,
        stopped=stopped,
        final_equity=round(final_equity, 2),
        initial=cfg.investment,
        equity_curve=equity_curve,
    )


# --------------------------------------------------------------------------- #
# Live / paper trading via CCXT (no hard dependency). Works on binance OR gateio.
# --------------------------------------------------------------------------- #
class GridTrader:
    """Exchange-agnostic grid runner. Use exchange_id='binance' or 'gateio'.

    Paper mode simulates fills from live prices (no keys). Live mode places real
    limit maker orders via CCXT with trade-only API keys.
    """

    SUPPORTED = ("binance", "gateio")

    def __init__(self, exchange_id: str = "binance", paper: bool = True,
                 api_key: str | None = None, api_secret: str | None = None):
        if exchange_id not in self.SUPPORTED:
            raise ValueError(f"exchange must be one of {self.SUPPORTED}")
        self.exchange_id = exchange_id
        self.paper = paper
        self.ex = None
        if not paper:
            import ccxt  # lazy import
            klass = getattr(ccxt, exchange_id)
            self.ex = klass({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})

    def fetch_price(self, symbol: str) -> float:
        if self.paper:
            raise RuntimeError("paper mode needs a price feed; pass live prices or run --real sim")
        t = self.ex.fetch_ticker(symbol)
        return float(t["last"] or t["close"])

    def suggest_range(self, cfg: GridConfig, price: float) -> GridConfig:
        """Fill in bounds/fees sensibly for the chosen exchange."""
        if not cfg.lower:
            cfg.lower = price * (1 - cfg.range_pct / 100)
        if not cfg.upper:
            cfg.upper = price * (1 + cfg.range_pct / 100)
        # Binance spot maker ~0.1% (0.075% with BNB); gate.io ~0.1-0.2%.
        cfg.fee_pct = 0.1 if self.exchange_id == "binance" else 0.15
        return cfg
