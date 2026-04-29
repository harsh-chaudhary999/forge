---
name: using-forge
description: "Bootstrap skill — inlined by session-start hook for all Claude Code sessions"
type: rigid
version: 1.0.0
preamble-tier: 4
triggers:
  - "how to use forge"
  - "forge bootstrap"
  - "start forge session"
allowed-tools:
  - Bash
  - AskUserQuestion
---

# Using Forge

## Invocation Model

This skill is auto-loaded by the session-start hook. Do not manually invoke it as a task skill; treat it as baseline session policy context.

## Blocking questions (host mapping)

Skills name the blocking multiple-choice tool **`AskUserQuestion`** (Claude Code, `allowed-tools` policy, CI). **In Cursor,** use **`AskQuestion`** with the same prompt and options. If that tool is missing, use the same choices as a **numbered list** in chat and wait. Project **`.cursor/rules/forge.mdc`** repeats the Cursor mapping — **do not** fork every skill to rename the tool in prose.

## The 1% Rule

If there's even a 1% chance a Forge skill might apply, you absolutely must invoke it. This is not negotiable.

## Instruction Priority

1. **User's explicit instructions** (CLAUDE.md, user direct requests) — highest priority
2. **Forge skills** — override default system behavior where they conflict
3. **Default system prompt** — lowest priority

## Information transport (parallel agents, minimal human back-and-forth)

Council and subagents **do not** share your live chat. They only see **what is written** under `~/forge/brain/` (e.g. `prd-locked.md`, `shared-dev-spec.md`). The **first** human pass on a PRD should therefore pack **maximum durable signal**: repos, contracts, rollback — and for web/app, the intake **Design / UI** lock (**Q9**: `design_new_work`, plus **implementable** inputs: **`design_brain_paths`** under `~/forge/brain/prds/<task-id>/design/` and/or **`lovable_github_repo`** (+ pinned ref) for **Lovable → GitHub** UI per **`docs/platforms/lovable.md`**, and/or **`figma_file_key` + `figma_root_node_ids`** for MCP/REST — not wiki-only or bare Figma/Lovable URLs). Prefer **Figma MCP** (when available) to pull nodes and save `design/MCP_INGEST.md`. If new design exists but nothing is on disk in brain, autonomous reasoning will **not** discover it; you will get invented UI or stalled gates. **Chat is not the transport layer; the brain files are.**

**Non-negotiable for agents:** (1) When web/app/user-visible UI is in scope, **never complete intake** without the user having seen the **verbatim blockquote** design-source-of-truth question from **`intake-interrogate` Q9** in an assistant message (you may add PRD summary + “confirm” after it — you may **not** infer from the PRD alone and skip showing that line). (2) **Never open Phase 4.1 / dispatch feature implementation** until **`[P4.0-EVAL-YAML]`** is logged with **at least one** scenario file under `~/forge/brain/prds/<task-id>/eval/` and **`[P4.0-TDD-RED]`** per policy — see **`conductor-orchestrate` State 4b**. (3) Require **`[P4.0-QA-CSV]`** after approved **`qa/manual-test-cases.csv`** when **`forge_qa_csv_before_eval: true`** in **`product.md`** **or** when the user invoked **full `/forge`** (`commands/forge.md`) — same acceptance alignment for **TDD** and **eval**; see **`qa-manual-test-cases-from-prd`**. Procedural text is not a CI bot: **you** must refuse to skip these steps.

**Optional machine layer (teams):** Run **`python3 tools/verify_forge_task.py --task-id <id> --brain ~/forge/brain`** in CI or pre-push on the **brain** repo so missing **`eval/*.yaml`** or bad **`conductor.log`** ordering fails the build — see **`docs/forge-task-verification.md`**. Add **`pip install -r tools/verify/requirements-verify.txt`** then **`--validate-eval-yaml`** so CI rejects malformed or empty-`expected` scenarios, not only “≥1 yaml file exists.” Use **`--strict-tech-plans`** once **`tech-plans/*.md`** exist to fail **`REVIEW_PASS`** without FORGE-GATE Section 0c / recross anchors or misplaced **`### 1b.2a`** (**`tools/verify_tech_plans.py`**). Enable **`--check-shared-spec`** (frozen shared spec checklist + TBD scan) and **`--validate-phase-ledger`** / **`--phase-ledger-verify-hashes`** when you use **`phase-ledger.jsonl`** (see **`tools/append_phase_ledger.py`**). The tool also **warns on stderr** when several **`prds/*/conductor.log`** files exist — keep **`FORGE_TASK_ID`** set in CI and locally so hooks and warnings align with the active task. Use **`--strict-single-task-brain`** in CI when exactly one active task is guaranteed. **`tools/forge_drift_check.py`** compares **Success Criteria** bullets to eval/QA text for obvious drift. On the **Forge** repo, CI runs **`tools/lint_skill_allowed_tools.py`** so rigid skills keep **`allowed-tools`** and **`tools/skill-tool-policy.json`** stays in sync. **`FORGE_BRAIN`** and **`FORGE_BRAIN_PATH`** are both accepted as the brain root for Python CLIs and hooks. The IDE still does not compile-check sessions; this checks **committed** artifacts.

