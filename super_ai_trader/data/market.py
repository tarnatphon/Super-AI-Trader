"""Market data layer.

Generates realistic synthetic OHLCV data (so the system runs with zero API keys)
and optionally loads real data from Yahoo Finance via `yfinance` if installed.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Bar:
    """One OHLCV bar."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def make_synthetic_series(
    ticker: str = "DEMO",
    days: int = 750,
    start_price: float = 100.0,
    seed: int | None = None,
    annual_drift: float = 0.08,
    annual_vol: float = 0.35,
) -> list[Bar]:
    """Generate a geometric random-walk price series with regime shifts.

    Deterministic when `seed` is set, so backtests are reproducible.
    """
    rng = random.Random(seed if seed is not None else hash(ticker) % 100_000)
    bars: list[Bar] = []
    price = start_price
    dt = 1 / 252
    # Pre-compute slow regime swings (bull / bear / chop) for realism.
    regime = 0
    for i in range(days):
        if i % 60 == 0:
            regime = rng.choice([1, -1, 0, 0])  # bull, bear, chop, chop
        drift = annual_drift * dt + regime * 0.0009
        shock = rng.gauss(0, annual_vol * math.sqrt(dt))
        ret = drift + shock
        open_p = price
        close_p = max(1.0, open_p * math.exp(ret))
        high_p = max(open_p, close_p) * (1 + abs(rng.gauss(0, 0.004)))
        low_p = min(open_p, close_p) * (1 - abs(rng.gauss(0, 0.004)))
        volume = rng.uniform(0.5e6, 3e6) * (1 + abs(ret) * 40)
        bars.append(
            Bar(
                date=f"day-{i:04d}",
                open=round(open_p, 4),
                high=round(high_p, 4),
                low=round(low_p, 4),
                close=round(close_p, 4),
                volume=round(volume),
            )
        )
        price = close_p
    return bars


def load_yahoo_series(ticker: str, period: str = "3y", interval: str = "1d") -> list[Bar]:
    """Load real OHLCV from Yahoo Finance. Requires `pip install yfinance`."""
    try:
        import yfinance as yf  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Real data needs yfinance. Install with `pip install yfinance` "
            "or use synthetic data (default)."
        ) from exc

    df = yf.download(ticker, period=period, interval=interval, progress=False)
    bars: list[Bar] = []
    for ts, row in df.iterrows():
        bars.append(
            Bar(
                date=str(ts.date()),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            )
        )
    return bars


def get_series(ticker: str, days: int = 750, real: bool = False) -> list[Bar]:
    """Return a price series — real (yfinance) or synthetic fallback."""
    if real:
        try:
            return load_yahoo_series(ticker)
        except Exception:
            pass  # fall back to synthetic offline
    return make_synthetic_series(ticker=ticker, days=days, seed=hash(ticker) % 100_000)
