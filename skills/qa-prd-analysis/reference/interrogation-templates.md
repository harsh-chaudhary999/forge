# qa-prd-analysis — Q1–Q8 interrogation templates

Run these as **sequential** turns (one dimension per assistant message), each with its
full fenced menu, brain-informed ☑/○. See the skill's Step 0.5 HARD-GATEs for the
dialogue rules; use `AskUserQuestion` for discrete shortcuts only *after* the full
checklist is visible.

## Q1 — Test Types (mandatory)

Ask as the **first** interrogation turn after Step 0 (after optional one-line context). **Only** Q1 content in that turn — then **wait**. **HARD-GATE — No dual prompt with prerequisites:** If **`prd-locked`** / **task-id** still need a **blocking** human confirm, that confirm is **its own** preceding turn — **do not** combine that **`AskUserQuestion`** with **Q1** in the **same** assistant message (markdown **Q1** + a separate widget **≠** one turn).

**HARD-GATE — Full checklist visible:** Paste the **complete** fenced menu below (Functional → Accessibility) with brain-informed ☑/○ — **every row the skill lists**. **Forbidden:** replacing Q1 with **only** prose plus **Full / Lean CI / Custom** (or similar) **without** the full structured list above it — users cannot consent to types they cannot see. **Allowed:** **after** the full menu, add optional shortcuts (*e.g.* "Reply **All recommended**, **Lean CI**, or line-by-line yes/no") **below** the fence — shortcuts may **not** substitute for the checklist.

Show the menu with brain-informed recommendations:

```
Which test types do you want for this QA run?
[Based on reading the PRD + tech plans, I recommend: ✓ items below]

Functional Testing
  ☑ Positive / Happy Path     — valid inputs, expected success flows
  ☑ Negative                  — invalid inputs, error handling, rejections
  ☑ Boundary Value Analysis   — at and around input limits (min, max, min±1, max±1)
  ☑ Equivalence Partitioning  — representative values per input class
  ☑ Edge Cases                — unusual-but-valid inputs, empty states, concurrency

Non-Functional Testing
  ☑ Smoke                     — critical path quick sanity (run first, fast)
  ☑ Regression                — verify existing behavior not broken by this change
  ○ Performance / SLA         — response times against SLA thresholds [recommend if SLA in spec]
  ○ Compatibility             — cross-browser, device sizes, OS versions [recommend if multi-platform]

Security Testing (OWASP Top 10 for this surface)
  ☑ Authentication / AuthZ    — login bypass, privilege escalation, session fixation
  ☑ Input Validation          — SQLi, XSS, path traversal in all input fields
  ○ Sensitive Data Exposure   — tokens in logs, unmasked fields, insecure storage [recommend if PII]
  ○ Rate Limiting / DoS       — brute force, request flooding protection [recommend if auth surface]

Accessibility (WCAG 2.1 AA)
  ○ Keyboard Navigation       — all flows reachable without mouse
  ○ Screen Reader             — ARIA labels, landmark roles, focus management
  ○ Color Contrast            — 4.5:1 for normal text, 3:1 for large text
  ○ Focus Indicators          — visible focus ring on all interactive elements

Select all that apply. Mark ○ items as yes/no. Or type "all" for maximum coverage.
```

Adjust the pre-checked (☑) items based on what the PRD actually contains. Pre-check an item if the PRD or tech plans have clear scope for it. Leave ○ if absent from PRD unless it is always required (positive, negative, edge case are always required).

## Q2 — Surfaces (mandatory)

Show only surfaces that exist in `forge-product.md` for this product:

```
Which surfaces should scenarios be generated for?
[Surfaces registered in forge-product.md for <slug>:]

  ☑ Web ({{ web-dashboard repo }}) — browser via Chrome DevTools Protocol
  ☑ API ({{ backend-api repo }})   — REST/GraphQL via HTTP driver
  ○ Android ({{ app-mobile repo }}) — ADB + UIAutomator / Appium MCP
  ○ iOS ({{ app-mobile repo }})     — XCTest / Appium MCP
  ☑ Database (MySQL/Postgres)       — schema and data integrity checks
  ○ Cache (Redis)                   — key presence, TTL, invalidation
  ○ Event Bus (Kafka)               — event publish/consume verification
  ○ Search (Elasticsearch)          — index update, query result checks

Pre-checked surfaces appear in both the PRD and forge-product.md.
Answer: which surfaces should have scenarios generated? (or "all")
```

> **D5 note (Android/iOS):** the *driver implementation* for mobile (Appium MCP vs
> ADB+UIAutomator / XCTest) is a CLAUDE.md **D5** choice — it is **deferred to the
> driver skills** and must be asked of the human and recorded in the task brain there,
> not silently assumed here. Q2 only decides whether a surface is *in scope*.

## Q3 — Coverage Depth

```
Coverage depth for this run?

  A) Smoke only       — critical path, fast (10–20 scenarios total)
  B) Standard         — happy + negative + boundary per feature (50–100+ scenarios)
  C) Comprehensive    — all types selected in Q1, maximum coverage, no gaps
                        (100–300+ scenarios depending on PRD size)

[Recommended: C — Comprehensive, based on <reason from PRD e.g. "payment feature with PII"]
```

