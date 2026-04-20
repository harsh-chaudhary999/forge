---
name: intake-interrogate
description: "WHEN: You've been given a PRD for a multi-repo product and need to lock scope, success criteria, and contracts. Asks 8 core questions one at a time; Q4 forces product.md↔PRD audience cross-check (no false-confidence repo picks); Q9 (design / UI change class + implementable design assets) is mandatory when web or app work is in scope."
type: rigid
requires: [brain-write]
---

# Intake Interrogation — PRD Lock

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I can infer this from context" | You cannot. The biggest projects fail because teams assume they agree on a spec and discover otherwise in code review. Intake enforces lock. No exceptions. |
| "This question is obviously answered by the PRD" | PRDs describe intent, not decisions. Intake extracts explicit, locked answers — not interpretations of intent. Ambiguous PRDs become arguments in code review. |
| "Asking all intake questions takes too long" | Skipping intake questions takes longer — each unanswered question becomes an assumption that fails during implementation or eval. |
| "The user said TBD, that's fine for now" | TBD answers cannot be locked. A PRD with TBD success criteria cannot be evaluated. Push for specifics or block the PRD until resolved. |
| "I'll ask multiple questions at once to save time" | Multi-question dumps produce short, shallow answers. One question at a time forces thought and produces lockable answers. |
| "Only one repo in `product.md` matches a signal (sole web app, sole API service, sole worker, …), so that must be the repo" | **Cardinality ≠ correctness.** Picking the only backend / only frontend / only mobile entry because it is unique is **registry guessing**, not a validated lock. STOP. Cross-check PRD audience and semantics against **`role:`** and **`repo:`** path; surface mismatches; use explicit list + `product.md` fix or human confirmation. |
| "I'll phrase option A as the narrowest scope so it looks like the right pick" | Narrowest ≠ correct. MCQ **order** and **only** wording bias humans and models toward A. STOP. When **PRD audience or surface** (who uses it: customer, partner, admin, internal, …) **conflicts** with a **project `role` name** or parent path segment, **do not** present a single-repo “100% confident” option — lead with **escalation / Other**. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
Q1–Q8 MUST ALWAYS BE ANSWERED WITH CONCRETE, LOCKED ANSWERS BEFORE THE PRD ADVANCES TO COUNCIL.
WHEN WEB OR MOBILE APP WORK IS IN SCOPE (SEE Q9), Q9 IS ALSO MANDATORY — SAME BAR AS Q1–Q8 (NO TBD, NO “SKIP”).
WHEN Q9 APPLIES, THE AGENT MUST ASK THE SINGLE DESIGN SOURCE OF TRUTH QUESTION AND RECORD design_intake_anchor — NEVER SKIP OR INFER.
A TBD ANSWER IS NO ANSWER. PARTIAL INTAKE IS NO INTAKE.
```

## HARD-GATE

Do not skip intake. Every PRD goes through this. No matter how simple it seems.

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Any question is answered with "TBD" or "we'll figure it out later"** — Unanswered questions become undiscovered requirements. STOP. Get the answer now or the PRD cannot be locked.
- **Agent fires multiple questions in a single message** — Simultaneous questions produce short answers. STOP. One question at a time, always.
- **Product slug is not found in `~/forge/brain/products/`** — PRD references an unregistered product. STOP. Register the product or ask the user to provide forge-product.md before proceeding.
- **Success criteria is stated in vague terms ("fast", "good UX", "reliable")** — Unmeasurable criteria cannot be evaluated. STOP. Get specific, testable criteria (e.g., "< 200ms p99 latency") before locking.
- **Rollback plan is "just redeploy the old version"** — Not a real rollback plan for schema changes, cache migrations, or event stream additions. STOP. Get a concrete rollback procedure.
- **User skips a question saying "that's not relevant"** — Every question was added because of a real project failure. STOP. Ask the question anyway; the user decides what's in scope, not which questions get asked.
- **PRD touches web or app but Q9 (design / UI change class) was not asked, was skipped, or is TBD** — Surfaces without an explicit design decision ship on hidden assumptions. STOP. Ask Q9 and lock an answer (including **no new design work** or **engineering-only UI**) before PRD lock.
- **`design_new_work: yes` but design is not machine-implementable** — A wiki/Confluence link, bare Figma share URL, or “we’ll export later” is not a durable transport layer for council or subagents. STOP. Require **implementable design** per Q9 rules (brain `design/` paths, or `figma_file_key` + `figma_root_node_ids`, or an explicit **`design_waiver`** with owner + risk). Do not lock until one of those is true.
- **User-visible or design-related work without asking “design source of truth” out loud** — If Q9 applies (see **When to ask** below) or the PRD reads like UI/design work, you **must** ask the explicit question: **“What is the single design source of truth for implementers?”** and capture the answer in `prd-locked.md`. **Never infer** from links in chat, **never skip** because “Figma was mentioned earlier,” **never assume** engineering-only without the user saying so. Silent skip = blocked intake.
- **Q4 repo choice without `repo_registry_confidence` + naming check** — You invented certainty. STOP. Reread `product.md` project **`role:`** names and **`repo:`** path segments against the PRD’s **stated audience and surface** (who/what the change is for). If they **diverge**, you must **not** lock “minimal MCQ” alone — record **`repo_naming_mismatch_notes`** and **`product_md_update_required`** or get human sign-off.
- **PRD is locked without brain-write recording the decision** — The lock exists only in chat context and will be lost. STOP. Write to brain before calling PRD locked.

## Process

1. **One question at a time** — ask, wait for answer, move to next. No multi-question dumps.
2. **Multiple-choice preferred** — easier to answer than open-ended.
3. **Lock answers** — write each to `prd-locked.md` as you go.
4. **Converge on consensus** — get the answer in the user's own words, write it back, confirm.

## Questions (in order)

**Q1: Which product?**
"This PRD affects which product? (e.g., 'ShopApp', 'InvoicingPlatform')"
→ Look up the product in `~/forge/brain/products/<slug>/product.md` to validate it exists.
→ If not found, ask user to provide `forge-product.md` or register the product first.

**Q2: What's the one-sentence goal?**
"In one sentence, what is this PRD trying to ship?"
→ Lock the answer.

**Q3: Success criteria?**
"How will you know this shipped successfully? (e.g., 'user can log in with 2FA', 'search returns results under 100ms')"
→ 2–3 criteria. Lock them.

**Q4: Which repos will change? (product topology — no false confidence)**

**Before you ask the user (agent MUST do this silently):**

1. Read `~/forge/brain/products/<slug>/product.md` and list every **`### <heading>`** and each project's **`- role:`** value — these are the **only** legal repo identifiers for MCQ options.
2. Extract from the PRD **explicit audience / surface / actor** (who or what the change serves: end customer, merchant, partner, admin, platform team, device class, region, …) — use **neutral** vocabulary; do not assume any vendor’s domain dictionary.
3. **Cross-check:** For each candidate repo, ask: *Would a new engineer, reading **only** the `role` name and the **`repo:`** path (parent folders, basename), believe this project matches the PRD’s audience and surface?*  
   - If the PRD implies one audience (e.g. **consumer-facing**) but the **only** registered web (or app, or API) **`role`** / path suggests **another** (e.g. **admin**, **partner**, **internal**), treat that as **HIGH RISK — naming or registry mismatch**. **Do not** recommend “that repo only” as the **first** or **sole** confident MCQ option.
