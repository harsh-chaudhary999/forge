---
description: "Diagnose and fix eval failures — locate fault, triage, debug, fix (max 3 attempts)"
---

Invoke the `self-heal-locate-fault` skill to begin the self-heal loop.

The self-heal pipeline: locate which service failed → triage the failure (flaky test, bad test, real bug, or environment issue) → systematic debug (4-phase investigation) → fix in the affected project.

Maximum 3 retry attempts. If the issue persists after 3 loops, escalation to the user is required.

**Session style:** Prefer **execution-style** for `/heal` (logs, edits, re-run eval). See **`docs/platforms/session-modes-forge.md`**.