**Session style (all hosts):** Forge cannot toggle your editor’s **planning vs execution** mode (or permissions) programmatically. Convention: **planning-style** for intake, council, and tech-plan **review**; **execution-style** for build, eval, heal. Instruct the user to switch style or permissions when the Forge phase changes — see **`docs/platforms/session-modes-forge.md`** (each platform doc links the same rules to local UI names).

## Agent reliability (diversion, hallucination, context collapse)

1. **Pin the task** — If more than one `prds/*/conductor.log` exists under the brain, set **`FORGE_TASK_ID`** (or **`FORGE_PRD_TASK_ID`**) before relying on stage injection or “next gate” hints; otherwise the hook may pick the **wrong** log by mtime.
2. **Brain over chat** — Subagents and later sessions **do not** see this chat. **Decisions, scope changes, and URLs** must land under **`~/forge/brain/prds/<task-id>/`** (and related paths). If it is only in chat, assume it **will be lost** or **hallucinated** later.
2b. **Written evidence (what / where / how)** — Anything you write for humans or subagents (plan digests, scan summaries, QA notes, eval rationales, test descriptions) must be **checkable**: **what** (path, id, symbol), **where** (repo or brain path), **how** (command + cwd, `Read`/`rg`, artifact field). Headline counts and **"N+"** scale without identifiers violate **AGENTS.md** — *Written artifacts — precision*; counts are optional, not a substitute for paths.
2c. **Volume is not a skip lever** — Multi‑thousand‑line files, full export extractions, or large brain writes are **not** blockers you may self‑waive. **Execute every required step** (batched `Read`, incremental `Write`, streaming Shell). Only **BLOCKED** (with evidence) or the **explicit** stop rules **inside the invoked skill** can halt work — not “too large” as a discretionary excuse (**AGENTS.md** Core rule **6**).
3. **Re-anchor after compact / clear** — After context compaction or a new session, **read** `prd-locked.md`, `shared-dev-spec.md` (if present), and the **tail** of `conductor.log` before big moves. Ask the human to restate **goal + non-negotiables** in one message if anything is ambiguous.
4. **One objective per thread** — Vague “keep going” invites the wrong skill path (e.g. council when the user wanted a bugfix). State **what** and **what not to touch**.
5. **Stubs are not specs** — Scan output and `modules/*.md` stubs are **hypotheses**. Confirm behavior with **real source**, APIs, or tests before implementing.
6. **Subagent handoff** — When dispatching work that will not see this chat, write a **short handoff file** under the task brain (what was decided, what to do, links) so the parent does not **collapse** child context into a wrong summary.

**Claude Code `session-start` hook (stage + preamble):** Optional env vars (export in shell or IDE env before launching Claude):

| Variable | Purpose |
|----------|---------|
| **`FORGE_TASK_ID`** or **`FORGE_PRD_TASK_ID`** | Use **`~/forge/brain/prds/<id>/conductor.log`** for stage detection. **Recommended** when multiple tasks exist; otherwise the hook picks the **newest mtime** among `prds/*/conductor.log`, which can be the wrong task. |
| **`FORGE_BRAIN`** or **`FORGE_BRAIN_PATH`** | Brain root if not **`~/forge/brain`** (either name; same semantics). |
| **`FORGE_PREAMBLE_TIER`** | `1`–`4`: which **`skills/_preamble/tier-N.md`** is prepended (default **`2`**). |
| **`FORGE_HOOKS_DEBUG=1`** | Log conductor.log path + resolved stage to stderr (hook diagnostics). |
| **`FORGE_DISABLE_CANARY=1`** | Skip writing **`~/.forge/.canary`** and skip canary-in-command checks in **`pre-tool-use`** (trusted local only). |

