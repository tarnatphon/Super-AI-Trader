"""Super-AI-Trader — a multi-agent AI trading firm in your terminal.

Architecture (see docs/RESEARCH-top-ai-traders-2026.md):
    data -> indicators -> agents (research -> bull/bear debate -> trader
         -> risk manager -> portfolio manager) -> backtest engine -> (paper/live)

The LLM agents ADVISE; a deterministic risk module VETOES; the engine EXECUTES.
"""

__version__ = "0.1.0"
