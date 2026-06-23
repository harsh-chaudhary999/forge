# Decision Tree: Trace Depth Strategy

## Decision Tree: Trace Depth Strategy

```
Asked to trace provenance of decision D###
    ↓
Is decision marked as Active or Warm?
├─ NO (Cold/Archived) → Proceed with warning that decision is no longer current
└─ YES → Continue below

Is full parent chain available (all parent → parent → ... → root)?
├─ YES → Trace to root and report full chain
└─ NO → Identify break point and escalate

Do you need shallow trace (immediate parent only)?
├─ YES → Return 1 level: "D### depends on <parent>"
└─ NO → Continue below

Do you need deep trace (full decision graph from root)?
├─ YES → Check depth; warn if > 5 levels
└─ NO → Continue below

Is this decision a root decision (no parent)?
├─ YES → Check evergreen status; if not evergreen, flag as orphan
└─ NO → Continue below

Is provenance complete (all sections documented)?
├─ YES → Trace and return full Why/When/By Whom/Evidence/Alternatives
└─ NO → Trace what's available, flag gaps, escalate for completion

Result:
- Default: Trace to root, report all 5 sections (Why/When/By Whom/Evidence/Alternatives)
- If incomplete: Report available sections, flag gaps
- If deep (>5 levels): Warn about chain depth, still return full trace
- If broken reference: Flag and escalate to brain maintainers
- If circular: Detect and break at cycle point, escalate
```

---

**Linked Skills:**
- `brain-read` — load decision index and decision files
- `brain-write` — record new decisions and lessons learned
- `conductor-orchestrate` — track Phase assignments to decisions

**Example Invocation:**
```bash
/brain-why D42
/brain-why D100
/brain-why D15
```

**Output Format:** Structured markdown with 5 main sections, dependencies, lessons, and patterns.

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] The why explanation references the specific `decision_id` (e.g., `D42`) by name — not a vague description like "the API versioning decision"
- [ ] The source artifact (prd-locked.md, spec doc, or equivalent brain file) is cited by its brain path or git-resolvable link in the Evidence or By Whom section — not paraphrased from memory
- [ ] The reasoning is not vague or placeholder — the Alternatives Considered section lists at least one rejected option with a stated reason for rejection
- [ ] The provenance trace was sourced from the actual brain file at `~/forge/brain/` (or the product brain path), not reconstructed from git log messages or conversation recall
- [ ] If a superseded predecessor exists (a `supersedes:` link in the decision), that predecessor was also read and its chain was followed to confirm the full evolution of the decision
