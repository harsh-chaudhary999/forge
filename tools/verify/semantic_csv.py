"""
Semantic automation CSV — NL-first eval steps with DependsOn ordering.

Schema: docs/semantic-eval-csv.md
Kind:   semantic-eval-manifest.json may set kind=semantic-csv-eval (see verify_forge_task).
"""

from __future__ import annotations

import csv
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

# Normalized surface tokens (lowercase). Aliases map here.
SURFACE_ALIASES: dict[str, str] = {
    "web": "web",
    "web-cdp": "web",
    "ui": "web",
    "api": "api",
    "api-http": "api",
    "http": "api",
    "rest": "api",
    "mysql": "mysql",
    "db": "mysql",
    "database": "mysql",
    "redis": "redis",
    "cache": "redis",
    "es": "es",
    "elasticsearch": "es",
    "search": "es",
    "kafka": "kafka",
    "bus": "kafka",
    "ios": "ios",
    "xctest": "ios",
    "android": "android",
    "adb": "android",
    "mobile-android": "android",
}

CANONICAL_SURFACES = frozenset(SURFACE_ALIASES.values())


def _norm_header(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


@dataclass
class SemanticStep:
    id: str
    surface: str
    intent: str
    depends_on: list[str] = field(default_factory=list)
    trace_to_csv_id: str | None = None
    expected_hint: str | None = None
    source_row: int = 0  # 1-based data row in CSV


def _split_depends(raw: str | None) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    parts: list[str] = []
    for p in str(raw).split(","):
        t = p.strip()
        if t:
            parts.append(t)
    return parts


def parse_semantic_automation_csv(path: Path) -> tuple[list[SemanticStep], list[str]]:
    """
    Parse qa/semantic-automation.csv. Returns (steps, errors).
    On any error, steps may be partial; callers should treat non-empty errors as fail.
    """
    errs: list[str] = []
    if not path.is_file():
        return [], [f"Missing {path}"]

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [], [f"{path}: cannot read ({exc})"]

    # utf-8-sig for Excel
    lines = text.splitlines()
    if not lines:
        return [], [f"{path.name}: empty file"]

    reader = csv.DictReader(lines)
    if not reader.fieldnames:
        return [], [f"{path.name}: no header row"]

    norm_to_original: dict[str, str] = {}
    for h in reader.fieldnames:
        if h is None:
            continue
        key = _norm_header(h)
        if key in norm_to_original and norm_to_original[key] != h:
            errs.append(f"{path.name}: duplicate header mapping for {key!r}")
        else:
            norm_to_original[key] = h

    required_norm = {"id", "surface", "intent"}
    if not required_norm.issubset(set(norm_to_original.keys())):
        missing = required_norm - set(norm_to_original.keys())
        errs.append(
            f"{path.name}: missing required columns (need Id, Surface, Intent) — missing {sorted(missing)}"
        )
        if errs:
            return [], errs

    steps: list[SemanticStep] = []
    seen_ids: set[str] = set()
    row_num = 1  # header is row 0 in file terms; first data row = 1

    for row in reader:
        row_num += 1
        if not row or all(not (v or "").strip() for v in row.values()):
            continue

        def col(name_norm: str) -> str:
            orig = norm_to_original.get(name_norm)
            if not orig:
                return ""
            v = row.get(orig)
            return (v or "").strip()

        sid = col("id")
        surf = col("surface")
        intent = col("intent")
        if not sid:
            errs.append(f"{path.name} row {row_num}: empty Id")
            continue
        if sid in seen_ids:
            errs.append(f"{path.name} row {row_num}: duplicate Id {sid!r}")
        seen_ids.add(sid)

        if not surf:
            errs.append(f"{path.name} row {row_num} Id={sid!r}: empty Surface")
        if not intent:
            errs.append(f"{path.name} row {row_num} Id={sid!r}: empty Intent")

        sn = _norm_header(surf)
        canonical = SURFACE_ALIASES.get(sn)
        if canonical is None and sn in CANONICAL_SURFACES:
            canonical = sn
        if canonical is None:
            errs.append(
                f"{path.name} row {row_num} Id={sid!r}: unknown Surface {surf!r} "
                f"(use one of: {', '.join(sorted(CANONICAL_SURFACES))} or common aliases in docs/semantic-eval-csv.md)"
            )
            canonical = surf or "?"

        dep_col = col("dependson") or col("depends_on")
        depends = _split_depends(dep_col)

        trace = col("tracetocsvid")
        if not trace and "tracetocsv" in norm_to_original:
            trace = (row.get(norm_to_original["tracetocsv"]) or "").strip()
        if not trace and "tracetocsvid" not in norm_to_original:
            # tolerate TraceToCsv without Id suffix in templates
            for k, o in norm_to_original.items():
                if "trace" in k and "csv" in k:
                    trace = (row.get(o) or "").strip()
                    break
        if trace == "":
            trace = None

        hint = col("expectedhint")
        if not hint and "expected_hint" in norm_to_original:
            hint = (row.get(norm_to_original["expected_hint"]) or "").strip()
        if not hint and "expected" in norm_to_original:
            hint = (row.get(norm_to_original["expected"]) or "").strip()
        if hint == "":
            hint = None

        steps.append(
            SemanticStep(
                id=sid,
                surface=canonical,
                intent=intent,
                depends_on=depends,
                trace_to_csv_id=trace,
                expected_hint=hint,
                source_row=row_num,
            )
        )

    if not steps and not errs:
        errs.append(f"{path.name}: no data rows after header")

    return steps, errs


def validate_depends_closure(steps: list[SemanticStep]) -> list[str]:
    """Unknown dependency ids and cycles are errors."""
    errs: list[str] = []
    by_id = {s.id: s for s in steps}
    for s in steps:
        for d in s.depends_on:
            if d not in by_id:
                errs.append(
                    f"semantic-automation: step Id={s.id!r} DependsOn references unknown Id={d!r}"
                )
    order, c_err = topological_order(steps)
    if c_err:
        errs.append(c_err)
    return errs


def topological_order(steps: list[SemanticStep]) -> tuple[list[SemanticStep] | None, str | None]:
    """
    Kahn topological sort. Returns (ordered steps, error string) on cycle or (ordered, None).
    """
    by_id = {s.id: s for s in steps}
    if len(by_id) != len(steps):
        return None, "semantic-automation: duplicate Ids in step list"
    in_degree: dict[str, int] = {s.id: 0 for s in steps}
    adj: dict[str, list[str]] = {s.id: [] for s in steps}
    for s in steps:
        for d in s.depends_on:
            if d in by_id:
                adj[d].append(s.id)
                in_degree[s.id] += 1
    q: deque[str] = deque([i for i, v in in_degree.items() if v == 0])
    out: list[SemanticStep] = []
    while q:
        n = q.popleft()
        out.append(by_id[n])
        for m in adj.get(n, []):
            in_degree[m] -= 1
            if in_degree[m] == 0:
                q.append(m)
    if len(out) != len(steps):
        return None, "semantic-automation: DependsOn cycle detected"
    return out, None


def validate_semantic_automation_file(path: Path) -> list[str]:
    """Parse + dependency validation; empty list means OK."""
    steps, parse_errs = parse_semantic_automation_csv(path)
    errs = list(parse_errs)
    if errs:
        return errs
    errs.extend(validate_depends_closure(steps))
    return errs
