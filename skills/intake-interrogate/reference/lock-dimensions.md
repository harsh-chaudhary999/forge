# Lock dimensions — Q1–Q9 reference

## Lock dimensions (Q1–Q9 reference — elicit in doubt order, not ritual order)

**Naming note:** **Q1–Q9** are **internal labels** for **which sections** must appear in `prd-locked.md` — *not* “you owe the user nine chat turns” and *not* “exactly eight plus design.” They exist so skills and reviewers can point at **specific lock dimensions**. The only “limit” is **document completeness**; conversation length is **unbounded above and below** (see **Confidence-first** Section 7).

The numbering below is a **checklist of fields** that must appear in `prd-locked.md` before council — **not** a promise to ask the user exactly eight (or any fixed number of) questions. **Order of conversation follows doubt severity**, not Q1→Q9 sequence, except where a later field depends on an earlier one (e.g. resolve **product** before **Q4** repos).

**Q1: Which product?**
"This PRD affects which product? (e.g., 'ShopApp', 'InvoicingPlatform')"
→ Look up the product in `~/forge/brain/products/<slug>/product.md` to validate it exists.
→ If not found, ask user to provide `forge-product.md` or register the product first.
→ **If high confidence:** PRD + metadata already name one registered product — pre-fill **Product:** and ask **confirm slug** only.

**Q2: What's the one-sentence goal?**
"In one sentence, what is this PRD trying to ship?"
→ Lock the answer.
→ **If high confidence:** PRD summary or title is one clear outcome — pre-fill **Goal:**, ask **confirm or tighten** one sentence.

**Q3: Success criteria?**
"How will you know this shipped successfully? (e.g., 'user can log in with 2FA', 'search returns results under 100ms')"
→ 2–3 criteria. Lock them.
→ **If high confidence:** Acceptance criteria section is already testable — map into **Success Criteria:** bullets and ask **confirm or add missing measurability** only.

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

**Q4b — Pipeline adjacency (ask when Q4 touches a “hero” or shared entity)**

When the PRD centers on an entity type that likely participates in **multiple product pipelines** (CRM / leads, acquisition feeds, verification, fraud or trust scoring, billing, messaging, regional compliance, alpha vs production paths — **use neutral names from the PRD**), add **`pipeline_adjacency_notes`** to `prd-locked.md` after this cluster (MCQ + free text is fine):

1. **Does this change touch or read state also used by other flows?** (yes / no / unknown)
2. If **yes** or **unknown**: list **which** adjacent pipelines (from PRD + `product.md` roles) and whether this task **reads**, **writes**, or **must explicitly avoid** each.
3. **Brain follow-up:** Point to **`docs/adjacency-and-cohorts.md`** for **`discovery-adjacency.md`** + **`touchpoints/`** artifacts before Council closes (**State 2.6** + council), unless **`adjacency_waiver`** with owner.

**Lock snippet (append to `prd-locked.md` when Q4b applies):**

```markdown
**pipeline_adjacency_notes:** (bullets: pipelines + R/W/exclude + confidence)
**adjacency_waiver:** no | yes (if yes: owner + reason)
```

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

**NEVER SKIP — explicit question (must appear in this intake thread):** In **at least one** assistant message after Q9 is in scope, you **must** include this **exact** blockquote (character-for-character), so implementers, humans, and logs prove the user saw it:

> **“What is the single design source of truth for implementers — exact file paths under the Forge brain, or Figma file key + root node IDs, or an explicit waiver to build only from PRD text?”**

**Allowed pattern when PRD is already clear:** same message may continue with “From your PRD we read: … — **confirm** or correct.” **Forbidden:** writing `design_intake_anchor` or closing intake **without** ever emitting the blockquote above in this thread. Do not substitute a vague “do you have a Figma link?” alone; the user must see **paths / keys / waiver** framed by this exact question.

**Question (one intake turn):** Deliver Q9 as **one message** that **starts with or contains** the **verbatim blockquote** above, then the bullets below (bundled prompt is the exception to “one bullet = one message” — still **wait** for a complete answer before locking). If any bullet is TBD, follow up until concrete.

"This PRD includes web or app work (or user-visible UI). I need an explicit lock on design.

[Include the verbatim blockquote line-for-line from **NEVER SKIP** above, then:]

1. **Is there net-new product or visual design work** for this slice (new screens, flows, or brand/visual changes), or is this **engineering-only / reuse** of existing UI patterns and copy?

2. **Design source of truth (follow-up to the blockquote):** Brain `design/` paths, **Lovable → GitHub** repo + branch/SHA (see **`lovable_github_repo`**), Figma key + node IDs for MCP, other exports in-repo, **or** explicit PRD-only waiver with owner + risk — not a wiki landing page alone.

3. If **no new design** but UI still changes: confirm **who owns layout/interaction decisions** during implementation (e.g. team lead, existing design system only).

4. **If Figma is authoritative:** Does your environment have **Figma MCP**? If yes, we will pull nodes by **file key + node id**; if no, we need **checked-in exports** or REST access — not a bare browser URL alone."

**Lock in `prd-locked.md` (concrete, no TBD when web/app in scope):**

