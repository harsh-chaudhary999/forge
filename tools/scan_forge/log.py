from __future__ import annotations

import os
from datetime import datetime, timezone


def _emit(level: str, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    script_id = os.environ.get("FORGE_SCAN_SCRIPT_ID", "unknown")
    print(f"FORGE_SCAN|{script_id}|{ts}|{level}|{msg}", flush=True)


def log_start(script_id: str, msg: str) -> None:
    os.environ["FORGE_SCAN_SCRIPT_ID"] = script_id
    _emit("START", msg)


def log_step(msg: str) -> None:
    _emit("STEP", msg)


def log_stat(msg: str) -> None:
    _emit("STAT", msg)


def log_warn(msg: str) -> None:
    _emit("WARN", msg)


def log_error(msg: str) -> None:
    _emit("ERROR", msg)


def log_done(msg: str) -> None:
    _emit("DONE", msg)


def log_die(msg: str, code: int = 1) -> None:
    log_error(f"{msg} exit_code={code}")
    raise SystemExit(code)