Stage resolution uses the **last** `[P…]` marker in the chosen log; implementation: **`.claude/hooks/forge-stage-detect.cjs`**. Run **`node .claude/hooks/test-forge-stage-detect.cjs`** (from repo root) to verify mapping after edits.

## Anti-Pattern Enforcement (HARD-GATE)

### Anti-Pattern 1: "This is a simple question, I don't need a skill"

**Why This Fails:**
Simple feels deceptive. You assume you understand scope, but the skill catalog surfaces edge cases you didn't anticipate. Small tasks hide correctness gaps that compound downstream.

**Enforcement (MUST):**
1. MUST check skill catalog before proceeding
2. MUST read edge case section of any potentially applicable skill
3. MUST verify no skill requires pre-work (e.g., brain-read before eval-*)
4. MUST follow skill discipline even for 1-line tasks
5. MUST reject the rationalization "I'll skip this one time"

---

### Anti-Pattern 2: "I need more context before I can pick a skill"

**Why This Fails:**
Skills provide the context-gathering process itself. Waiting for clarity before invoking a skill means you skip the intake or intake-interrogate phase. Skills are designed to surface context gaps, not assume they're pre-filled.

**Enforcement (MUST):**
1. MUST invoke the process skill (intake, intake-interrogate, brain-read) FIRST
2. MUST let the skill ask questions; don't pre-answer
3. MUST allow the skill to surface hidden context dependencies
4. MUST NOT invent context from memory and skip skill invocation
5. MUST escalate NEEDS_CONTEXT if skill reveals missing information

---

### Anti-Pattern 3: "I know this skill's content from memory"

**Why This Fails:**
Skills evolve. Your memory is stale from context collapse or prior session. The skill may have new enforcement gates, edge cases, or dependency chains. Running old logic from memory causes silent failures.

**Enforcement (MUST):**
1. MUST always read current skill file, never rely on memory alone
2. MUST check the skill's requires field for dependencies
3. MUST verify no HARD-GATE changes since last session
4. MUST re-read edge cases even if you've seen the skill before
5. MUST treat memory as a hint, not truth; let the skill be authoritative

---

### Anti-Pattern 4: "Multiple skills apply, I'll pick one and infer the rest"

**Why This Fails:**
Each skill has a priority order. Picking one arbitrarily and inferring the rest causes gaps. forge-eval-gate and forge-council-gate both apply to PRDs — but council must run BEFORE eval. Skipping one leaves your work unchecked.

**Enforcement (MUST):**
1. MUST invoke all applicable skills in priority order (process → implementation → reference)
2. MUST NOT skip a skill because you think you understand its output
3. MUST NOT infer skill behavior from a prior skill's result
4. MUST trace skill dependencies via the requires field
5. MUST explicitly report if a skill is deliberately omitted and why

---

### Anti-Pattern 5: "The user just wants a quick answer"

**Why This Fails:**
Quick answers that skip skills cause correctness failures. These failures are then discovered in eval or production, turning a 2-minute skill invocation into a 2-hour debugging session. Skill invocation IS the faster path long-term.

**Enforcement (MUST):**
1. MUST run the skill even if user asks for speed
2. MUST show user the skill output, not a summarized guess
3. MUST explain why the skill is necessary (e.g., "eval catches 60% of bugs")
4. MUST NOT override skill requirement for speed; user preference = override only for explicit exceptions
5. MUST log the exception if user explicitly waives skill invocation

## Edge Cases

### Edge Case 1: Skill Not Found in Catalog

**Symptom:**
Skill tool returns "not found" or skill is referenced but doesn't exist in `~/forge/skills/`.

**Do NOT:**
Invent behavior from memory. Proceed as if a missing skill is equivalent to running it.

**Action:**
1. Check using-forge skill catalog (this file, "Where Things Live")
2. Search for nearest skill by name prefix or similar function
3. Report the gap: "Skill X missing from catalog"
4. Identify workaround or escalate

**Escalation:**
`NEEDS_CONTEXT` — Forge skill catalog incomplete

---

### Edge Case 2: Two Skills Both Apply

**Symptom:**
forge-eval-gate and eval-coordinate-multi-surface both seem relevant. forge-council-gate and reasoning-as-web-frontend overlap. Ambiguous ordering.

