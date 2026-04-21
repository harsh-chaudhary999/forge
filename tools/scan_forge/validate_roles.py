from __future__ import annotations

import os
from pathlib import Path

from . import log


def run_validate_roles(product_md: Path) -> None:
    product_md = product_md.resolve()
    if not product_md.is_file():
        raise SystemExit(f"validate-roles: file not found: {product_md}")

    os.environ["FORGE_SCAN_SCRIPT_ID"] = "validate-roles"
    log.log_start("validate-roles", f"product={product_md}")

    mismatches = 0
    incomplete = 0
    pending_repo = ""
    pending_role = ""

    def expand_repo_line(line: str) -> str:
        p = line
        for prefix in ("- repo:", "- repo :"):
            if p.startswith(prefix):
                p = p[len(prefix) :]
                break
        return os.path.expanduser(p.strip())

    def expand_role_line(line: str) -> str:
        r = line
        for prefix in ("- role:", "- role :"):
            if r.startswith(prefix):
                r = r[len(prefix) :]
                break
        return r.strip()

    def check_pair() -> None:
        nonlocal pending_repo, pending_role, mismatches
        if not pending_repo or not pending_role:
            pending_repo = ""
            pending_role = ""
            return
        base = Path(pending_repo).name
        if base != pending_role:
            log.log_warn(
                f"role_repo_basename_mismatch role={pending_role} repo_basename={base} path={pending_repo} "
                "hint=rename_folder_or_set_role_to_match_basename_for_phase4_phase56",
            )
            print(
                f"validate-roles: WARN — role '{pending_role}' ≠ repo basename '{base}' (repo: {pending_repo})",
                file=__import__("sys").stderr,
            )
            mismatches += 1
        pending_repo = ""
        pending_role = ""

    def new_project_block() -> None:
        nonlocal pending_repo, pending_role, incomplete
        if pending_repo and not pending_role:
            print(
                f"validate-roles: WARN — project has repo but no role before next heading: {pending_repo}",
                file=__import__("sys").stderr,
            )
            log.log_warn(f"incomplete_project_block repo={pending_repo} missing_role_line")
            incomplete += 1
        pending_repo = ""
        pending_role = ""

    in_projects = 0
    for line in product_md.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## Projects"):
            new_project_block()
            in_projects = 1
            continue
        if line.startswith("## "):
            if in_projects:
                new_project_block()
                in_projects = 0
            continue
        if not in_projects:
            continue
        if line.startswith("### "):
            new_project_block()
            continue
        if line.lstrip().startswith("- repo:") or line.lstrip().startswith("- repo :"):
            pending_repo = expand_repo_line(line.lstrip())
            continue
        if line.lstrip().startswith("- role:") or line.lstrip().startswith("- role :"):
            pending_role = expand_role_line(line.lstrip())
            check_pair()
            continue

    new_project_block()

    if mismatches == 0 and incomplete == 0:
        log.log_stat("phase=validate-roles mismatches=0 incomplete=0")
        log.log_done("ok")
    else:
        log.log_stat(f"phase=validate-roles mismatches={mismatches} incomplete={incomplete}")
        log.log_done(f"mismatches={mismatches} incomplete={incomplete}")
        if os.environ.get("FORGE_VALIDATE_PRODUCT_STRICT") == "1" and mismatches > 0:
            raise SystemExit(1)
