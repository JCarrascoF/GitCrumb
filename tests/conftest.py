"""Add src/ to sys.path so tests can import from gitrack.*."""

import os
import sys

_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

# Remove the root-level gitrack.py shadow if it was loaded.
sys.modules.pop("gitrack", None)