4. **Never** justify a repo pick with “it is the only **X** in `product.md`” where **X** is mobile, web, backend, worker, etc. That is **mechanical cardinality**, not product truth.

**How to ask Q4:**

- Prefer **open list first**: “Which **`role` names** from `product.md` will change? (2–5). If unsure, say unsure.”
- If you use **multiple choice**, every option must be **honestly scoped**:
  - **Do not** put a **single** repo as **option A** when step 3 found a **naming/audience tension** — put **“Other / registry review”** first or make **D) Other** the **recommended** path until the user confirms.
  - Add one line of **epistemic humility** in the prompt: *“If the PRD audience does not match any `role` name, answer **Other** and we will fix `product.md` before council.”*
- If no registered repo clearly matches the PRD surface, **STOP** and say so: *“No `product.md` project matches [audience]. Add/register the correct repo or rename roles before locking Q4.”*

**Lock in `prd-locked.md` immediately after Q4 (always include these three lines):**

```markdown
**Repos Affected:** (role names from product.md, 2–5)
**repo_registry_confidence:** high | medium | low
**repo_naming_mismatch_notes:** (none) | (bullets: e.g. “PRD implies consumer UI; only registered web role is `admin-console` — confirm or add repo”)
**product_md_update_required:** no | yes (if yes, link or describe what to add/fix before council)
```

