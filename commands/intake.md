---
description: "Start PRD intake — confidence-first lock in brain (mandatory prd-locked fields; doubt-driven questions)"
---

Invoke the `forge-intake-gate` skill to begin PRD intake.

If the user provided a PRD or description after this command, use it as the initial PRD input.
If no PRD was provided, ask the user to describe what they want to build.

The intake process locks the PRD into `~/forge/brain/prds/` via **`intake-interrogate`**: **variable** number of user turns — only doubts and low-confidence gaps; **stop** when mandatory fields are concrete (two sharp answers can clear many open items; **no** fixed “8 questions” quota).

**Session style:** Prefer **planning-style** for `/intake` (scope and design source-of-truth). See **`docs/platforms/session-modes-forge.md`**.