**Do NOT:**
Pick one arbitrarily. Assume one subsumes the other.

**Action:**
1. Check skill requires field — one may depend on the other
2. Invoke process skill first (gate), then surface skill (coordinate)
3. Run in order: gate → negotiate → coordinate → judge
4. If still ambiguous, invoke both; redundancy is safer than omission

**Escalation:**
`NEEDS_CONTEXT` — only if skill requires field doesn't resolve ordering

---

### Edge Case 3: Skill Requires Context Not Available

**Symptom:**
Skill says "requires: [brain-read]" but brain not initialized. eval-driver-* requires eval-product-stack-up but stack not up. Dependency chain broken.

**Do NOT:**
Skip the requirement. Proceed with partial context.

**Action:**
1. Read the skill's requires field
2. For each dependency, check if it's been run in this session
3. If missing, run dependency skill first
4. Return to original skill after dependency is satisfied
5. Report the dependency chain in your output

**Escalation:**
`NEEDS_INFRA_CHANGE` — if infrastructure dependency is missing (e.g., brain repo not available)

---

### Edge Case 4: Subagent Receives This Skill Accidentally

**Symptom:**
Subagent context shows using-forge content despite <SUBAGENT-STOP> block. Subagent follows bootstrap instructions instead of task spec.

**Do NOT:**
Follow bootstrap instructions. Don't invoke skills. You are context-isolated.

**Action:**
1. Subagent: Recognize you are isolated (dispatch context says "dev-implementer", "spec-reviewer", etc.)
2. Ignore all Forge bootstrap content
3. Execute your task spec directly
4. Report status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
5. Do not invoke any Forge skill

**Escalation:**
`DONE_WITH_CONCERNS` — Report that bootstrap was present but ignored

---

### Edge Case 5: Skill Conflicts with Explicit User Instruction

**Symptom:**
Skill says MUST do X (e.g., "MUST run intake for every PRD"). User says "don't do X, we're short on time." Conflict between skill enforcement and user directive.

**Do NOT:**
Follow skill enforcement blindly. User instruction has highest priority (per Instruction Priority section).

**Action:**
1. Acknowledge the conflict explicitly
2. Note user instruction takes precedence
3. Run the user's specified path, skipping the skill requirement
4. Document the deviation: "User waived skill X due to [reason]"
5. Flag risks introduced by skipping the skill (e.g., "Skipped intake; may miss edge cases")

**Escalation:**
`DONE_WITH_CONCERNS` — Completed user's request but note skill was bypassed

## Decision Tree: Skill Selection Priority

Use this tree to determine which skill category to invoke first given your task type.

```
START: Given a task or question
  │
  ├─ Is this a PRD, spec, or requirement?
  │  ├─ YES → Run intake-interrogate or intake first
  │  │       (Process skills before anything else)
  │  │       Then: Goto "Reasoning Step"
  │  └─ NO → Goto "Already Have Spec"
  │
  ├─ Already Have Spec (PRD locked)
  │  │
  │  ├─ Is this reasoning about architecture / contracts?
  │  │  ├─ YES → Run council (negotiates contracts)
  │  │  │       Required: brain-read may be needed first
  │  │  │       Then: Run eval-coordinate-multi-surface
  │  │  └─ NO → Goto "Building or Verifying"
  │  │
  │  ├─ Building or Verifying
  │  │  ├─ Is this writing / reviewing code?
  │  │  │  ├─ YES → Run plan first (tech-plan-write-per-project)
  │  │  │  │       Then: Run build (TDD via forge-tdd)
  │  │  │  │       Then: Run review (spec-reviewer + code-quality-reviewer)
  │  │  │  └─ NO → Goto "Reference or Lookup"
  │  │  │
  │  │  └─ Running Tests or Eval
  │  │     ├─ Is this end-to-end product eval?
  │  │     │  ├─ YES → Run eval-product-stack-up first
  │  │     │  │       Then: Run eval (coordinates all drivers)
  │  │     │  │       Then: Run eval-judge
  │  │     │  └─ NO → Run specific eval-driver-*
  │  │
  │  └─ Reference or Lookup
  │     ├─ Looking up decisions / brain?
  │     │  ├─ YES → Run brain-read
  │     │  │       If tracing decision: brain-why
  │     │  │       If recording decision: brain-write
  │     │  └─ NO → Generic forge skill?
  │     │
  │     └─ Check forge-glossary or status
  │        Run forge-status for pipeline state
  │
  └─ DONE: Invoke identified skill(s) in order
```

