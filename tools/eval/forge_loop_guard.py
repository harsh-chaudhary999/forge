#!/usr/bin/env python3
"""Forge loop guard — explicit termination logic for the self-heal loop.

Loop engineering (Steinberger & Osmani, "Loop Engineering: The Architecture of
Autonomous Iteration", 2026): the single most expensive mistake is a loop without
explicit termination. A hard iteration cap **alone is not enough** — a well-built
loop also needs *no-progress detection* (bail when attempts stop changing the
state) and a *budget*. Forge's `self-heal-loop-cap` had the cap; this guard adds
the rest, as a deterministic check run **before the next retry is spent**.

Controls (the four loop-engineering termination levers):
  - cap          — attempt count vs --max-attempts (default 3; the self-heal cap)
  - no-progress  — the last two [P4.4-EVAL-FAIL] attempts share a failure
                   *signature* (same root cause) → stop early: the diagnosis is
                   wrong, the 3rd try won't fix what the 2nd didn't.
  - budget       — optional wall-clock budget via --max-seconds (from marker
                   timestamps); 0 disables it.
  - verifiable   — the loop's success condition is [P4.4-EVAL-GREEN] (checked,
                   not self-assessed); if present, the loop is already DONE.

Verdict: DONE | CONTINUE | ESCALATE_NO_PROGRESS | ESCALATE_CAP | ESCALATE_BUDGET

A failure signature is read from the [P4.4-EVAL-FAIL] marker fields, in order:
`signature=` → `fault=` → `reason=` → `outcome=` → the raw marker. So self-heal
should log `[P4.4-EVAL-FAIL] task_id=<id> signature=<root-cause-id> outcome=<RED|YELLOW>`
for no-progress detection to work at full fidelity (it degrades gracefully otherwise).

Usage:
  python3 tools/eval/forge_loop_guard.py --task-id <id> [--brain ~/forge/brain]
          [--max-attempts 3] [--max-seconds 0] [--strict] [--out guard.json]

Stdlib only. --strict exits 1 on any ESCALATE_* verdict (pre-retry / CI gate).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forge_trajectory_eval as traj  # noqa: E402  (parse_log, brain_root — DRY)

SUCCESS_PREFIXES = ("P4.4-EVAL-GREEN", "P4.4-EVAL-PASS")
FAIL_PREFIX = "P4.4-EVAL-FAIL"
SIG_FIELDS = ("signature", "fault", "reason", "outcome")


def _signature(event: dict) -> str:
    fields = event.get("fields") or {}
    for k in SIG_FIELDS:
        if fields.get(k):
            return f"{k}={fields[k]}"
    return event["marker"]


def _ts(event: dict) -> datetime | None:
    if not event.get("ts"):
        return None
    try:
        return datetime.strptime(event["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def guard(task_id: str, brain: Path, max_attempts: int = 3, max_seconds: int = 0) -> dict:
    log_path = brain / "prds" / task_id / "conductor.log"
    if not log_path.exists():
        return {"task_id": task_id, "verdict": "CONTINUE", "error": f"no conductor.log at {log_path}"}

    events = traj.parse_log(log_path)
    fails = [e for e in events if e["marker"].startswith(FAIL_PREFIX)]
    signatures = [_signature(e) for e in fails]
    attempts = len(fails)

    # A later GREEN/PASS after the last failure means the loop already succeeded.
    last_fail_idx = max((i for i, e in enumerate(events) if e["marker"].startswith(FAIL_PREFIX)), default=-1)
    succeeded = any(
        e["marker"].startswith(SUCCESS_PREFIXES) and i > last_fail_idx
        for i, e in enumerate(events)
    )

    # Elapsed wall-clock across the heal attempts (first→last timestamped event).
    stamped = [t for t in (_ts(e) for e in events) if t is not None]
    elapsed_s = int((stamped[-1] - stamped[0]).total_seconds()) if len(stamped) >= 2 else 0

    no_progress = (
        attempts >= 2
        and signatures[-1] == signatures[-2]
        and not signatures[-1].startswith(("outcome=", "P4.4-EVAL-FAIL"))  # need a real signature, not just RED/YELLOW
    )

    def decide() -> tuple[str, str]:
        if succeeded:
            return "DONE", "a [P4.4-EVAL-GREEN]/PASS follows the last failure — loop succeeded."
        if no_progress:
            return ("ESCALATE_NO_PROGRESS",
                    f"attempts {attempts-1} and {attempts} share signature {signatures[-1]!r} — "
                    "the root-cause diagnosis is wrong; escalate instead of spending another retry.")
        if attempts >= max_attempts:
            return ("ESCALATE_CAP",
                    f"{attempts} failed attempts ≥ cap {max_attempts} — escalate BLOCKED with all evidence.")
        if max_seconds and elapsed_s > max_seconds:
            return ("ESCALATE_BUDGET",
                    f"elapsed {elapsed_s}s > budget {max_seconds}s — escalate; the loop is over budget.")
        return ("CONTINUE",
                f"{attempts}/{max_attempts} attempts, distinct signatures — a next retry is within bounds.")

    verdict, reason = decide()
    return {
        "task_id": task_id,
        "log": str(log_path),
        "attempts": attempts,
        "max_attempts": max_attempts,
        "signatures": signatures,
        "no_progress": no_progress,
        "elapsed_seconds": elapsed_s,
        "max_seconds": max_seconds,
        "succeeded": succeeded,
        "verdict": verdict,
        "reason": reason,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Loop-engineering termination guard for the Forge self-heal loop.")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--brain", default=None, help="Brain root (default: $FORGE_BRAIN or ~/forge/brain)")
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--max-seconds", type=int, default=0, help="Wall-clock budget; 0 disables.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on any ESCALATE_* verdict")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    v = guard(args.task_id, traj.brain_root(args.brain), args.max_attempts, args.max_seconds)
    payload = json.dumps(v, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(f"loop-guard {v['task_id']}: {v['verdict']} — {v.get('reason') or v.get('error','')}")
        print(payload)

    if args.strict and str(v["verdict"]).startswith("ESCALATE"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
