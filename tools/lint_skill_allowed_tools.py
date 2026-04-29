#!/usr/bin/env python3
"""Shim: forwards to ``tools/dev/lint_skill_allowed_tools.py`` (grouped layout; see tools/README.md)."""
from __future__ import annotations

import runpy
from pathlib import Path

_IMPL = Path(__file__).resolve().parent / "dev/lint_skill_allowed_tools.py"
runpy.run_path(str(_IMPL), run_name="__main__")
