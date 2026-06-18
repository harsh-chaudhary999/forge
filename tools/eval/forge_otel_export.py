#!/usr/bin/env python3
"""Forge OTel exporter — emit a delivery trajectory as OTLP/JSON spans.

Converts a task's `conductor.log` into an OpenTelemetry trace (OTLP/JSON: the
neutral wire format that Langfuse, Braintrust, Arize Phoenix, and any
OTel-compatible backend ingest). One root span per task, one child span per
phase marker; the eval span carries `gen_ai.*` attributes from the OpenTelemetry
GenAI semantic conventions. Trajectory scores ride on the root span.

This lets teams pipe Forge delivery runs into the observability stack they
already run — no vendor lock-in, stdlib only (no OTel SDK dependency).

Usage:
  python3 tools/forge_otel_export.py --task-id <id> [--brain ~/forge/brain] [--out trace.json]

Then POST the file to an OTLP/HTTP traces endpoint, e.g.:
  curl -X POST -H 'Content-Type: application/json' \\
       --data @trace.json http://localhost:4318/v1/traces
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forge_trajectory_eval as traj  # noqa: E402

SERVICE_NAME = "forge"
SERVICE_VERSION = "1.1.0"
FALLBACK_BASE_NS = 1_700_000_000 * 1_000_000_000  # deterministic base when markers lack timestamps


def _hex(seed: str, n: int) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:n]


def _ns(ts: str | None) -> int | None:
    if not ts:
        return None
    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1_000_000_000)
    except ValueError:
        return None


def _attr(key: str, value) -> dict:
    if isinstance(value, bool):
        return {"key": key, "value": {"boolValue": value}}
    if isinstance(value, int):
        return {"key": key, "value": {"intValue": value}}
    if isinstance(value, float):
        return {"key": key, "value": {"doubleValue": value}}
    return {"key": key, "value": {"stringValue": str(value)}}


def build_trace(task_id: str, brain: Path) -> dict:
    log_path = brain / "prds" / task_id / "conductor.log"
    if not log_path.exists():
        raise FileNotFoundError(f"no conductor.log at {log_path}")
    events = traj.parse_log(log_path)
    verdict = traj.analyze(task_id, brain)

    trace_id = _hex(f"forge:{task_id}", 32)

    # Assign start times: real marker ts when present, else a deterministic sequence.
    starts: list[int] = []
    base = next((_ns(e["ts"]) for e in events if _ns(e["ts"]) is not None), FALLBACK_BASE_NS)
    for i, e in enumerate(events):
        starts.append(_ns(e["ts"]) if _ns(e["ts"]) is not None else base + i * 1_000_000_000)
    root_start = starts[0] if starts else base
    root_end = (starts[-1] + 1_000_000_000) if starts else base + 1_000_000_000

    spans = []
    root_span_id = _hex(f"forge:{task_id}:root", 16)
    root_attrs = [
        _attr("forge.task_id", task_id),
        _attr("forge.verdict", verdict.get("verdict", "UNKNOWN")),
        _attr("forge.overall", float(verdict.get("overall", 0))),
        _attr("forge.eval_outcome", verdict.get("eval_outcome") or "none"),
        _attr("forge.self_heal_loops", int(verdict.get("self_heal_loops", 0))),
    ]
    for k, val in verdict.get("scores", {}).items():
        root_attrs.append(_attr(f"forge.score.{k}", float(val)))
    spans.append({
        "traceId": trace_id,
        "spanId": root_span_id,
        "name": f"forge.task {task_id}",
        "kind": 1,  # INTERNAL
        "startTimeUnixNano": str(root_start),
        "endTimeUnixNano": str(root_end),
        "attributes": root_attrs,
    })

    for i, e in enumerate(events):
        start = starts[i]
        end = starts[i + 1] if i + 1 < len(starts) else start + 1_000_000_000
        attrs = [
            _attr("forge.marker", e["marker"]),
            _attr("forge.task_id", task_id),
        ]
        if e["rank"] is not None:
            attrs.append(_attr("forge.phase_rank", float(e["rank"])))
        for fk, fv in (e["fields"] or {}).items():
            attrs.append(_attr(f"forge.field.{fk}", fv))
        # Eval spans carry OTel GenAI semantic-convention attributes.
        if e["marker"].startswith("P4.4-EVAL"):
            attrs += [
                _attr("gen_ai.operation.name", "eval"),
                _attr("gen_ai.system", "forge"),
                _attr("gen_ai.response.finish_reason", e["fields"].get("outcome", "PASS" if e["marker"].endswith("PASS") else "unknown")),
            ]
        spans.append({
            "traceId": trace_id,
            "spanId": _hex(f"forge:{task_id}:{i}:{e['marker']}", 16),
            "parentSpanId": root_span_id,
            "name": e["marker"],
            "kind": 3 if e["marker"].startswith("P4.4-EVAL") else 1,  # CLIENT for GenAI eval spans, else INTERNAL
            "startTimeUnixNano": str(start),
            "endTimeUnixNano": str(end),
            "attributes": attrs,
        })

    return {
        "resourceSpans": [{
            "resource": {"attributes": [
                _attr("service.name", SERVICE_NAME),
                _attr("service.version", SERVICE_VERSION),
            ]},
            "scopeSpans": [{
                "scope": {"name": "forge.conductor", "version": SERVICE_VERSION},
                "spans": spans,
            }],
        }],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Export a Forge delivery trajectory as OTLP/JSON spans.")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--brain", default=None, help="Brain root (default: $FORGE_BRAIN or ~/forge/brain)")
    ap.add_argument("--out", default=None, help="Write OTLP/JSON to this file (default: stdout)")
    args = ap.parse_args()

    try:
        trace = build_trace(args.task_id, traj.brain_root(args.brain))
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    payload = json.dumps(trace, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        n = len(trace["resourceSpans"][0]["scopeSpans"][0]["spans"])
        print(f"wrote {args.out} ({n} spans)")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
