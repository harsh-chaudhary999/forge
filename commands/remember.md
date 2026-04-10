---
description: "Record a decision, learning, or pattern to brain with full provenance"
---

Invoke the `brain-write` skill.

The user's argument is the decision or learning to record.
If no content was provided, ask the user what they want to remember.

Brain-write creates a decision record with: decision ID, timestamp, context, rationale, alternatives considered, confidence level, and linked decisions. The record is git-committed to `~/forge/brain/`.