**SUCCESS:** User confirms repo list **or** explicitly accepts risk after reading mismatch notes.  
**FAILURE:** You locked Q4 with a **letter-only** answer and **no** `repo_registry_confidence` / mismatch notes — that is incomplete intake.

**Q5: Any contract changes?**
"Will this PRD require changes to any contracts? (API endpoints, DB schema, event schemas, cache keys, search indexes)"
→ Examples: "REST API v2 migration", "Add Order event to Kafka", "New MySQL table"
→ Lock the contracts affected.

**Q6: What's the timeline?**
"When does this need to ship? (e.g., 'by EOW', 'no hard deadline')"
→ Lock the date or note "no hard deadline".

**Q7: Rollback plan?**
"If this breaks prod, how do we roll it back? (e.g., 'API v1 is still live', 'DB migration is backward-compat')"
→ Lock the rollback strategy.

**Q8: Success metrics?**
"How will you measure if this succeeded post-launch? (e.g., 'login rate > 90%', 'search latency < 500ms')"
→ Lock the metrics.

**Q9: Design & UI change class (mandatory when web or app is in scope)**

**When to ask (HARD-GATE):** Ask Q9 **before locking** if **any** of the following is true:

1. **Q4** lists any repo or surface that is clearly **web** or **mobile app** (e.g. `web-*`, `app-*`, `*-dashboard`, `*-mobile`), **or**
2. The PRD text (title, body, acceptance criteria) describes **user-visible** changes: screens, pages, layouts, navigation, widgets, dashboards, modals, **spacing/typography/color**, icons, illustrations, animations, **“UI”**, **“UX”**, mockups, **Figma**, Zeplin, screenshots, “pixel-perfect”, “match design”, **visual** parity, onboarding flow, empty states, **or**
3. The user or PRD says the work is **design-related** or **front-end visible** even if Q4 looked backend-heavy.

**Only skip Q9** when the PRD is **backend/infra only** (no web or app in Q4 **and** no UI/design signals in the PRD text). Then note `design_ui_scope: not applicable` and **`design_intake_anchor: not applicable (backend-only / no user-visible UI)`** in `prd-locked.md`.

**NEVER SKIP — explicit question (audible in transcript):** In the Q9 turn you **must** include this sentence verbatim (so implementers and logs prove it was asked):

> **“What is the single design source of truth for implementers — exact file paths under the Forge brain, or Figma file key + root node IDs, or an explicit waiver to build only from PRD text?”**

Do not substitute a vague “do you have a Figma link?” alone; the user must choose **paths / keys / waiver**.

**Question (one intake turn):** Deliver Q9 as **one message** with the bullets below (bundled prompt is the exception to “one bullet = one message” — still **wait** for a complete answer before locking). If any bullet is TBD, follow up until concrete.

"This PRD includes web or app work (or user-visible UI). I need an explicit lock on design:

