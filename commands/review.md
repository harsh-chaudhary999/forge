---
description: "Run two-stage code review — spec compliance first, then code quality"
---

Invoke the `forge-trust-code` skill to run the two-stage review pipeline.

**Stage 1 — Spec Reviewer:** Skeptical adversary that reads actual code (doesn't trust the implementer's report). Maps each requirement to code line-by-line. Checks for over-building beyond spec scope.

**Stage 2 — Code Quality Reviewer:** Evaluates across 11 dimensions including naming, file size, complexity, test coverage, performance, security, and observability. Only runs if Stage 1 passes.

**Session style:** Bias **planning-style** for read-heavy spec review; shift to **execution-style** when applying review fixes. See **`docs/platforms/session-modes-forge.md`**.
