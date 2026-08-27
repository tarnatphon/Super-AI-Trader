"""Local AI assistant.

Runs on a LOCAL model (Ollama by default, e.g. llama3.1/qwen — no cloud AI). If no
local model is running, it falls back to a simple offline rule-based parser so the
app still works. The assistant only CONFIGURES and EXPLAINS; the deterministic risk
layer still approves every action.
"""