1. **Is there net-new product or visual design work** for this slice (new screens, flows, or brand/visual changes), or is this **engineering-only / reuse** of existing UI patterns and copy?

2. **Design source of truth (mandatory):** What is the **single** source of truth for implementers? (Brain `design/` paths, Figma key + node IDs for MCP, exports in-repo, **or** explicit PRD-only waiver with owner + risk — not a wiki landing page alone.)

3. If **no new design** but UI still changes: confirm **who owns layout/interaction decisions** during implementation (e.g. team lead, existing design system only).

4. **If Figma is authoritative:** Does your environment have **Figma MCP** (e.g. Cursor)? If yes, we will pull nodes by **file key + node id**; if no, we need **checked-in exports** or REST access — not a bare browser URL alone."

**Lock in `prd-locked.md` (concrete, no TBD when web/app in scope):**

- **`design_intake_anchor`:** One sentence — the user’s **exact** answer to **“single design source of truth”** (which paths, which Figma key+nodes, or PRD-only waiver with owner). **Required whenever Q9 is asked.** Proves the question was not skipped.
- `design_new_work:` **yes** | **no** (engineering-only / reuse existing patterns)
- `design_assets:` Human-readable pointers (Figma page links, Confluence, Slack) — **optional** for humans; these **do not** satisfy implementability alone.
- **Implementable design (HARD-GATE when `design_new_work: yes`):** You **must** lock **at least one** of the following before advancing to council:
  - **`design_brain_paths`:** Paths under `~/forge/brain/prds/<task-id>/design/` (e.g. exported PNG/SVG/PDF, `README.md` listing frames, MCP transcript saved as `.md`) — files agents can `Read` without chat context; **or**
  - **`figma_file_key`** + **`figma_root_node_ids`** (comma-separated node ids) — so implementers can use **Figma MCP** or REST to fetch structure; **or**
  - **`design_waiver: prd_only`** — stakeholder **owner name** + **one-line risk** explicitly accepting implementation from PRD prose only with no pixel parity gate.
- When `design_new_work: no` or PRD-only UI: set **`design_assets: none`** and omit figma fields unless you still want a file key for optional reference.

**INSUFFICIENT to lock when `design_new_work: yes` (treat as TBD — keep asking):**

- Only a **Confluence / wiki / Google Doc URL** with no files under `~/forge/brain/.../design/` and no `figma_file_key` + `figma_root_node_ids`.
- Only a **bare Figma share URL** with no **file key + node id(s)** and no exports under brain or repo paths agents can read.
- “Design is in Figma / we’ll export before build” with **no** committed path and **no** waiver.

**If Figma URL exists but implementability uses MCP or REST:** Still record **`figma_file_key`** and **`figma_root_node_ids`** in `prd-locked.md` (parse from URL when possible). Tell the user to place exports under `~/forge/brain/prds/<task-id>/design/` **before council** if MCP will not be used in-session.

**You may not lock the PRD** while web/app are in scope and Q9 fields above are missing, **TBD**, or vague ("we'll see in implementation"). **`design_new_work: yes` without implementable design + without `design_waiver: prd_only` is a blocked lock.** **No Figma is fine** when the explicit choice is **engineering-only / PRD-only / waived** with the fields above.

## Output

Write all answers to `~/forge/brain/prds/<task-id>/prd-locked.md`:

