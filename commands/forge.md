---
description: "Run the full Forge pipeline: PRD → Intake → Council → Tech Plans → Build → Eval → Review → PR Set → Brain"
---

Invoke the `conductor-orchestrate` skill to run the full Forge pipeline.

If the user provided a PRD or product description after this command, use it as the initial input.
If no PRD was provided, ask the user to describe what they want to build or provide a path to an existing PRD document.

The conductor will orchestrate the entire flow: intake → council → tech plans → human approval → build → review → eval → self-heal (if needed) → PR coordination → dreamer retrospective.
