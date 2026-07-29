#!/usr/bin/env python3
"""
gitrack — Git activity report in a time window.

Usage:
    gitrack                                          # interactive with defaults
    gitrack ~/Dev --start 2026-01-01                 # CLI parameters
    gitrack ~/Dev --pdf                              # with PDF export
    gitrack --non-interactive                        # no prompts (uses defaults)
"""

from __future__ import annotations

import os
import sys

# Ensure the src/ package is on sys.path when run directly (symlink or shebang).
_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from gitrack.cli import main


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠  Cancelado por el usuario.")
        sys.exit(0)
