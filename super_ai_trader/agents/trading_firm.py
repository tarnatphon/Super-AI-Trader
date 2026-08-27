"""The AI trading firm: specialist analysts -> bull/bear debate -> trader ->
portfolio manager. Mirrors the TradingAgents / ai-hedge-fund architecture.

Each agent first tries an LLM (if configured) and falls back to a transparent
deterministic heuristic, so the system always produces a decision.
"""
from __future__ import annotations

from .base import Signal, LLMClient, clamp


# --------------------------------------------------------------------------- #
# Specialist research analysts
# --------------------------------------------------------------------------- #
class TechnicalAnalyst:
    name = "technical"

    def analyze(self, snap: dict, llm: LLMClient | None = None) -> Signal:
        if llm and llm.enabled:
            out = llm.chat_json(
                "You are a technical analyst. Return JSON only: "
                '{"action":"BUY|SELL|HOLD","conviction":0-100,"rationale":"...","stop_pct":number}.',
                f"Market snapshot: {snap}",
            )
            if out and out.get("action") in ("BUY", "SELL", "HOLD"):
                return Signal(self.name, out["action"], clamp(float(out.get("conviction", 50)), 0, 100),
                              str(out.get("rationale", "LLM technical read")), out.get("stop_pct"))

        score, notes = 0, []
        rsi = snap.get("rsi14")
        if rsi is not None:
            if rsi < 32:
                score += 2; notes.append(f"RSI {rsi} oversold")
            elif rsi > 68:
                score -= 2; notes.append(f"RSI {rsi} overbought")
        if snap.get("sma200_dist_pct") is not None:
            if snap["sma200_dist_pct"] > 0:
                score += 1; notes.append("above 200 SMA (uptrend)")
            else:
                score -= 1; notes.append("below 200 SMA (downtrend)")
        if snap.get("bb_pos") is not None:
            if snap["bb_pos"] < 0.15:
                score += 1; notes.append("at lower Bollinger band")
            elif snap["bb_pos"] > 0.85:
                score -= 1; notes.append("at upper Bollinger band")
        macd_h = snap.get("macd_hist")
        if macd_h is not None:
            score += 1 if macd_h > 0 else -1
            notes.append("MACD positive" if macd_h > 0 else "MACD negative")

        action = "BUY" if score >= 2 else "SELL" if score <= -2 else "HOLD"
        conviction = clamp(50 + abs(score) * 9, 5, 95)
        return Signal(self.name, action, conviction, "; ".join(notes) or "neutral tape",
                      stop_pct=2.0 * (snap.get("atr14_pct") or 2))


class MomentumAnalyst:
    name = "momentum"

    def analyze(self, snap: dict, llm: LLMClient | None = None) -> Signal:
        r20, r60 = snap.get("ret_20d_pct"), snap.get("ret_60d_pct")
        score = 0
        if r20 is not None:
            score += 1 if r20 > 2 else -1 if r20 < -2 else 0
        if r60 is not None:
            score += 1 if r60 > 5 else -1 if r60 < -5 else 0
        if snap.get("macd_hist") is not None:
            score += 1 if snap["macd_hist"] > 0 else -1
        action = "BUY" if score >= 2 else "SELL" if score <= -2 else "HOLD"
        return Signal(self.name, action, clamp(50 + abs(score) * 12, 5, 95),
                      f"20d={r20}% 60d={r60}% momentum read", stop_pct=None)


class SentimentAnalyst:
    name = "sentiment"

    def analyze(self, snap: dict, llm: LLMClient | None = None, news: list[str] | None = None) -> Signal:
        if llm and llm.enabled and news:
            out = llm.chat_json(
                "You are a market sentiment analyst reading headlines. Return JSON only: "
                '{"action":"BUY|SELL|HOLD","conviction":0-100,"rationale":"..."}.',
                f"Headlines: {news}",
            )
            if out and out.get("action") in ("BUY", "SELL", "HOLD"):
                return Signal(self.name, out["action"], clamp(float(out.get("conviction", 50)), 0, 100),
                              str(out.get("rationale", "LLM sentiment")), None)

        # Offline proxy: short-term tape as sentiment stand-in.
        r20 = snap.get("ret_20d_pct") or 0
        action = "BUY" if r20 > 3 else "SELL" if r20 < -3 else "HOLD"
        return Signal(self.name, action, clamp(50 + abs(r20) * 3, 5, 90),
                      f"sentiment proxy from tape (20d {r20}%); feed news headlines for real NLP",
                      stop_pct=None)


class FundamentalAnalyst:
    name = "fundamental"

    def analyze(self, snap: dict, llm: LLMClient | None = None, fundamentals: dict | None = None) -> Signal:
        if llm and llm.enabled and fundamentals:
            out = llm.chat_json(
                "You are a fundamental analyst. Return JSON only: "
                '{"action":"BUY|SELL|HOLD","conviction":0-100,"rationale":"..."}.',
                f"Fundamentals: {fundamentals}",
            )
            if out and out.get("action") in ("BUY", "SELL", "HOLD"):
                return Signal(self.name, out["action"], clamp(float(out.get("conviction", 50)), 0, 100),
                              str(out.get("rationale", "LLM fundamentals")), None)
        # Long-term trend as a slow value proxy.
        r60 = snap.get("ret_60d_pct") or 0
        action = "BUY" if r60 > 0 else "SELL"
        return Signal(self.name, action, clamp(50 + abs(r60), 5, 85),
                      "long-horizon trend proxy; supply financials for real valuation", None)


