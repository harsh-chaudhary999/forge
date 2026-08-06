---
name: forge-brain-persist
description: "WHEN: A decision needs to be recorded in the brain. HARD-GATE: Every decision auditable, traceable, retrievable. Brain is immutable record of truth."
type: rigid
version: 1.0.1
preamble-tier: 2
triggers:
  - "persist brain decision"
  - "commit brain to git"
  - "push brain"
allowed-tools:
  - Bash
  - Edit
  - Read
  - Write
  - AskUserQuestion
---
# Brain Persistence (Immutable Record)

**Rule:** Every decision recorded in brain. Never deleted, never lost, always retrievable.

## Anti-Pattern Preamble: Why Agents Skip Brain Recording

| Rationalization | The Truth |
|---|---|
| "This decision is obvious, everyone knows why we did it" | Obviousness is subjective and temporal. In 6 months, "obvious" is forgotten. Record decisions. |
| "Recording decisions slows us down, we need to move fast" | Recording takes 2 minutes. Redebating forgotten decisions takes 2 hours. Speed math is backwards. |
| "We already discussed this in Slack, the decision is documented" | Slack is ephemeral (logs rotate, threads get archived, searches fail). Brain is permanent. Double-record. |
| "The code change itself documents the decision" | Code shows what was built, not why it was built. Future maintainers can't read intent from code. Record reasoning. |
| "Our team is small, we all remember the reasoning" | Teams change. People leave. New members inherit decisions they didn't make. Record for them. |
| "This is a low-stakes decision, it doesn't need to be recorded" | Low-stakes decisions can have downstream consequences. Record all. Severity is determined later. |
| "I'll record the decision later when I have time" | Later never comes. Record immediately or the reasoning is lost while fresh. |
| "The brain is for big architecture decisions, not everyday choices" | Every decision shapes the product. Record all: architecture, config, prioritization, trade-offs, small fixes. |
| "We document everything in Confluence/Notion, that's the brain" | External docs get stale. The brain is source of truth. Link Confluence to brain, not the reverse. |
| "No one needs to know the details, just the final decision" | Reasoning is as important as conclusion. Future trade-offs require understanding original context. Record both. |

## Iron Law

