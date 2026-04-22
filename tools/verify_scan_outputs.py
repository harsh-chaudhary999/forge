#!/usr/bin/env python3
"""
Verify a codebase scan completed consolidation steps (markdown + JSON artifacts).

Usage:
  python3 tools/verify_scan_outputs.py ~/forge/brain/products/<slug>/codebase

Exit 1 if required files are missing or SCAN.json reports source files but modules/ is empty.
Catches "scan ran but flow escaped" (partial write, wrong --brain-codebase, aborted CLI).

Implementation lives in ``scan_forge.verify_brain_codebase`` (also invoked from ``scan_forge.cli``
after each run with retries unless ``FORGE_SCAN_SKIP_VERIFY=1``).
"""
from __future__ import annotations

import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from scan_forge.verify_brain_codebase import verify_brain_codebase_once


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_scan_outputs.py <brain-codebase-directory>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    code, lines = verify_brain_codebase_once(root)
    for ln in lines:
        print(ln)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