```markdown
# PRD Locked

**Product:** ShopApp  
**Goal:** Users can log in with two-factor authentication.  
**Success Criteria:**
- Users can enable 2FA in settings
- Login requires 2FA code if enabled
- 2FA code delivered via SMS in < 5 seconds

**Repos Affected:**
- backend-api
- web-dashboard
- app-mobile

**repo_registry_confidence:** medium
**repo_naming_mismatch_notes:** (none)
**product_md_update_required:** no

**Contracts Affected:**
- REST: Add POST /auth/2fa/enable, POST /auth/2fa/verify
- MySQL: Add user_2fa_enabled bool, user_2fa_secret string
- Redis: 2fa_codes key for temp storage, 5min TTL

**Timeline:** EOW  
**Rollback:** API v1 is still live, 2FA is optional, no DB breaking changes.  
**Success Metrics:** 2FA adoption > 50% within 2 weeks.

**Design / UI (Q9 — include when web or app in scope):**
- **design_intake_anchor:** User stated: build login from existing design system only; no new Figma.
- **design_new_work:** no (reuse existing auth patterns)
- **design_assets:** none (PRD describes screens; no Figma)
- **design_brain_paths:** (omit — not net-new design)
- **figma_file_key:** (omit)
- **figma_root_node_ids:** (omit)
- **design_waiver:** (omit unless used)

---

**Locked by:** [Claude]  
**Date:** 2026-04-08  
**Ready for:** Council reasoning
```

## Edge Cases & Fallback Paths

### Edge Case 1: User answers are contradictory (Q2 vs Q3, or Q5 vs Q7)

**Diagnosis**: User says goal is "Add 2FA" (Q2), but success criteria is "Users can log in without 2FA" (Q3). Or contracts affected are "Add DB table" but rollback plan is "No breaking changes".

**Response**:
- **Detect**: Flag the contradiction explicitly.
- **Read back**: "I hear you want [Q2 answer] but success looks like [Q3 answer]. These seem incompatible. Can you clarify which one is correct?"
- **Wait for clarification**: Don't write to `prd-locked.md` until contradiction is resolved.
- **Reword**: Once clarified, rewrite both answers to be consistent.
- **Document**: Note in prd-locked.md: "Clarification required on [question]. Original answers were contradictory; locked version reflects [final answer]."

**Escalation**: If user cannot resolve contradiction (e.g., "I don't know, let me ask stakeholders"), escalate to NEEDS_CONTEXT. Pause intake until user returns with clarified answers.

---

### Edge Case 2: PRD changes during intake (scope expands mid-interrogation)

**Diagnosis**: While answering Q3 (success criteria), user adds three new requirements that weren't in the original PRD. "Actually, we also need..." scope creep.

**Response**:
- **Detect**: Flag the scope expansion.
- **Clarify**: "Original PRD scope was [original list]. You've now added [new items]. Is this still one task, or should we split into two?"
- **Options**:
  1. **Accept scope expansion**: Revise answers. Document what changed and why.
  2. **Defer new items**: "Let's ship original scope. New items become a separate PRD."
- **Decision**: User chooses. Write final answers to prd-locked.md with note about scope decision.

**Escalation**: If scope expands significantly (e.g., goes from 1 repo to 5 repos), escalate to user: "Scope has tripled. Recommend: split into two PRDs. Proceed with Phase 1 only?"

---

### Edge Case 3: Eight questions reveal infeasibility (Q4 + Q5 + timeline = impossible)

**Diagnosis**: During Q4-Q6, you realize: repos needed are not owned by team, contracts required are incompatible with existing code, and timeline is 1 week. Task is infeasible.

**Response**:
- **Escalate early**: "I've locked answers to Q4-Q6. Based on this, the task appears infeasible: [specific blockers]. Recommend: discuss with stakeholders before council."
- **Don't force lock**: If you have genuine concerns about feasibility, report them.
- **Escalation paths**:
  1. User acknowledges infeasibility, task is canceled or descoped.
  2. User says constraints can be changed (e.g., timeline extended, repos reassigned), revise answers.
  3. User insists on proceeding despite concerns, lock as-is with escalation note.

**Escalation**: NEEDS_CONTEXT - Feasibility concern raised. User must decide: proceed, descope, or reschedule.

---

### Edge Case 4: Product doesn't exist in brain (Q1 lookup fails)

