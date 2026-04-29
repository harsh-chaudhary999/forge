#!/usr/bin/env python3
"""Forge scan-codebase CLI — Python entry only (no shell wrapper).

Adds ``tools/`` to ``sys.path`` and delegates to ``scan_forge.cli:main``.

  python3 tools/forge_scan.py --brain-codebase … --repos backend:./api …
  (implementation: ``tools/scan/forge_scan.py``)

Equivalent: ``PYTHONPATH=tools python3 -m scan_forge …``
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    tools_root = Path(__file__).resolve().parent.parent
    if str(tools_root) not in sys.path:
        sys.path.insert(0, str(tools_root))
    from scan_forge.cli import main as run

    run()


if __name__ == "__main__":
    main()
