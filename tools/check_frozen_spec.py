#!/usr/bin/env python3
"""
Fail if a frozen shared-dev-spec still contains obvious unfinished markers.

Usage:
  python3 tools/check_frozen_spec.py path/to/shared-dev-spec.md

Exit 1 if TBD or TODO appears (case-insensitive) outside obvious code fences.
Cheap CI / pre-freeze hook — not a full markdown parser.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MARKERS = re.compile(r"\b(TBD|TODO)\b", re.IGNORECASE)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_frozen_spec.py <shared-dev-spec.md>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="replace")
    in_fence = False
    bad: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("#") and "TBD" in stripped.upper():
            continue
        if MARKERS.search(line):
            bad.append((i, line.rstrip()[:200]))
    if bad:
        print(f"check_frozen_spec: FAIL {path} — TBD/TODO in non-fence lines:")
        for ln, content in bad[:50]:
            print(f"  L{ln}: {content}")
        if len(bad) > 50:
            print(f"  ... and {len(bad) - 50} more")
        return 1
    print(f"check_frozen_spec: OK {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