**Diagnosis**: User says PRD affects "AlphaProduct", but `~/forge/brain/products/alpha-product/` doesn't exist.

**Response**:
- **Ask**: "Product 'AlphaProduct' not found in brain. Do you have a `forge-product.md` for this? If not, we need to register it first."
- **Options**:
  1. **User provides product file**: Import it. Validate repos and surfaces are defined.
  2. **User says "I'll register it later"**: Cannot proceed. Intake requires valid product. Escalate.
  3. **User wants to continue anyway**: Document risk in prd-locked.md: "Product not registered. Proceeding with unvalidated product definition."

**Escalation**: BLOCKED - Cannot lock PRD without validating product exists. Route to product registration or ask user to provide product.md.

---

### Edge Case 5: User cannot identify affected contracts (Q5)

**Diagnosis**: User says "I don't know if this affects contracts" or "Maybe? Not sure". No clear contracts identified.

**Response**:
- **Clarify**: "Contracts include: REST API changes, database schema changes, event schemas, cache keys, search indexes. Does this PRD touch any of those?"
- **Guiding questions**:
  - "Will this PRD create new endpoints or modify existing ones?" → Contract: REST API
  - "Will this PRD add/modify database tables or columns?" → Contract: MySQL schema
  - "Will this PRD publish or consume events?" → Contract: Event schema
  - "Will this PRD use cache or change cache patterns?" → Contract: Cache keys
- **If still unclear**: Lock as "Contracts: TBD - to be determined during council reasoning". Escalate to council to investigate.

**Escalation**: If contracts truly cannot be identified, proceed with "TBD" in lock. Council will discover them during reasoning.

---

### Edge Case 6: Timeline is vague ("ASAP", "no hard deadline", or conflicting urgencies)

**Diagnosis**: User says "ASAP" but also "no hard deadline". Or says "ship by EOW" but also "low priority".

**Response**:
- **Push for clarity**: "I need a specific date or clear relative priority. Is this EOD? EOW? Next month? Or is timing flexible?"
- **Lock specific date**: "Let's lock this as: [specific date] OR [no deadline, low priority]."
- **Document assumptions**: Note in prd-locked.md: "Timeline: EOW (March 15). If date slips, impacts [downstream work/no impact]."

**Escalation**: If user cannot commit to a timeline, lock as "No hard deadline" and note that this affects prioritization against other work.

---

## Commit

After locking all **mandatory** questions (Q1–Q8 always; **Q9 when web or app is in scope**), commit the prd-locked.md:

```bash
git -C ~/forge/brain add prds/<task-id>/prd-locked.md
git -C ~/forge/brain commit -m "intake: lock PRD for <task-id>"
```

Next: Council reasoning to negotiate contracts across surfaces.

## Checklist

Before claiming intake complete:

- [ ] Q1–Q8 answered (no TBD, no skipped, no "we'll figure it out")
- [ ] **Q4 registry lock:** `repo_registry_confidence`, `repo_naming_mismatch_notes`, `product_md_update_required` present in `prd-locked.md` alongside **Repos Affected** (no letter-only MCQ without these)
- [ ] **Q9 answered when web or app is in scope** — `design_new_work` + `design_assets` (or `design_ui_scope: not applicable` documented when Q9 skipped)
- [ ] **If `design_new_work: yes`:** `design_brain_paths` **or** (`figma_file_key` + `figma_root_node_ids`) **or** `design_waiver: prd_only` with owner + risk — not URL-only
- [ ] **If Q9 was in scope:** `design_intake_anchor` line present (verbatim answer to single design source of truth)
- [ ] Each answer confirmed in the user's own words and written back for approval
- [ ] Contradictions between answers detected and resolved before locking
- [ ] prd-locked.md written to `~/forge/brain/prds/<task-id>/` and committed to brain
- [ ] Success criteria are measurable and testable (not behavioral descriptions)
- [ ] Rollback plan is concrete (not "revert the commit")
