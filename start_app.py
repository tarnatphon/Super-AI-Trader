#!/usr/bin/env python3
"""Double-click entry point: python start_app.py  (or via the .command/.bat).

By default it opens the dashboard in your BROWSER (the most reliable option
on macOS/Windows). Set SAT_NATIVE=1 to try the own native window (pywebview).
"""
import os
import sys


def main():
    # The native (pywebview) window can crash on some macOS/Python combos
    # when launched from a double-clicked script. Default to browser; the
    # user can opt into the native window with SAT_NATIVE=1.
    use_native_window = os.environ.get("SAT_NATIVE", "0") == "1"

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from super_ai_trader.launcher import launch
    launch(window=use_native_window)


if __name__ == "__main__":
    try:
        main()
    except ModuleNotFoundError:
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        main()
