#!/usr/bin/env python3
"""Shim: forwards to ``tools/verify/run_semantic_csv_eval.py``."""
from __future__ import annotations

import runpy
from pathlib import Path

_IMPL = Path(__file__).resolve().parent / "verify/run_semantic_csv_eval.py"
runpy.run_path(str(_IMPL), run_name="__main__")