```
EVERY DECISION IS WRITTEN TO BRAIN BEFORE THE TASK MOVES FORWARD. AN UNDOCUMENTED DECISION DOES NOT EXIST — IF IT IS NOT IN THE BRAIN, IT NEVER HAPPENED.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **A decision is recorded in conversation or chat but not committed to `~/forge/brain/`** — Chat history is ephemeral. Brain is permanent. STOP. A decision exists only when it is a committed file in the brain repo. No exceptions.
- **A decision file is written but not committed with `git commit`** — An uncommitted file is not a brain record — it disappears with the working directory. STOP. Every brain write must be followed by an explicit `git -C ~/forge/brain commit` before proceeding.
- **A PRD is locked or a spec is frozen without a corresponding brain decision** — Locking without a brain record means there is no auditable basis for the lock. STOP. Every gate event (PRD lock, spec freeze, trade-off decision) must produce a brain commit before the pipeline advances.
- **`terminology.md` is advanced to `status: locked` in git without a transcript-backed review (or with `open_doubts: pending` while consumers assume locked copy)** — STOP. Product terminology is a first-class decision surface (see [docs/terminology-review.md](../../docs/terminology-review.md) and [brain-write](../brain-write/SKILL.md)). Persist **who / when** in Revision rows or a brain `decisions/` note when the team requires extra audit.
- **Decision body contains only a conclusion without reasoning** — Future maintainers cannot evaluate whether to change a decision if they don't know why it was made. STOP. Every decision must record the alternatives considered and the reasoning for the choice made.
- **An existing brain decision is overwritten instead of superseded** — Overwriting destroys the audit trail of the change. STOP. When a decision changes, create a new decision that references the old one and marks the old decision's status as superseded — never edit the original record.
- **Decision ID is absent or is a generic name like `decision-1`** — Non-unique IDs cause reference collisions and make brain-recall queries ambiguous. STOP. Every decision must have a globally unique ID following the brain naming convention (e.g., `PRD-20260401-auth-2fa`).

## Detailed Workflow

### Identify Decision Points
**Record a decision when:**
- `terminology.md` is first created, materially revised, or set to `locked` after human review (pair with [brain-write](../brain-write/SKILL.md) for format)
- PRD is locked (intake)
- Spec is locked (council)
- Tech plan decided
- Trade-off made (speed vs. quality, cost vs. features)
- Architecture chosen (why this pattern over that)
- Priority decided (why feature X before feature Y)
- Bug root cause found (why did this fail, what was assumption)
- Risk escalated (dreamer intervention)
- Spec conflict resolved
- Task created or split

**Do NOT skip recording because:**
- Decision seems small
- Decision is in code comments
- "Everyone knows this"
- Time pressure exists
- Retrospective recording is planned

### Structure Decision Record
For each decision, record in brain:

**Format: Decision ID** — defer to `forge-brain-layout` (the naming authority) and
`brain-write`'s `decision_id:` field. Canonical global decisions are zero-padded
`D{NNN}` filed under a category:
```
~/forge/brain/decisions/<category>/D<NNN>_<short-topic>.md
Example: decisions/product/D102_session-timeout-strategy.md   (decision_id: D102)
Example: decisions/engineering/D201_orm-vs-raw-sql.md         (decision_id: D201)
```
PRD-scoped records may use the datestamp variant `D<YYYYMMDD>-<NNN>` (as in
`commands/why.md`, e.g. `D20260410-001`). Pick the scheme the active scope uses;
do not invent a third. (This persist/why.md vs layout split is a known
divergence — flag it to forge-brain-layout's owner rather than forking a new form.)

**Required fields:**

1. **What (Decision)**
   - Exact decision made (not paraphrase)
   - What was chosen (and why NOT unchosen alternatives)

2. **Why (Reasoning)**
   - Problem being solved
   - Constraints considered
   - Trade-offs evaluated
   - Evidence or assumptions

3. **Who (Stakeholders)**
   - Who made the decision (person, role)
   - Who was consulted
   - Who disagreed (if applicable)

4. **When (Timeline)**
   - Timestamp (ISO 8601)
   - PR/issue/meeting link
   - Context (what triggered this decision)

5. **Evidence (Justification)**
   - Data supporting the decision (if any)
   - Links to experiments, benchmarks
   - Links to spec/requirements/constraints

6. **Outcome (Tracking)**
   - Was the decision good? (proven later)
   - Did it achieve the goal?
   - What would we do differently?

### Link Decisions
Create semantic edges between decisions:

- **Parent → Child:** "D1-prd-intake gates D2-spec-locked"
- **Alternative:** "D3-postgres chosen over D3-alt-mongodb"
- **Conflict:** "D4-speed goal conflicts with D5-reliability goal"
- **Resolved:** "D6-dreamer resolved D4 vs D5 conflict"
- **Follow-up:** "D7-created follow-up for DB migration task"

**Invoke `/brain-link` to create edges**

### Record During Work (Not Retrospectively)
**When to invoke `/brain-write`:**

- PRD locked: immediately after intake-interrogate
- Spec locked: immediately after council
- Tech plan written: link to spec lock
- Task split: document why split, parent-child link
- Trade-off evaluated: record alternatives considered, rationale
- Escalation made: record to dreamer, what problem triggered escalation
- Merge committed: link to PR, eval result, spec lock
- Bug found: root cause analysis (record assumption that was wrong)

**Do NOT delay:**
- "I'll write it up later" → Write now
- "Let me finish first" → Record decision while implementing
- "The spec document covers it" → Brain supplements spec, doesn't replace

### Retrieve and Audit
**To verify decisions are recorded:**

- Invoke `/brain-recall` (search for decisions by keyword, date, ID)
- Invoke `/brain-why` (trace why any decision was made)
- Verify complete chain: PRD locked → Spec locked → Tech plan → Implementation → Eval pass → Merged
- If any link missing: create retrospective decision record

### Archive Deprecated Decisions
**When decision is superseded:**

1. Do NOT delete the decision
2. Invoke `/brain-forget` to mark as archived (cold decision)
3. Record why it's deprecated (decision ID that replaced it)
4. Keep full history (for audit trail)

### Edge Cases & Fallback Paths

See [reference/edge-cases.md](reference/edge-cases.md) for the full fallback playbook — Cases 1–7 (recording for someone else, async/Slack decisions, conflicting decisions, wrong-in-hindsight, rapid-fire, stale records, sensitive decisions) and Additional Edge Cases 1–5 (ID merge conflict, brain not in git, corrupted decision file, duplicate ID, multi-repo attribution).

### Brain Persistence Checklist

Before claiming work is complete, verify:

- [ ] PRD locked (decision ID: PRDLK-...)
- [ ] Spec locked (decision ID: SPECLOCK-...)
- [ ] Tech plan linked (decision ID: `D<NNN>` or `D<YYYYMMDD>-<NNN>` — same two schemes as everything else here, not a third)
- [ ] All trade-offs recorded (what was chosen, what was not)
- [ ] All constraints recorded (why we can't do X)
- [ ] All escalations recorded (to dreamer, with links)
- [ ] All alternatives considered recorded (and why not chosen)
- [ ] Implementation linked to decisions (PR links to SPECLOCK)
- [ ] Eval result recorded (pass/fail, any learnings)
- [ ] Merge recorded (linked to eval result)
- [ ] Decisions linked together (parent-child, conflict, resolved)
- [ ] No decision left as "TBD" or "TODO"
- [ ] Brain-recall can find all decisions (search by keyword/date)
- [ ] Brain-why trace works (can reconstruct reasoning for any decision)
- [ ] Deprecated decisions marked (not deleted, just archived)

During implementation:

- [ ] Every decision point captures reasoning
- [ ] No decisions made without recording
- [ ] Alternative approaches are documented (not just chosen one)
- [ ] Constraints and trade-offs are explicit

Post-deployment:

- [ ] Outcome recorded (did decision work as expected?)
- [ ] Learnings recorded (what would we change?)
- [ ] Related decisions linked (if outcome changes other decisions)

## Additional Edge Cases

See [reference/edge-cases.md](reference/edge-cases.md) for Additional Edge Cases 1–5 — ID merge conflict (BLOCKED), brain not in git (NEEDS_INFRA_CHANGE), corrupted decision file (BLOCKED on unrecoverable data loss), duplicate decision ID (NEEDS_CONTEXT), and multi-repo attribution (NEEDS_COORDINATION).

Output: **DECISION RECORDED** (auditable, traceable, retrievable in brain, committed to git) or **BLOCKED** (can't persist, merge conflict, brain not in git, data corruption)

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] The brain write used `git add` + `git -C ~/forge/brain commit` — not just a file write; verify the file is tracked by running `git -C ~/forge/brain status` and confirming nothing is left unstaged
- [ ] The commit message includes at least one of `task_id:`, `decision_id:`, or `contract_id:` as an anchor — not a generic message like "record decision" or "update brain"
- [ ] `git -C ~/forge/brain log --oneline -1` confirms the brain commit appears at HEAD with the correct anchor in the subject or body
- [ ] No decision was left only in the conversation transcript — every decision point identified during the task has a corresponding committed file in `~/forge/brain/`
- [ ] `brain-recall` can find the newly committed decision using at least two distinct query terms (keyword search returns the file path)

## Checklist

Before claiming decision recorded:

- [ ] Decision file written with full frontmatter (id, date, product, type, status)
- [ ] Reasoning and alternatives documented — not just the conclusion
- [ ] Decision committed to brain git repo
- [ ] brain-link called to connect this decision to related decisions
- [ ] Decision retrievable via brain-recall with at least 2 query terms
