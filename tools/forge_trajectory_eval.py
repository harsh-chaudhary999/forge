#!/usr/bin/env python3
"""Shim: forwards to ``tools/eval/forge_trajectory_eval.py`` (grouped layout; see tools/README.md)."""
from __future__ import annotations

import runpy
from pathlib import Path

_IMPL = Path(__file__).resolve().parent / "eval/forge_trajectory_eval.py"
runpy.run_path(str(_IMPL), run_name="__main__")
