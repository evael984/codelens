"""Make the top-level `benchmark` package importable in tests.

`benchmark/` lives at the repo root (not under `src/`) because it is a
development tool, not part of the shipped wheel.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
