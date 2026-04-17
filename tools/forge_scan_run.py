#!/usr/bin/env python3
"""Run Forge scan-codebase phases in order with an isolated FORGE_SCAN_TMP.

Delegates to the Python implementation in ``tools/scan_forge`` (no bash phase scripts).

Example:

  PYTHONPATH=tools python3 -m scan_forge \\
    --brain-codebase "$HOME/forge/brain/products/acme/codebase" \\
    --repos backend:/path/to/api web:/path/to/web

Or (adds ``tools/`` to ``sys.path`` automatically):

  python3 tools/forge_scan_run.py \\
    --brain-codebase ... --repos backend:./api web:./web
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    tools = Path(__file__).resolve().parent
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from scan_forge.cli import main as run

    run()


if __name__ == "__main__":
    main()