- **`design_intake_anchor`:** One sentence — the user’s **exact** answer to **“single design source of truth”** (which paths, which Figma key+nodes, or PRD-only waiver with owner). **Required whenever Q9 is asked.** Proves the question was not skipped.
- `design_new_work:` **yes** | **no** (engineering-only / reuse existing patterns)
- `design_assets:` Human-readable pointers (Figma page links, Confluence, Slack) — **optional** for humans; these **do not** satisfy implementability alone.
- **Implementable design (HARD-GATE when `design_new_work: yes`):** You **must** lock **at least one** of the following before advancing to council:
  - **`design_brain_paths`:** Paths under `~/forge/brain/prds/<task-id>/design/` (e.g. exported PNG/SVG/PDF, `README.md` listing frames, MCP transcript saved as `.md`) — files agents can `Read` without chat context; **or**
  - **`lovable_github_repo`** (`owner/repo`) + optional **`lovable_path_prefix`** (subfolder in a monorepo) + **pinned branch/tag/commit** (in the PRD or `design/LOVABLE_SYNC.md`) — [Lovable](https://lovable.dev) UI synced to GitHub so agents read **source files**, not only a builder URL; see **`docs/platforms/lovable.md`**; **or**
  - **`figma_file_key`** + **`figma_root_node_ids`** (comma-separated node ids) — so implementers can use **Figma MCP** or REST to fetch structure; **or**
  - **`design_waiver: prd_only`** — stakeholder **owner name** + **one-line risk** explicitly accepting implementation from PRD prose only with no pixel parity gate.
- When `design_new_work: no` or PRD-only UI: set **`design_assets: none`** and omit figma fields unless you still want a file key for optional reference.

**INSUFFICIENT to lock when `design_new_work: yes` (treat as TBD — keep asking):**

- Only a **Confluence / wiki / Google Doc URL** with no files under `~/forge/brain/.../design/` and no `figma_file_key` + `figma_root_node_ids`.
- Only a **bare Figma share URL** with no **file key + node id(s)** and no exports under brain or repo paths agents can read.
- Only a **Lovable project URL** with **no** **`lovable_github_repo`** (or equivalent registry path) **and** no **`design_brain_paths`** agents can read.
- “Design is in Figma / we’ll export before build” with **no** committed path and **no** waiver.

**If Figma URL exists but implementability uses MCP or REST:** Still record **`figma_file_key`** and **`figma_root_node_ids`** in `prd-locked.md` (parse from URL when possible). Tell the user to place exports under `~/forge/brain/prds/<task-id>/design/` **before council** if MCP will not be used in-session.

**You may not lock the PRD** while web/app are in scope and Q9 fields above are missing, **TBD**, or vague ("we'll see in implementation"). **`design_new_work: yes` without implementable design + without `design_waiver: prd_only` is a blocked lock.** **No Figma is fine** when the explicit choice is **engineering-only / PRD-only / waived** with the fields above.

**Q10: Implementation closure — VCS reference, delivery boundary, stack (mandatory when gate applies)**

**Purpose:** When several **equally plausible** implementations could satisfy the prose PRD, closure records **which** path is authoritative so council, tech plans, tests, and eval do not diverge.

**When Q10 is mandatory (HARD-GATE):** Lock Q10 **before council** if **any** of:

1. **Q4** lists **more than one** affected repo, **or**
2. **Q9 applies** (web / app / user-visible UI), **or**
3. The PRD allows **multiple channels or boundaries** (e.g. config vs service vs client; “reuse existing”, “toggle”, “rollout”, “dual path”, major/minor version split) **without** already naming the canonical one, **or**
4. Naming, scope, or initiative wording suggests work might **already exist** on another branch, tag, or open change request in the listed repos.

**Only skip Q10** when the change is **narrowly unambiguous** (single repo, single obvious integration point, behavior fully specified with no channel fork). Then record **`implementation_closure: not applicable`** plus **one line** why (e.g. “single-table migration; no alternate delivery path”).

**Lock in `prd-locked.md` (concrete; no `TBD` when gate applies):**

- **`implementation_reference`:** `branch:<ref>` **|** `tag:<ref>` **|** `pr:<url>` **|** `issue:<key>` **|** `none` — plus **one sentence**. Use `none` only with explicit acknowledgment that implementation proceeds **without** diffing prior VCS work (greenfield path).
- **`delivery_mechanism`:** **Exactly one** authoritative **system boundary or channel** where acceptance behavior is enforced (e.g. “REST handlers in service S”, “batch worker + outbox”, “file-backed operator config”, “browser client bundle only”). Add a **second line** when parallel paths can coexist during rollout (compat window, feature flag scope, deprecation).
- **`implementation_stack`:** For **each** repo role in Q4 that this task touches, a **short concrete** note: modules, frameworks, or reuse targets **or** `n/a (headless-only)` where no presentation layer exists. **Legacy alias:** some locks may still use **`ui_implementation_stack`** — same slot; new locks should prefer **`implementation_stack`**.

**INSUFFICIENT to lock when Q10 applies:**

- External doc / ticket link as the only narrative **without** an `implementation_reference` decision when item **(4)** could apply.
- **`delivery_mechanism: TBD`**, **`implementation_stack: implementer’s choice`**, or **“decide in tech plan”** — delegates the fork to implementation time.
