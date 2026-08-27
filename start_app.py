#!/usr/bin/env python3
"""Double-click entry point: python start_app.py  (or via the .command/.bat)."""
import sys

try:
    from super_ai_trader.launcher import launch
    launch()
except ModuleNotFoundError:
    # Allow running from anywhere by adding the folder containing this file.
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from super_ai_trader.launcher import launch
    launch()
