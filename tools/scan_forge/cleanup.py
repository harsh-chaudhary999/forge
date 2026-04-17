from __future__ import annotations

from pathlib import Path

from . import log


def run_cleanup(scan_tmp: Path) -> None:
    scan_tmp = scan_tmp.resolve()
    log.log_start("cleanup", f"action=remove_glob pattern={scan_tmp}/forge_scan_*.txt")
    paths = sorted(scan_tmp.glob("forge_scan_*.txt"))
    before = len(paths)
    for p in paths:
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
    print(f"Cleanup: removed {before} {scan_tmp}/forge_scan_*.txt files")
    log.log_done(f"files_removed={before}")
