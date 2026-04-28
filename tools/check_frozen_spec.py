#!/usr/bin/env python3
"""
Fail if a frozen shared-dev-spec still contains obvious unfinished markers.

Usage:
  python3 tools/check_frozen_spec.py path/to/shared-dev-spec.md

Exit 1 if TBD or TODO appears (case-insensitive) outside obvious code fences.
Cheap CI / pre-freeze hook — not a full markdown parser.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from shared_spec_policy import tbd_violations

_MAX_VIOLATIONS_SHOWN = 50


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fail if shared-dev-spec.md contains TBD/TODO outside code fences."
    )
    ap.add_argument("path", help="Path to shared-dev-spec.md")
    args = ap.parse_args()
    path = Path(args.path)
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="replace")
    bad = tbd_violations(text)
    if bad:
        print(f"check_frozen_spec: FAIL {path} — TBD/TODO in non-fence lines:")
        for msg in bad[:_MAX_VIOLATIONS_SHOWN]:
            print(f"  {msg}")
        if len(bad) > _MAX_VIOLATIONS_SHOWN:
            print(f"  ... and {len(bad) - _MAX_VIOLATIONS_SHOWN} more")
        return 1
    print(f"check_frozen_spec: OK {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