**Priority Rule:**
Process (intake/council) → Implementation (plan/build/review) → Reference (brain/glossary)

**Key Check:**
If two skills apply and order is ambiguous, check the `requires` field in both skill files. The skill with no requires often runs first.

## Iron Law

```
WHEN THERE IS A 1% CHANCE A SKILL APPLIES, INVOKE IT BEFORE ANY RESPONSE. PROCESS SKILLS FIRST. IMPLEMENTATION SKILLS SECOND. SUBAGENTS EXECUTE THEIR TASK AND REPORT STATUS — THEY DO NOT RE-RUN THE BOOTSTRAP.
```

## Where Things Live

- **Brain:** `~/forge/brain/` (git repo, source of truth)
- **Product config:** `~/forge/brain/products/<slug>/product.md` (repos, roles, infra)
- **Codebase scan:** `~/forge/brain/products/<slug>/codebase/` (module map, patterns, API surface)
- **Manual QA from PRD:** `~/forge/brain/prds/<task-id>/qa/` — `qa-analysis.md` (brain-loaded analysis + test type / surface / coverage lock), `manual-test-cases.csv` (`qa-prd-analysis` → `qa-manual-test-cases-from-prd`), `scenarios-manifest.md` (coverage matrix), `branch-env-manifest.md` (branch SHAs + env), `qa-run-report-<ts>.md` (verdict + failures) — full standalone QA pipeline via `/qa`, `/qa-write`, `/qa-run`
- **Skills:** `~/.claude/skills/<skill-name>/SKILL.md`
- **Subagents:** `~/.claude/agents/<agent-name>.md`

## Onboarding an Existing Project

If you are starting Forge on a **codebase that already exists** (not greenfield):

1. Run `/workspace` to register repos and create `product.md` — scan runs automatically
2. If scan was skipped or is stale, run `/scan <slug>` before council
3. `product-context-load` will warn you if the scan is absent or >7 days old
4. `forge-council-gate` will check scan freshness before each council session

The codebase scan gives surface agents architecture context they cannot derive from the PRD alone. Skipping it means council will produce tech plans that may conflict with the existing structure.

**Scan staleness rule:** <7 days = fresh. 7-30 days = warn. >30 days = prompt to refresh before council.

## Brain-first routing (then open product sources)

When deciding **where** in a product repo work belongs — council arguments, tech-plan file lists, eval targets, or exploratory reads before a plan exists — **use the brain codebase scan first**, then open repo files.

1. **Read** `~/forge/brain/products/<slug>/codebase/index.md`, `SCAN.json`, and relevant `codebase/modules/*.md`, `api-surface.md`, `patterns.md` as needed.
2. **From that**, extract real paths and module boundaries (Tier‑1 hubs, dependents).
3. **Only then** open paths under the cloned repos for deeper reads or edits.

Do **not** replace step 1–2 with ad‑hoc `find` / tree walks / “let me explore the Android app” through source when scan data exists and is fresh. If scan is missing or stale, run **`/scan <slug>`** (or refresh) before inventing filenames. The scan runner already walked the tree; the LLM’s job is to **route** from brain output, not rediscover structure from scratch.

## Subagent STOP

If you are a dispatched subagent (dev-implementer, spec-reviewer, code-quality-reviewer, dreamer):

<SUBAGENT-STOP>
Skip the bootstrap. You are isolated. Execute your task. Report your status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED.
</SUBAGENT-STOP>

## Skills Priority

Process skills first (intake, conductor), then implementation skills (council, eval).

## Four Subagents (Locked)

1. **dev-implementer** — Context-isolated builder. TDD. Self-reviews. Commits.
2. **spec-reviewer** — Skeptical adversary. Reads code. Verifies spec compliance.
3. **code-quality-reviewer** — Code quality, patterns, naming, test quality.
4. **dreamer** — Inline conflict resolution + retrospective scoring.

Everything else is skills.

## Checklist

Before responding to any user message:

- [ ] Checked if any skill applies (even at 1% probability)
- [ ] Process skills invoked before implementation skills
- [ ] Skill file read fresh — not relying on memory
- [ ] All applicable skills in requires chain satisfied before invoking target skill
- [ ] If subagent: bootstrap instructions ignored, task spec executed directly
- [ ] If user waived a skill: deviation documented and risks flagged
