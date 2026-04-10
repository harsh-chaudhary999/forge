---
description: "Build tasks in isolated worktrees using TDD — red, green, refactor"
---

Invoke the `forge-worktree-gate` skill first to ensure worktree isolation, then invoke `forge-tdd` for test-driven development.

This requires approved tech plans. If no plans are approved, direct the user to run `/plan` first.

Each task gets a fresh git worktree per project. The dev-implementer subagent builds using strict TDD: write failing test (RED) → implement minimal code (GREEN) → refactor while tests pass.