class RiskAnalyst:
    name = "risk_analyst"

    def analyze(self, snap: dict, llm: LLMClient | None = None) -> Signal:
        atr = snap.get("atr14_pct")
        if atr is not None and atr > 6:
            return Signal(self.name, "SELL", 70, f"elevated volatility ATR {atr}% — de-risk", None)
        if atr is not None and atr < 0.5:
            return Signal(self.name, "HOLD", 55, f"very low volatility ATR {atr}% — no edge", None)
        return Signal(self.name, "HOLD", 50, "volatility within normal bounds", None)


# --------------------------------------------------------------------------- #
# Bull / Bear debate + Trader + Portfolio Manager
# --------------------------------------------------------------------------- #
class BullResearcher:
    name = "bull"

    def debate(self, signals: list[Signal]) -> Signal:
        bullish = [s for s in signals if s.action == "BUY"]
        conv = max((s.conviction for s in bullish), default=20)
        rationale = "Bull case: " + ("; ".join(f"{s.agent}({s.conviction:.0f})" for s in bullish)
                                     or "no analysts bullish")
        return Signal(self.name, "BUY" if bullish else "HOLD", clamp(conv, 5, 95), rationale)


class BearResearcher:
    name = "bear"

    def debate(self, signals: list[Signal]) -> Signal:
        bearish = [s for s in signals if s.action == "SELL"]
        conv = max((s.conviction for s in bearish), default=20)
        rationale = "Bear case: " + ("; ".join(f"{s.agent}({s.conviction:.0f})" for s in bearish)
                                     or "no analysts bearish")
        return Signal(self.name, "SELL" if bearish else "HOLD", clamp(conv, 5, 95), rationale)


class Trader:
    name = "trader"

    def propose(self, signals: list[Signal], bull: Signal, bear: Signal) -> Signal:
        buy_votes = sum(s.conviction for s in signals if s.action == "BUY")
        sell_votes = sum(s.conviction for s in signals if s.action == "SELL")
        net = buy_votes - sell_votes
        if net > 60:
            action = "BUY"
        elif net < -60:
            action = "SELL"
        else:
            action = "HOLD"
        stops = [s.stop_pct for s in signals if s.stop_pct]
        stop = sum(stops) / len(stops) if stops else None
        conviction = clamp(abs(net) / 3, 5, 95)
        return Signal(self.name, action, conviction,
                      f"net conviction {net:+.0f} (buy {buy_votes:.0f} vs sell {sell_votes:.0f})",
                      stop_pct=stop)


class PortfolioManager:
    """Synthesizes the debate into a final trading decision + market regime."""

    name = "portfolio_manager"

    def decide(self, signals: list[Signal], bull: Signal, bear: Signal, trader: Signal) -> dict:
        # Regime classification (used by risk manager for position sizing).
        r20 = next((s for s in signals if s.agent == "momentum"), None)
        macd_pos = None
        if trader.action == "BUY":
            regime = "bull" if trader.conviction > 55 else "chop"
        elif trader.action == "SELL":
            regime = "bear" if trader.conviction > 55 else "chop"
        else:
            regime = "chop"

        return {
            "action": trader.action,
            "conviction": trader.conviction,
            "regime": regime,
            "bull": bull.to_dict(),
            "bear": bear.to_dict(),
            "trader": trader.to_dict(),
            "analysts": [s.to_dict() for s in signals],
        }


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #
class TradingFirm:
    """Runs the full agent stack on a market snapshot."""

    def __init__(self, use_llm: bool = True):
        self.llm = LLMClient() if use_llm else None
        self.tech = TechnicalAnalyst()
        self.mom = MomentumAnalyst()
        self.sent = SentimentAnalyst()
        self.fund = FundamentalAnalyst()
        self.risk_a = RiskAnalyst()
        self.bull = BullResearcher()
        self.bear = BearResearcher()
        self.trader = Trader()
        self.pm = PortfolioManager()

    def analyze(self, snap: dict, news: list[str] | None = None,
                fundamentals: dict | None = None) -> dict:
        llm = self.llm
        signals = [
            self.tech.analyze(snap, llm),
            self.mom.analyze(snap, llm),
            self.sent.analyze(snap, llm, news),
            self.fund.analyze(snap, llm, fundamentals),
            self.risk_a.analyze(snap, llm),
        ]
        bull = self.bull.debate(signals)
        bear = self.bear.debate(signals)
        trader = self.trader.propose(signals, bull, bear)
        decision = self.pm.decide(signals, bull, bear, trader)
        decision["snapshot"] = snap
        decision["llm_used"] = bool(llm and llm.enabled)
        return decision
