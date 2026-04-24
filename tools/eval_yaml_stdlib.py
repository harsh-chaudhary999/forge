"""
Best-effort eval scenario validation without PyYAML.

Supports common Forge smoke shape (block-style mapping + list steps) documented in
eval-scenario-format. Flow-style YAML or complex anchors may false-negative; use
PyYAML + --validate-eval-yaml when available for full fidelity.
"""

from __future__ import annotations

import re
from pathlib import Path


def _strip_yaml_comments(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if "#" in line:
            in_single = False
            in_double = False
            cut = len(line)
            for i, ch in enumerate(line):
                if ch == "'" and not in_double:
                    in_single = not in_single
                elif ch == '"' and not in_single:
                    in_double = not in_double
                elif ch == "#" and not in_single and not in_double:
                    cut = i
                    break
            line = line[:cut].rstrip()
        out.append(line)
    return "\n".join(out)


def validate_eval_file_stdlib(raw: str, label: str) -> list[str]:
    """Return error strings; empty = pass."""
    errs: list[str] = []
    text = _strip_yaml_comments(raw)
    if not text.strip():
        return [f"{label}: empty after stripping comments"]

    if not re.search(r"(?m)^\s*scenario:\s*\S", text):
        errs.append(f"{label}: missing top-level 'scenario:' with a value (stdlib check)")

    if not re.search(r"(?m)^\s*steps:\s*(#.*)?$", text):
        errs.append(f"{label}: missing top-level 'steps:' (stdlib check)")

    # Steps: collect blocks starting at "  - id:" (list item under steps)
    step_starts = list(re.finditer(r"(?m)^(\s*)-\s+id:\s*(\S.+)?$", text))
    if not step_starts:
        errs.append(f"{label}: no list steps with '- id:' found (stdlib check)")
        return errs

    for i, m in enumerate(step_starts):
        start = m.start()
        end = step_starts[i + 1].start() if i + 1 < len(step_starts) else len(text)
        block = text[start:end]
        if "driver:" not in block:
            errs.append(f"{label} step[{i}]: missing 'driver:' in step block starting {m.group(0)!r}")
        if "action:" not in block:
            errs.append(f"{label} step[{i}]: missing 'action:' in step block starting {m.group(0)!r}")
        if "expected:" not in block:
            errs.append(f"{label} step[{i}]: missing 'expected:' in step block starting {m.group(0)!r}")
        else:
            exp_idx = block.find("expected:")
            exp_line_start = block.rfind("\n", 0, exp_idx) + 1
            nl = block.find("\n", exp_idx)
            if nl == -1:
                exp_line = block[exp_line_start:]
            else:
                exp_line = block[exp_line_start:nl]
            exp_indent = len(exp_line) - len(exp_line.lstrip(" "))
            tail = block[nl:] if nl != -1 else ""
            has_child = False
            for ln in tail.splitlines():
                if not ln.strip():
                    continue
                ind = len(ln) - len(ln.lstrip(" "))
                if ind <= exp_indent:
                    break
                if ln.strip().startswith("- ") and ind <= exp_indent + 2:
                    break
                if re.match(r"^\s+\w+\s*:", ln):
                    has_child = True
                    break
            if not has_child:
                errs.append(
                    f"{label} step[{i}]: 'expected:' must contain at least one nested key "
                    "(non-empty mapping; stdlib check)"
                )
    return errs


def validate_eval_dir_stdlib(eval_dir: Path) -> list[str]:
    errs: list[str] = []
    for path in sorted(
        p for p in eval_dir.iterdir() if p.is_file() and p.suffix.lower() in (".yaml", ".yml")
    ):
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errs.append(f"{path.name}: cannot read: {exc}")
            continue
        errs.extend(validate_eval_file_stdlib(raw, path.name))
    return errs


__all__ = ["validate_eval_file_stdlib", "validate_eval_dir_stdlib"]