## Q4 — Feature Priority

Based on the PRD sections read, list the top feature areas and ask:

```
Which feature areas need the highest test density?
[From PRD, I identified these feature areas:]

  1. Authentication (login/logout/session)
  2. Payment checkout flow
  3. Order management
  4. User profile / settings
  5. Admin dashboard

Mark priority: High / Medium / Low per area, or "all high".
High = maximum scenario count. Medium = standard. Low = smoke only.
```

## Q5 — Regression Scope

```
For regression testing, which existing functionality must not break?
[From codebase scan, I see these Tier 1 architectural hubs that touch this feature:]
  - auth.service.ts (referenced by 12 modules)
  - payment.service.ts (referenced by 8 modules)
  - user.repository.ts (referenced by 9 modules)

List any additional areas to regression-test, or confirm the above is complete.
```

Only ask this if codebase scan is present. If absent, ask: "List any existing flows that must not break with this change."

## Q6 — Open Ambiguities

Based on PRD reading, list every ambiguity found:

```
I found the following open questions in the PRD. Answer each:

  1. [<specific ambiguity from PRD, e.g. "PRD says 'validate email' but doesn't specify the format rule">]
  2. [<specific ambiguity, e.g. "SLA not specified for checkout API — what is the P95 target?">]
  3. [<specific ambiguity, e.g. "Error message for duplicate email: what exact text?">]
  ...

Answer each, or mark as 'accept risk' with your name.
```

Generate this list entirely from the PRD read in Step 0 — do not ask generic questions like "any edge cases I should know about?" that the user must answer from scratch. You read the PRD — find the gaps yourself.

## Q7 — Environment and Data

```
Test environment details (I'll use these to write concrete test data into scenarios):

  a) Test user credentials format? (e.g. qa+{n}@example.com / password format)
  b) Test data state: seeded DB or agent creates data during the test?
  c) Any third-party services to stub/mock? (e.g. payment gateway, SMS OTP)
  d) Known flaky areas or test isolation issues to work around?
```

## Q8 — Design source of truth & PRD → UI mapping (mandatory if Web, Android, or iOS is in scope)

**Skip only if** confirmed surfaces are exclusively API/DB/cache/events/search with **no** user-visible UI for this feature — state **N/A** in chat and in `qa-analysis.md`.

**Reuse-first (do this before the full questionnaire):** If **planning / development already produced** PRD↔UI traceability — e.g. **tech plans** with screens and testids, **`shared-dev-spec.md`** user-visible behaviors, **`prd-locked.md`** design/Q9 fields, **`design/MCP_INGEST.md`** or Figma refs — then **Q8 is not a greenfield mapping exercise**. You **summarize what exists** (brain paths + section titles), list **only gaps** (missing component for a PRD bullet, unknown fixture, conflicting testid), and elicit **confirm or patch** for those gaps with `AskUserQuestion` when the gap is a **discrete** choice. Paste this **short form** in chat when reuse applies:

```
Q8 — Inherited PRD ↔ design mapping (confirm / gap-fill)

Already documented (read in Step 0):
  - <path#heading> — what it covers
  - ...

For QA test authoring, confirm:
  (A) Accurate as-is — proceed to cases using citations above
  (B) Needs updates — list only deltas: <gap 1>, <gap 2>, ...

If (B): answer only the gaps (authoritative source, testid, fixture, E2E order).
```

**Full Q8 workshop** — use **only** when no adequate mapping exists in brain artifacts, or after **(B)** to capture **remaining** items:

```
Design & UI (maps PRD language to what testers assert on screen):

  a) **Authoritative design source** — Figma file/key + node(s), and/or paths under brain/prds/<task-id>/design/ (e.g. MCP_INGEST.md), Lovable GitHub repo + pinned ref (lovable_github_repo, see design/LOVABLE_SYNC.md) — which wins when they disagree?
  b) **For each major PRD user-visible requirement** (e.g. "blacklisted banner after login", "Step 1 tab", "restricted crawl"): name the **screen or component**, **data-testid** or accessibility label if known, and **preconditions** (account state, tier, due date, feature flag).
  c) **End-to-end flow** — ordered steps from entry (e.g. login) through the assertion (e.g. banner visible on home), including **where** copy/layout must match design vs PRD prose only.
  d) **Fixtures** — which seeded users / tokens / DB rows are required so the UI can reach each state (blacklisted, overdue, L2 only, etc.)?

If Figma MCP or design files are unavailable: record **CONTEXT_GAP** and the minimum **user-supplied** screenshots or testids needed before writing UI automation rows or manual web rows.
```

---

**Wait until every dimension** for Q1–Q7 (+ Q8 when UI in scope) is **resolved or explicitly risk-accepted**, using **sequential turns** and **adaptive skips/substitutions**, before proceeding to Step 1. After **each** reply, reconcile; chase **new doubts** before advancing the default Q sequence.

Record all Q&A verbatim in the output artifact (including *skipped — subsumed by …*). Do not proceed on partial answers — ask again for any unanswered item. There is no upper limit on **tailored** follow-up questions: **zero ambiguities** is the stop condition, not "asked Q8 verbatim."
