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

import argparse
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

_IMPORT_ERR: Exception | None = None
try:
    from scan_forge.verify_brain_codebase import verify_brain_codebase_once
except ImportError as exc:  # pragma: no cover - environment-dependent
    _IMPORT_ERR = exc
    verify_brain_codebase_once = None  # type: ignore[assignment]


def main() -> int:
    if _IMPORT_ERR is not None or verify_brain_codebase_once is None:
        print(
            f"verify_scan_outputs.py: cannot import scan_forge.verify_brain_codebase: {_IMPORT_ERR}",
            file=sys.stderr,
        )
        return 2
    ap = argparse.ArgumentParser(
        description="Verify scan outputs under a brain codebase directory."
    )
    ap.add_argument("brain_codebase_directory", help="Path to brain/products/<slug>/codebase")
    args = ap.parse_args()
    root = Path(args.brain_codebase_directory).resolve()
    code, lines = verify_brain_codebase_once(root)
    for ln in lines:
        print(ln)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
