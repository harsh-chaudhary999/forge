---
name: forge-brain-persist
description: "WHEN: A decision needs to be recorded in the brain. HARD-GATE: Every decision auditable, traceable, retrievable. Brain is immutable record of truth."
type: rigid
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
- **Decision body contains only a conclusion without reasoning** — Future maintainers cannot evaluate whether to change a decision if they don't know why it was made. STOP. Every decision must record the alternatives considered and the reasoning for the choice made.
- **An existing brain decision is overwritten instead of superseded** — Overwriting destroys the audit trail of the change. STOP. When a decision changes, create a new decision that references the old one and marks the old decision's status as superseded — never edit the original record.
- **Decision ID is absent or is a generic name like `decision-1`** — Non-unique IDs cause reference collisions and make brain-recall queries ambiguous. STOP. Every decision must have a globally unique ID following the brain naming convention (e.g., `PRD-20260401-auth-2fa`).

## Detailed Workflow

### Identify Decision Points
**Record a decision when:**
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

**Format: Decision ID (D prefix)**
```
D<YYYY><MM><DD>-<SEQUENCE>-<SHORTNAME>
Example: D20240415-001-prd-intake-auth
Example: D20240415-002-spec-locked-auth
Example: D20240415-003-schema-decision-postgres
```

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

#### Case 1: Decision Made by Someone Else (You're Recording for Them)
- **Symptom:** "The architect decided on this pattern, I need to record it"
- **Do NOT:** Record it yourself without consulting architect
- **Action:**
  1. Ask architect to provide: reasoning, constraints, alternatives considered
  2. Create decision record with architect as primary decider
  3. Get architect to review and approve the record
  4. Link decision to any prior discussions (email, PR comment)

#### Case 2: Decision Made Asynchronously (Slack, Email, PR Comment)
- **Symptom:** "The team debated the approach in Slack threads"
- **Do NOT:** Rely on Slack as the permanent record
- **Action:**
  1. Collect all input (extract relevant messages)
  2. Synthesize decision (what was actually decided?)
  3. Create decision record with synthesis
  4. Link to Slack thread (for reference, not as primary record)
  5. Record in brain as source of truth

#### Case 3: Conflicting Decisions (Two Decisions Contradict Each Other)
- **Symptom:** "D1 says use pattern X, D2 says use pattern Y"
- **Do NOT:** Ignore the conflict, pick one later
- **Action:**
  1. Create conflict record: "D1 vs D2 conflict identified"
  2. Escalate to dreamer for clarification
  3. Dreamer resolves: which is correct? Or are both valid in different contexts?
  4. Record dreamer decision as D3 (precedence or scope boundaries)

#### Case 4: Decision Turns Out to Be Wrong (In Hindsight)
- **Symptom:** "We chose approach X, but it failed in production"
- **Do NOT:** Delete the original decision, hide the failure
- **Action:**
  1. Keep original decision (D1)
  2. Record new decision (D2): "D1 was wrong because Y, we're switching to Z"
  3. Link D2 as "supersedes D1" with reason
  4. Record lessons learned in brain (why was D1 wrong)
  5. Mark D1 as archived (not deleted)

#### Case 5: Rapid-Fire Decisions (Multiple Decisions in Quick Succession)
- **Symptom:** "We made 10 decisions in a 2-hour meeting"
- **Do NOT:** Skip recording because it's overwhelming
- **Action:**
  1. Record all 10 decisions immediately after meeting
  2. Use sequential IDs (D-001, D-002, ..., D-010)
  3. Link them as siblings (all from same meeting)
  4. Use short format if time-pressured (expand later)
  5. Set reminder to review and expand short records within 24h

#### Case 6: Decision Records Become Stale (Wrong or Outdated)
- **Symptom:** "Decision D1 recorded 6 months ago no longer applies"
- **Do NOT:** Modify or delete D1
- **Action:**
  1. Create new decision record (D-new): "D1 is superseded by D-new due to X"
  2. Link D-new to D1 (with reason for change)
  3. Mark D1 as archived (but keep full history)
  4. All future refs should link to D-new, not D1

