#!/usr/bin/env python3
"""
Machine checks for Forge task readiness under a git-backed brain.

Validates (when applicable):
  - At least one eval scenario file under prds/<task-id>/eval/
  - Optional --validate-eval-yaml: eval scenario shape checks (PyYAML when
    installed; else stdlib best-effort via tools/eval_yaml_stdlib.py).
  - Optional --check-prd-sections: prd-locked.md mandatory lock headings/fields.
  - Optional --require-conductor-timestamps: conductor.log lines with phase
    markers must start with ISO-8601 (audit trail).
  - Optional --strict-single-task-brain: fail if multiple prds/*/conductor.log
    (use --allow-multi-task-brain to opt out).
  - conductor.log ordering: [P4.0-EVAL-YAML] before any [P4.1-DISPATCH]
  - forge_qa_csv_before_eval: true -> qa/manual-test-cases.csv + log order vs eval
  - Net-new design (prd-locked) -> design/ artifacts or [DESIGN-INGEST] before P4.1
  - Optional --strict-tdd: [P4.0-TDD-RED] before first [P4.1-DISPATCH]
  - Optional --gates-dir: read gate JSON ledger (written by post-commit.cjs)
    instead of (or as supplement to) conductor.log regex parsing.
  - Optional --check-shared-spec: shared-dev-spec.md anchors + no TBD/TODO (see
    tools/shared_spec_checklist.json).
  - Optional phase-ledger.jsonl: --validate-phase-ledger, --require-phase-ledger,
    --phase-ledger-verify-hashes (see tools/append_phase_ledger.py).
  - Optional --strict-tech-plans: when prds/<task-id>/tech-plans/*.md exist,
    run structural checks (headings, 1b.2a placement, REVIEW_PASS gate markers).
  - Optional --strict-0c-inventory: same tech-plan gate as --strict-tech-plans,
    plus REVIEW_PASS Section 0c semantic rails (no GAP last column; cite
    Confluence mirror / touchpoints / QA CSV when those files exist — see
    tools/verify_tech_plans.py).

Core checks use stdlib only (product.md may mix markdown headings with YAML).
PyYAML strengthens eval checks when installed (see tools/requirements-verify.txt);
stdlib fallback is always available for the same flag.

Usage (from Forge repo root, brain elsewhere):
  python3 tools/verify_forge_task.py --task-id my-feature --brain ~/forge/brain

Usage (brain repo checked out as cwd, Forge path explicit):
  python3 /path/to/forge/tools/verify_forge_task.py --task-id my-feature --brain .

Usage (with gate JSON ledger from post-commit.cjs):
  python3 tools/verify_forge_task.py --task-id my-feature --brain ~/forge/brain --gates-dir ~/forge/brain/prds/my-feature/gates

Drift (PRD success criteria vs eval/QA text):
  python3 tools/forge_drift_check.py --task-id my-feature --brain ~/forge/brain [--strict]

Phase ledger (append-only JSONL + SHA256):
  python3 tools/append_phase_ledger.py --brain ~/forge/brain --task-id my-feature \\
    --phase '[P4.0-EVAL-YAML]' --artifacts eval/smoke.yaml
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from eval_yaml_stdlib import validate_eval_dir_stdlib
from phase_ledger import LEDGER_NAME, verify_ledger
from shared_spec_policy import validate_shared_spec


def _default_brain_root() -> Path:
    """Honor FORGE_BRAIN or FORGE_BRAIN_PATH (same semantics), then ~/forge/brain."""
    home = Path.home()
    for key in ("FORGE_BRAIN", "FORGE_BRAIN_PATH"):
        v = os.environ.get(key, "").strip()
        if v:
            return Path(v).expanduser()
    return home / "forge" / "brain"


def _validate_single_eval_document(data: object, label: str) -> list[str]:
    """Minimal invariants aligned with skills/eval-scenario-format (smoke + steps)."""
    errs: list[str] = []
    if not isinstance(data, dict):
        return [f"{label}: root must be a mapping (YAML object), got {type(data).__name__}"]
    scenario = data.get("scenario")
    if not scenario or not isinstance(scenario, str) or not scenario.strip():
        errs.append(f"{label}: missing or empty 'scenario' (non-empty string required)")
    steps = data.get("steps")
    if not isinstance(steps, list) or len(steps) < 1:
        errs.append(f"{label}: 'steps' must be a non-empty list")
        return errs
    for i, step in enumerate(steps):
        prefix = f"{label} steps[{i}]"
        if not isinstance(step, dict):
            errs.append(f"{prefix}: must be a mapping, got {type(step).__name__}")
            continue
        for key in ("id", "driver", "action", "expected"):
            if key not in step:
                errs.append(f"{prefix}: missing key {key!r}")
        exp = step.get("expected")
        if exp is not None:
            if not isinstance(exp, dict):
                errs.append(f"{prefix}: 'expected' must be a mapping, got {type(exp).__name__}")
            elif len(exp) == 0:
                errs.append(
                    f"{prefix}: 'expected' must not be empty "
                    "(machine-readable assertions required per eval-scenario-format)"
                )
    return errs


def _validate_eval_yaml_files_pyyaml(eval_dir: Path, yaml_mod: object) -> list[str]:
    """Parse each *.yaml/*.yml with PyYAML (full fidelity)."""
    errors: list[str] = []
    yaml_files = sorted(
        p for p in eval_dir.iterdir() if p.is_file() and p.suffix.lower() in (".yaml", ".yml")
    )
    for path in yaml_files:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.name}: cannot read file: {exc}")
            continue
        try:
            docs = list(yaml_mod.safe_load_all(raw))
        except getattr(yaml_mod, "YAMLError", Exception) as exc:
            errors.append(f"{path.name}: YAML parse error: {exc}")
            continue
        substantive = [d for d in docs if d is not None]
        if not substantive:
            errors.append(f"{path.name}: no YAML documents (empty or comments only)")
            continue
        for di, data in enumerate(substantive):
            label = path.name if len(substantive) == 1 else f"{path.name} (document {di + 1})"
            errors.extend(_validate_single_eval_document(data, label))
    return errors


def _validate_eval_yaml_files(eval_dir: Path) -> list[str]:
    """
    Eval scenario shape: prefer PyYAML when installed; else stdlib best-effort
    (tools/eval_yaml_stdlib.py).
    """
    try:
        import yaml as yaml_mod  # type: ignore
    except ImportError:
        print(
            "INFO: PyYAML not installed — using stdlib eval YAML checks "
            "(pip install -r tools/requirements-verify.txt for full fidelity).",
            file=sys.stderr,
        )
        return validate_eval_dir_stdlib(eval_dir)
    return _validate_eval_yaml_files_pyyaml(eval_dir, yaml_mod)


RE_PRD_LOCKED_HEADING = re.compile(r"(?m)^#\s+PRD\s+Locked\s*$", re.IGNORECASE)
RE_REPOS_AFFECTED = re.compile(
    r"(?ms)\*\*Repos Affected:\*\*\s*\n(.*?)(?=\n\*\*[A-Za-z /]+:\*\*|\n---|\Z)"
)
RE_UI_SIGNAL = re.compile(
    r"\b(web|app|mobile|dashboard|frontend|ui|ios|android|react|next)\b", re.IGNORECASE
)

# Mandatory lock dimensions from intake template (substring presence).
PRD_REQUIRED_MARKERS: tuple[str, ...] = (
    "**Product:**",
    "**Goal:**",
    "**Success Criteria:**",
    "**Repos Affected:**",
    "**repo_registry_confidence:**",
    "**repo_naming_mismatch_notes:**",
    "**product_md_update_required:**",
    "**Contracts Affected:**",
    "**Timeline:**",
    "**Rollback:**",
    "**Success Metrics:**",
)


def _validate_prd_locked_sections(prd_path: Path) -> list[str]:
    """Structural checks on prd-locked.md (intake lock template)."""
    errs: list[str] = []
    if not prd_path.is_file():
        errs.append(f"Missing {prd_path}")
        return errs
    text = _read_text(prd_path)
    if not RE_PRD_LOCKED_HEADING.search(text):
        errs.append("prd-locked.md: expected top-level heading '# PRD Locked'")
    for marker in PRD_REQUIRED_MARKERS:
        if marker not in text:
            errs.append(f"prd-locked.md: missing required block/field {marker!r}")
    if "**Design / UI" not in text and "design_ui_scope: not applicable" not in text:
        block = RE_REPOS_AFFECTED.search(text)
        body = block.group(1) if block else ""
        if body and RE_UI_SIGNAL.search(body):
            errs.append(
                "prd-locked.md: UI-related repos/surfaces suggested in **Repos Affected:** "
                "but no **Design / UI** section and no `design_ui_scope: not applicable` — "
                "lock Q9 per intake-interrogate."
            )
    return errs


RE_PHASE_MARKER_IN_LINE = re.compile(r"\[[Pp][0-9][^\]\s]*\]")


def _line_has_leading_iso_timestamp(raw: str) -> bool:
    """True if line starts with ISO-8601 date-time (plain or bracketed)."""
    if re.match(r"^\d{4}-\d{2}-\d{2}T", raw):
        return True
    if re.match(r"^\[\d{4}-\d{2}-\d{2}T[^\]]*\]\s*\[", raw):
        return True
    return False


def _conductor_timestamp_violations(lines: list[str]) -> list[str]:
    """Lines containing [P…] phase markers should be auditable with a leading timestamp."""
    errs: list[str] = []
    for i, line in enumerate(lines, start=1):
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if not RE_PHASE_MARKER_IN_LINE.search(raw):
            continue
        if _line_has_leading_iso_timestamp(raw):
            continue
        errs.append(
            f"conductor.log line {i}: phase marker present but line lacks leading ISO-8601 "
            f"timestamp (use e.g. '2026-04-24T12:00:00Z [P4.0-EVAL-YAML] …' or "
            f"'[2026-04-24T12:00:00Z] [P4.0-EVAL-YAML] …'). Got: {raw[:160]!r}"
        )
    return errs


def _effective_gates_dir(task_dir: Path, gates_dir: Path | None) -> tuple[Path | None, str | None]:
    """
    Resolve gate JSON directory. If explicit --gates-dir is missing on disk but
    prds/<task-id>/gates exists, fall back to the task-local gates dir.
    Returns (directory or None, optional INFO message).
    """
    task_gates = task_dir / "gates"
    if gates_dir is not None:
        if gates_dir.is_dir():
            return gates_dir, None
        if task_gates.is_dir():
            return (
                task_gates,
                f"INFO: --gates-dir {gates_dir} not found or not a directory; using {task_gates}",
            )
        return None, None
    if task_gates.is_dir():
        return task_gates, None
    return None, None


def _multi_task_brain_messages(brain: Path, task_id: str, strict: bool) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings) for multiple prds/*/conductor.log files."""
    errs: list[str] = []
    warns: list[str] = []
    prds = brain / "prds"
    if not prds.is_dir():
        return errs, warns
    with_logs = sorted(d.name for d in prds.iterdir() if d.is_dir() and (d / "conductor.log").is_file())
    if len(with_logs) <= 1:
        return errs, warns
    msg = (
        f"Brain has {len(with_logs)} tasks with conductor.log ({', '.join(with_logs)}). "
        f"Session hooks use mtime when FORGE_TASK_ID is unset — export FORGE_TASK_ID={task_id!r} "
        "(or FORGE_PRD_TASK_ID) while working on this task."
    )
    if strict:
        errs.append(
            msg + " Or drop --strict-single-task-brain / pass --allow-multi-task-brain if intentional."
        )
    else:
        warns.append(msg)
    return errs, warns


def _run_verify_tech_plans(
    brain: Path, task_id: str, *, strict_0c_inventory: bool = False
) -> list[str]:
    """Load sibling verify_tech_plans.py via importlib (works regardless of cwd)."""
    import importlib.util

    path = Path(__file__).resolve().parent / "verify_tech_plans.py"
    spec = importlib.util.spec_from_file_location("_forge_verify_tech_plans", path)
    if spec is None or spec.loader is None:
        return [f"Cannot load tech plan verifier from {path}"]
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.verify_tech_plans(brain, task_id, strict_0c_inventory=strict_0c_inventory)


RE_PRODUCT_LINE = re.compile(r"^\*\*Product:\*\*\s*(.+)\s*$", re.MULTILINE)
RE_NAME_FIELD = re.compile(r"^name:\s*(.+)\s*$", re.MULTILINE)
RE_QA_FLAG_TRUE = re.compile(r"^forge_qa_csv_before_eval:\s*true\s*$", re.MULTILINE)
RE_DESIGN_NEW_YES = re.compile(
    r"(?:\*\*design_new_work:\*\*|design_new_work:)\s*yes\b", re.IGNORECASE
)
RE_DESIGN_WAIVER_PRD = re.compile(r"design_waiver.*prd_only", re.IGNORECASE)
RE_P40_EVAL = re.compile(r"\[P4\.0-EVAL-YAML\]")
RE_P41_DISPATCH = re.compile(r"\[P4\.1-DISPATCH\]")
RE_P40_QA_APPROVED = re.compile(r"\[P4\.0-QA-CSV\].*approved=yes")
RE_P40_QA_SKIPPED = re.compile(r"\[P4\.0-QA-CSV\].*skipped=not_required")
RE_DESIGN_INGEST = re.compile(r"\[DESIGN-INGEST\]")
RE_P40_TDD_RED = re.compile(r"\[P4\.0-TDD-RED\]")


def _first_line_number(pattern: re.Pattern[str], lines: list[str]) -> int | None:
    for i, line in enumerate(lines, start=1):
        if pattern.search(line):
            return i
    return None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_prd_product_name(prd_path: Path) -> str | None:
    if not prd_path.is_file():
        return None
    text = _read_text(prd_path)
    m = RE_PRODUCT_LINE.search(text)
    return m.group(1).strip() if m else None


def _resolve_product_slug(
    brain: Path, prd_path: Path, product_slug: str | None
) -> tuple[str | None, Path | None]:
    """Return (slug, product.md path) for policy reads."""
    products = brain / "products"
    if product_slug:
        pm = products / product_slug / "product.md"
        return (product_slug, pm if pm.is_file() else None)

    pname = _parse_prd_product_name(prd_path)
    if not pname or not products.is_dir():
        return (None, None)
    want = pname.casefold()
    for pm in sorted(products.glob("*/product.md")):
        m = RE_NAME_FIELD.search(_read_text(pm))
        if m and m.group(1).strip().casefold() == want:
            return (pm.parent.name, pm)
    return (None, None)


def _product_requires_qa_before_eval(product_md: Path | None) -> bool:
    if not product_md or not product_md.is_file():
        return False
    return bool(RE_QA_FLAG_TRUE.search(_read_text(product_md)))


def _prd_net_new_design(prd_text: str) -> bool:
    return bool(RE_DESIGN_NEW_YES.search(prd_text))


def _prd_design_waiver_prd_only(prd_text: str) -> bool:
    return bool(RE_DESIGN_WAIVER_PRD.search(prd_text))


def _eval_yaml_count(eval_dir: Path) -> int:
    if not eval_dir.is_dir():
        return 0
    n = 0
    for p in eval_dir.iterdir():
        if p.is_file() and p.suffix.lower() in (".yaml", ".yml"):
            n += 1
    return n


def _csv_data_rows(csv_path: Path) -> int:
    if not csv_path.is_file():
        return 0
    lines = [ln.strip() for ln in _read_text(csv_path).splitlines() if ln.strip()]
    return max(0, len(lines) - 1)  # assume one header row


def _design_file_count(design_dir: Path) -> int:
    if not design_dir.is_dir():
        return 0
    return sum(1 for p in design_dir.rglob("*") if p.is_file())


def _load_gates_ledger(gates_dir: Path | None) -> dict[str, dict]:
    """
    Load gate JSON artifacts written by post-commit.cjs from gates_dir.
    Returns a mapping of gate_id -> artifact dict.
    Only gates with status="satisfied" are included.

    If gates_dir is None or does not exist, returns an empty dict (caller
    falls back to conductor.log regex parsing as before).
    """
    if not gates_dir or not gates_dir.is_dir():
        return {}
    ledger: dict[str, dict] = {}
    for jf in gates_dir.glob("*.json"):
        try:
            data = json.loads(jf.read_text(encoding="utf-8", errors="replace"))
            gate_id = data.get("gate_id", "")
            status = data.get("status", "")
            if gate_id and status == "satisfied":
                ledger[gate_id] = data
        except (json.JSONDecodeError, OSError):
            pass  # skip unreadable/invalid gate files
    return ledger


def verify(
    brain: Path,
    task_id: str,
    product_slug: str | None,
    strict_tdd: bool,
    require_log: bool,
    gates_dir: Path | None = None,
    validate_eval_yaml: bool = False,
    check_prd_sections: bool = False,
    check_shared_spec: bool = False,
    shared_spec_path: Path | None = None,
    shared_spec_checklist: Path | None = None,
    validate_phase_ledger: bool = False,
    require_phase_ledger: bool = False,
    phase_ledger_verify_hashes: bool = False,
    require_conductor_timestamps: bool = False,
    strict_single_task_brain: bool = False,
    strict_tech_plans: bool = False,
    strict_0c_inventory: bool = False,
) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []

    task_dir = brain / "prds" / task_id
    if not task_dir.is_dir():
        errors.append(f"Task directory missing: {task_dir}")
        return errors

    prd_locked = task_dir / "prd-locked.md"
    slug, product_md = _resolve_product_slug(brain, prd_locked, product_slug)
    if product_slug and not product_md:
        errors.append(f"--product {product_slug}: missing {brain / 'products' / product_slug / 'product.md'}")
    require_qa = _product_requires_qa_before_eval(product_md)

    if check_prd_sections:
        errors.extend(_validate_prd_locked_sections(prd_locked))

    if check_shared_spec:
        spec_path = shared_spec_path or (task_dir / "shared-dev-spec.md")
        errors.extend(validate_shared_spec(spec_path, checklist_path=shared_spec_checklist))

    # Load gate JSON ledger from post-commit.cjs (if available)
    effective_gates_dir, gates_msg = _effective_gates_dir(task_dir, gates_dir)
    if gates_msg:
        print(gates_msg, file=sys.stderr)
    ledger = _load_gates_ledger(effective_gates_dir)
    using_ledger = bool(ledger)
    if using_ledger and effective_gates_dir is not None:
        print(
            f"INFO: Gate ledger loaded from {effective_gates_dir} "
            f"({len(ledger)} satisfied gates: {sorted(ledger)})",
            file=sys.stderr,
        )

    eval_dir = task_dir / "eval"
    n_yaml = _eval_yaml_count(eval_dir)
    if n_yaml < 1:
        errors.append(
            f"Need at least one eval scenario (*.yaml/*.yml) under {eval_dir} "
            "(State 4b / forge-eval-gate)."
        )

    if validate_eval_yaml and eval_dir.is_dir():
        errors.extend(_validate_eval_yaml_files(eval_dir))

    qa_csv = task_dir / "qa" / "manual-test-cases.csv"
    if require_qa:
        rows = _csv_data_rows(qa_csv)
        if rows < 1:
            errors.append(
                f"forge_qa_csv_before_eval: true but missing or empty data rows in {qa_csv}"
            )

    log_path = task_dir / "conductor.log"
    prd_text = _read_text(prd_locked) if prd_locked.is_file() else ""

    if not log_path.is_file():
        msg = f"No conductor.log at {log_path} — log ordering checks skipped."
        if require_log:
            errors.append(msg.rstrip(" — log ordering checks skipped.") + " (--require-log)")
        else:
            warnings.append(msg)
        lines: list[str] = []
    else:
        lines = _read_text(log_path).splitlines()

    if lines and require_conductor_timestamps:
        errors.extend(_conductor_timestamp_violations(lines))

    # When a gate ledger is available, use it for gate presence checks.
    # Ordering checks still use conductor.log line numbers (ledger has timestamps,
    # but line ordering in the log is the canonical ordering authority).
    if using_ledger:
        # Presence checks via ledger
        has_eval_yaml  = "P4.0-EVAL-YAML" in ledger
        has_dispatch   = "P4.1-DISPATCH"  in ledger
        has_qa_ok      = "P4.0-QA-CSV"   in ledger
        has_tdd_red    = "P4.0-TDD-RED"  in ledger

        if has_dispatch and not has_eval_yaml:
            errors.append(
                "Gate ledger: [P4.1-DISPATCH] satisfied but [P4.0-EVAL-YAML] missing — invalid orchestration."
            )
        if require_qa and has_eval_yaml and not has_qa_ok:
            errors.append(
                "Gate ledger: forge_qa_csv_before_eval: true requires [P4.0-QA-CSV] satisfied "
                "before [P4.0-EVAL-YAML]."
            )
        if strict_tdd and has_dispatch and not has_tdd_red:
            errors.append(
                "--strict-tdd: gate ledger shows [P4.1-DISPATCH] but [P4.0-TDD-RED] is absent."
            )
        elif has_dispatch and not has_tdd_red:
            warnings.append(
                "[P4.0-TDD-RED] absent from gate ledger (dispatch happened without TDD RED). "
                "Use --strict-tdd to fail on this."
            )

        # For ordering within the log (QA before eval, TDD before dispatch),
        # fall through to conductor.log line checks below only when lines exist.

    if lines:
        ln_eval = _first_line_number(RE_P40_EVAL, lines)
        ln_p41 = _first_line_number(RE_P41_DISPATCH, lines)
        ln_qa_ok = _first_line_number(RE_P40_QA_APPROVED, lines)
        ln_tdd = _first_line_number(RE_P40_TDD_RED, lines)

        if not using_ledger:
            # Presence checks via conductor.log (fallback when no ledger)
            if ln_p41 is not None and ln_eval is None:
                errors.append(
                    "conductor.log has [P4.1-DISPATCH] but no [P4.0-EVAL-YAML] — invalid orchestration."
                )

        # Ordering checks always use conductor.log line numbers (ledger has no line order)
        if ln_p41 is not None and ln_eval is not None and ln_p41 < ln_eval:
            errors.append(
                f"conductor.log: first [P4.1-DISPATCH] (line {ln_p41}) is before "
                f"[P4.0-EVAL-YAML] (line {ln_eval})."
            )

        if require_qa and ln_eval is not None and not using_ledger:
            if ln_qa_ok is None:
                if RE_P40_QA_SKIPPED.search("\n".join(lines)):
                    errors.append(
                        "[P4.0-QA-CSV] skipped=not_required in log but "
                        "forge_qa_csv_before_eval: true requires approved=yes before eval."
                    )
                else:
                    errors.append(
                        "forge_qa_csv_before_eval: true requires [P4.0-QA-CSV] ... approved=yes "
                        f"before [P4.0-EVAL-YAML] (eval first seen line {ln_eval})."
                    )
            elif ln_qa_ok >= ln_eval:
                errors.append(
                    f"forge_qa_csv_before_eval: true but [P4.0-QA-CSV] approved (line {ln_qa_ok}) "
                    f"is not before [P4.0-EVAL-YAML] (line {ln_eval})."
                )

        if not using_ledger:
            if strict_tdd and ln_p41 is not None:
                if ln_tdd is None or ln_tdd > ln_p41:
                    errors.append(
                        "--strict-tdd: require [P4.0-TDD-RED] before first [P4.1-DISPATCH] "
                        f"(tdd_line={ln_tdd}, p41_line={ln_p41})."
                    )
            elif ln_p41 is not None and (ln_tdd is None or ln_tdd > ln_p41):
                warnings.append(
                    f"[P4.0-TDD-RED] missing or after first [P4.1-DISPATCH] "
                    f"(tdd={ln_tdd}, p41={ln_p41}). Use --strict-tdd to fail on this."
                )

    # Net-new design: materialized under design/ and/or logged before P4.1
    if _prd_net_new_design(prd_text) and not _prd_design_waiver_prd_only(prd_text):
        design_dir = task_dir / "design"
        dcount = _design_file_count(design_dir)
        if dcount < 1:
            if not lines:
                errors.append(
                    "prd-locked indicates net-new design without prd_only waiver: "
                    "design/ is empty and conductor.log is missing — add brain design/ "
                    "artifacts or commit conductor.log with [DESIGN-INGEST]."
                )
            else:
                ln_p41_d = _first_line_number(RE_P41_DISPATCH, lines)
                ln_ingest = _first_line_number(RE_DESIGN_INGEST, lines)
                if ln_ingest is None or (
                    ln_p41_d is not None and ln_ingest > ln_p41_d
                ):
                    errors.append(
                        "prd-locked indicates net-new design without prd_only waiver: "
                        "expected files under design/ and/or [DESIGN-INGEST] in conductor.log "
                        "before first [P4.1-DISPATCH]."
                    )

    ledger_path = task_dir / LEDGER_NAME
    if require_phase_ledger and not ledger_path.is_file():
        errors.append(f"Missing required {ledger_path} (--require-phase-ledger)")
    if ledger_path.is_file() and (
        validate_phase_ledger or require_phase_ledger or phase_ledger_verify_hashes
    ):
        errors.extend(
            verify_ledger(
                task_dir,
                verify_hashes=phase_ledger_verify_hashes,
                task_id_expected=task_id,
            )
        )

    m_errs, m_warns = _multi_task_brain_messages(brain, task_id, strict_single_task_brain)
    errors.extend(m_errs)
    warnings.extend(m_warns)

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)

    if slug and product_md:
        print(f"INFO: Using product slug={slug!r} ({product_md})", file=sys.stderr)

    if strict_tech_plans or strict_0c_inventory:
        tp_dir = task_dir / "tech-plans"
        if tp_dir.is_dir() and any(
            p.suffix.lower() == ".md"
            and p.name.lower() not in ("human_signoff.md", "readme.md")
            for p in tp_dir.iterdir()
            if p.is_file()
        ):
            errors.extend(
                _run_verify_tech_plans(
                    brain, task_id, strict_0c_inventory=strict_0c_inventory
                )
            )

    return errors


def main() -> int:
    p = argparse.ArgumentParser(description="Verify Forge brain task gates (eval, log order, QA, design).")
    p.add_argument("--task-id", required=True, help="prds/<task-id> directory name")
    p.add_argument(
        "--brain",
        default=None,
        help="Brain root (default: $FORGE_BRAIN or $FORGE_BRAIN_PATH or ~/forge/brain)",
    )
    p.add_argument(
        "--product",
        default=None,
        help="Product slug under brain/products/<slug>/product.md (optional if prd-locked matches name:)",
    )
    p.add_argument(
        "--strict-tdd",
        action="store_true",
        help="Fail if [P4.0-TDD-RED] is missing or after first [P4.1-DISPATCH]",
    )
    p.add_argument(
        "--require-log",
        action="store_true",
        help="Fail if conductor.log is missing (default: warn only)",
    )
    p.add_argument(
        "--gates-dir",
        default=None,
        help=(
            "Path to gate JSON ledger directory written by post-commit.cjs "
            "(e.g. brain/prds/<task-id>/gates). "
            "When omitted, uses prds/<task-id>/gates if that directory exists. "
            "If this path is missing but the task-local gates/ exists, that directory is used."
        ),
    )
    p.add_argument(
        "--validate-eval-yaml",
        action="store_true",
        help=(
            "Validate each eval *.yaml/*.yml scenario shape (PyYAML if installed, "
            "else stdlib best-effort in tools/eval_yaml_stdlib.py)."
        ),
    )
    p.add_argument(
        "--check-prd-sections",
        action="store_true",
        help="Require prd-locked.md intake template headings and Q9 heuristic for UI repos.",
    )
    p.add_argument(
        "--require-conductor-timestamps",
        action="store_true",
        help="Fail if conductor.log lines with [P…] phase markers lack a leading ISO-8601 timestamp.",
    )
    p.add_argument(
        "--strict-single-task-brain",
        action="store_true",
        help="Fail when more than one prds/*/conductor.log exists (multi-task ambiguity).",
    )
    p.add_argument(
        "--allow-multi-task-brain",
        action="store_true",
        help="Allow multiple conductor.log files under prds/ (only with --strict-single-task-brain).",
    )
    p.add_argument(
        "--check-shared-spec",
        action="store_true",
        help="Require shared-dev-spec.md and tools/shared_spec_checklist.json anchors (+ no TBD/TODO).",
    )
    p.add_argument(
        "--shared-spec-path",
        default=None,
        help="Override path to shared-dev-spec.md (default: prds/<task-id>/shared-dev-spec.md).",
    )
    p.add_argument(
        "--shared-spec-checklist",
        default=None,
        help="JSON checklist path (default: tools/shared_spec_checklist.json next to verify script).",
    )
    p.add_argument(
        "--validate-phase-ledger",
        action="store_true",
        help="If phase-ledger.jsonl exists, validate JSON lines and schema.",
    )
    p.add_argument(
        "--require-phase-ledger",
        action="store_true",
        help="Require prds/<task-id>/phase-ledger.jsonl to exist.",
    )
    p.add_argument(
        "--phase-ledger-verify-hashes",
        action="store_true",
        help="When validating phase-ledger.jsonl, re-hash artifact paths vs recorded sha256.",
    )
    p.add_argument(
        "--strict-tech-plans",
        action="store_true",
        help=(
            "When tech-plans/*.md exist for the task, fail on missing canonical "
            "headings, misplaced ### 1b.2a, or REVIEW_PASS without FORGE-GATE anchors "
            "(see tech-plan-self-review + verify_tech_plans.py)."
        ),
    )
    p.add_argument(
        "--strict-0c-inventory",
        action="store_true",
        help=(
            "Implies tech-plans/*.md checks (same as --strict-tech-plans) plus, for "
            "REVIEW_PASS, reject Section 0c rows whose last table column is GAP and "
            "require inventory citations when prd-source-confluence.md, "
            "source-confluence.md, touchpoints/*.md, or qa/manual-test-cases.csv exist."
        ),
    )
    args = p.parse_args()

    brain = Path(args.brain).expanduser() if args.brain else _default_brain_root()

    gates_dir = Path(args.gates_dir).expanduser() if args.gates_dir else None
    shared_spec_path = Path(args.shared_spec_path).expanduser() if args.shared_spec_path else None
    shared_spec_checklist = (
        Path(args.shared_spec_checklist).expanduser() if args.shared_spec_checklist else None
    )

    strict_single = bool(args.strict_single_task_brain and not args.allow_multi_task_brain)

    errs = verify(
        brain=brain,
        task_id=args.task_id,
        product_slug=args.product,
        strict_tdd=args.strict_tdd,
        require_log=args.require_log,
        gates_dir=gates_dir,
        validate_eval_yaml=args.validate_eval_yaml,
        check_prd_sections=args.check_prd_sections,
        check_shared_spec=args.check_shared_spec,
        shared_spec_path=shared_spec_path,
        shared_spec_checklist=shared_spec_checklist,
        validate_phase_ledger=args.validate_phase_ledger,
        require_phase_ledger=args.require_phase_ledger,
        phase_ledger_verify_hashes=args.phase_ledger_verify_hashes,
        require_conductor_timestamps=args.require_conductor_timestamps,
        strict_single_task_brain=strict_single,
        strict_tech_plans=bool(args.strict_tech_plans or args.strict_0c_inventory),
        strict_0c_inventory=args.strict_0c_inventory,
    )
    if errs:
        print("Forge task verification FAILED:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK: task {args.task_id!r} under {brain}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