#### Case 7: Sensitive Decision (Security, Confidential, Privacy)
- **Symptom:** "This decision involves sensitive data, should we record it?"
- **Do NOT:** Skip recording for "security through obscurity"
- **Action:**
  1. Record the decision (recording is not publishing)
  2. Mark record as CONFIDENTIAL (if applicable)
  3. Access control: only relevant team members can read
  4. Record just as thoroughly as non-sensitive decisions
  5. Secure the brain (don't expose to public)

### Brain Persistence Checklist

Before claiming work is complete, verify:

- [ ] PRD locked (decision ID: PRDLK-...)
- [ ] Spec locked (decision ID: SPECLOCK-...)
- [ ] Tech plan linked (decision ID: TECHPLAN-...)
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

### Edge Case 1: Decision Already Exists with Different Content (Merge Conflict)
**Situation:** Brain already has a decision record with same ID or very similar content, but the new decision conflicts with it.

**Example:** Decision "D1-schema-approach-postgres" was recorded 3 days ago. Now a new decision is being made with same ID, different approach (MySQL instead of postgres). Conflict in brain.

**Do NOT:** Overwrite the old decision. Overwriting destroys audit trail.

**Action:**
1. Identify: why are there two decisions with same ID?
   - Same decision re-recorded? (duplication)
   - Conflicting decisions with same ID? (merge conflict)
2. If duplication (same decision recorded twice):
   - Keep the older record (original decision point)
   - Link new record to old one: "Re-affirmed D1 [reasons why]"
   - Mark new record status as "affirmed_previous" (not independent)
3. If conflict (different decisions, same ID):
   - Do NOT overwrite or delete
   - Create new decision: "D2-schema-conflict" (different ID)
   - Document: "D1 vs D2 conflict identified"
   - Escalate to dreamer for arbitration
   - Record dreamer decision: which is correct, or are both valid in different contexts?
4. Preserve full history: old decision, new decision, conflict record, dreamer arbitration
5. Escalation keyword: **BLOCKED** (cannot proceed until conflict resolved)

---

### Edge Case 2: Brain Not in Git (Lost Version Control, No Audit Trail)
**Situation:** Brain directory exists but is not tracked in git. Decisions are written but not committed. No version control = no audit trail.

**Example:** Agent writes decision to brain file, but forgets to `git commit`. Decision is on disk but not in git history.

**Do NOT:** Treat uncommitted brain files as recorded decisions. They are at risk of loss.

**Action:**
1. Identify: is brain directory a git repo?
   ```bash
   cd ~/forge/brain && git status
   ```
2. If NOT a git repo:
   - Initialize: `git init`
   - Add .gitignore (if any sensitive files)
   - Commit initial state
   - Escalate: **NEEDS_INFRA_CHANGE** (brain must be in git)
3. If git repo but decision is uncommitted:
   - Stage the decision file: `git add decision_id.md`
   - Commit immediately: `git commit -m "record: [decision summary]"`
   - Do NOT proceed until committed
4. Verify: brain commit appears in git log
5. Document in brain: how brain git infrastructure was restored

---

### Edge Case 3: Decision File Corrupted (Invalid YAML, Read Error, Incomplete)
**Situation:** Decision file exists but is corrupted, incomplete, or has invalid format. Brain-recall or brain-why cannot parse it.

**Example:** Decision file has malformed YAML (missing quotes, bad indentation). Or file was partially written (power loss, disk failure). Or file encoding is wrong (UTF-8 vs. ASCII).

**Do NOT:** Delete or overwrite corrupted file. Preserve for forensics.

**Action:**
1. Detect: try to read decision file
   ```bash
   cat ~/forge/brain/decisions/D1-xxxx.md
   ```
2. If file is unreadable:
   - Check encoding: `file <filename>`
   - Try to view in hex: `hexdump -C <filename> | head -20`
   - Document what you find
3. If file is incomplete (partial write):
   - Recover what you can (read partial content)
   - Create new decision record with recovered content
   - Mark old file as "corrupted" (don't delete)
   - Create new decision with unique ID (don't reuse corrupted ID)
4. If file has invalid YAML:
   - Copy file to backup: `cp file.md file.md.corrupted`
   - Fix YAML manually (correct indentation, quoting, etc.)
   - Validate: `yaml file.md` (use yaml parser)
   - Git commit the fix
5. If file cannot be recovered:
   - Create recovery record: "D-recovery-YYYY-MM-DD: Lost decision [description], attempted recovery"
   - Document what was lost, why, when noticed
   - Escalate: **BLOCKED** (data loss in brain)
6. Review: why was data corrupted? Disk issue? Permission issue? Commit process broken?

---

---

### Edge Case 4: Duplicate Decision ID Attempted (Same ID Written Twice)

**Situation:** Agent attempts to write a new decision with ID D042, but D042 already exists in the brain with different content (different feature, different date).

**Do NOT:** Overwrite the existing decision. ID collisions corrupt the audit trail.

**Action:**
1. Read the existing D042 to understand what it records
2. If the new decision is truly different, assign the next available ID (D043, D044...)
3. If the new decision is an update to D042 (same feature, new information), create D042-amendment instead
4. If the existing D042 is stale/wrong and should be replaced, invoke `brain-forget` on D042 first, then write D043 with a `replaces: D042` link
5. Never write two decisions to the same ID path — the last write wins and prior content is lost without trace
6. Escalation: NEEDS_CONTEXT — if the ID conflict suggests a wider brain indexing problem (gaps, skips, non-sequential IDs), surface it to the dreamer

---

### Edge Case 5: Decision Requires Multi-Repo Attribution (Two Teams, One Decision)

**Situation:** A shared architectural decision (e.g., "all services use JWT for authentication") affects the backend, mobile, and web repos. The decision was made jointly by backend and mobile leads. Who owns the brain record?

**Do NOT:** Write the decision into only one repo's brain files. Shared decisions without shared attribution create knowledge silos.

**Action:**
1. Write the decision to the product-level brain (not repo-level): `~/forge/brain/products/<slug>/decisions/`
2. Set `type: cross-repo-architecture` in the frontmatter
3. List all affected repos in a `scope:` field: `scope: [backend, web, mobile]`
4. Link the decision from each repo's relevant module brain file using `brain-link`
5. If each repo needs repo-specific implementation notes, write separate `D042-backend-impl.md` and `D042-mobile-impl.md` that reference the parent D042
6. Escalation: NEEDS_COORDINATION — notify all surface leads that a shared decision has been recorded and they are responsible for implementation in their respective repos

---

Output: **DECISION RECORDED** (auditable, traceable, retrievable in brain, committed to git) or **BLOCKED** (can't persist, merge conflict, brain not in git, data corruption)

## Checklist

Before claiming decision recorded:

- [ ] Decision file written with full frontmatter (id, date, product, type, status)
- [ ] Reasoning and alternatives documented — not just the conclusion
- [ ] Decision committed to brain git repo
- [ ] brain-link called to connect this decision to related decisions
- [ ] Decision retrievable via brain-recall with at least 2 query terms
