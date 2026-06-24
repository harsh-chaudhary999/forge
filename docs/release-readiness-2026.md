# Forge — Release Readiness & June-2026 Roadmap

Status date: 2026-06-23. This is a planning artifact, not a skill or contract. It
combines (a) the repo audit from the skill-compliance sweep and (b) a June-2026 web
research pass on the agent/LLM landscape. Each item lists **what / where / how**.

---

## TL;DR

Forge's **skill layer** is in good shape (all 85 skills ≤400 lines, standard + lint
pass, 0 broken markdown links, 5 cohorts bug-audited). It is **not** release-ready:
no end-to-end functional proof, ~half the skills never got a correctness audit, CI
does not enforce any of the compliance just achieved, there is no `LICENSE`, and 84
stray self-symlinks are committed. Separately, the June-2026 landscape has moved —
MCP, native goals/memory, OTel GenAI semconv, computer-use, and a crowded
spec-driven-dev competitor field (BMAD at ~47k stars) all have concrete implications.

---

## Progress log (2026-06-23)

- **A1 CI skills-guard** — DONE (`47e3ee3`): enforces standard + lint + no-drift + ≤400 + 0 broken links + no symlinks.
- **A2 LICENSE (MIT)** — DONE (`ce30bf2`).
- **A3 84 symlinks** — DONE (`47e3ee3`): all verified self-referential, nothing depended on them.
- **A7/B6 security threat model** — DONE (`1d5332b`, `docs/security.md`).
- **A4 self-test fixture** — the canonical seed product (referenced by `forge-self-test` but never committed → `/forge-test` hit Phase 0 BLOCKED on every clean clone) is now committed (`f67fb6c`): `seed-product/shopapp/` 4 repos + `seed/prds/01-favorites-cross-surface-sync.md` + topology. `/forge-test` Phases 0–3 now run against a real target; Phase 4 driver eval still needs live MySQL/Redis/Kafka/ES + an Android emulator (operator-run; absent infra → scenarios N/A, not failed).

## Progress log (2026-06-24)

- **Seed is now LOCAL-ONLY — REVERSES A4 (operator decision).** The seed fixture commit `f67fb6c` (`seed-product/` + `seed/prds/`) was dropped from the unpushed history and `seed-product/` + `seed/` are gitignored: the seed is our local test scaffold, never committed, nothing seed-related goes to the remote. **Consequence:** a clean clone no longer ships a self-test fixture, so `/forge-test` hits Phase-0 BLOCKED on a fresh checkout again (the exact problem A4 had "fixed" by committing it). If a bundled fixture is wanted for release, it must ship some other way (separate fixtures repo, generated on demand, or a minimal committed stub) — TBD. The `forge-product.md` migration decision below is unaffected.
- **Seed favorites implementation + tests GREEN** (local seed, gitignored) — completed the implementation the 2026-06-23 `/forge-self-test` run stalled before producing (it stopped at P3-TECH-PLANS). `web-dashboard`: added `hooks/useFavorites.ts`, `components/FavoritesGrid.tsx`, a `Favorite` type in `lib/api.ts`, and jest wiring (`jest.config.js`, `jest.setup.js`, devDeps, `test` script). `shared-schemas/test/favorites_proto.test.js` PASS; `web-dashboard` 4/4 PASS (`useFavorites` ×2 + `FavoritesGrid` ×2). RED→GREEN verified via `npm test` in both repos.
- **A6 merged extractions audit** — DONE (audit only, no fix needed). Scope correction: there are **16** `*-reference.md` files, not 11. (1) Link-depth: CI `.md` check 0 broken over 274 files; gap check (dirs + non-`.md` relative links the CI skips) over all 16 refs = 0 broken. (2) Content-loss (non-blank accounting at each file's add-commit): 15/16 show ~99.8% of SKILL.md-removed lines present verbatim in the reference. The one outlier, `qa-prd-analysis/reference/surface-reference.md` (`f5b4a16`), is a confirmed **false positive** — that commit split one 643→388 SKILL.md across **three** reference files; all "absent" lines are accounted for by documented intentional edits (collapsed anti-pattern rows, condensed Step-0 bash with all 8 read targets preserved, date→placeholder, Lovable/Cursor renames) + lightly-reworded coverage content verified present in `coverage-techniques.md` / `interrogation-templates.md`. No content lost.
- **A8 / A5 topology filename — FULL MIGRATION DONE** (working tree, UNCOMMITTED, supersedes the earlier eval-product-stack-up-only A8 fix). The A5 sweep found the inconsistency was catalog-wide and a **functional break**, not cosmetic: the creator (`/workspace` command) wrote `product.md` while consumers (`eval-product-stack-up`) read `forge-product.md`, so stack-up would fail on real (non-seed) products. **Decision (operator): canonical = `forge-product.md`** (finish the migration — matches the committed seed + namespacing). Renamed every bare `product.md` → `forge-product.md` across **48 files** (skills, commands incl. the `/workspace` creator, agents, `docs/forge-opportunities.md` + `forge-task-verification.md`, and 3 tools: `phase56.py`, `topology_reader.py`, `verify_forge_task.py`). Verify: 0 bare `product.md` remaining (this doc excepted — it discusses the names), 0 `forge-forge-` double-prefix, 240 total `forge-product.md`. Standard (88 conform) + lint (0 warn) + policy-in-sync + 0 broken links + all 3 tools `py_compile` clean.
- **A5 correctness sweep (greppable bug classes) — clean otherwise**: stale tool names (`AskQuestion`/`Cursor`/`Lovable export`) 0 across the 26-skill cohort; `FORGE_BRAIN` brain-path precedence honored everywhere (initial 5 flags were a false positive from a buggy check); `exit`-in-bash — only `canary:111`, harmless (standalone block = own subshell via the Bash tool). The topology contradiction above was the one substantive finding. **Remaining A5:** the deeper per-skill semantic audit (residue, brain-MCP wiring correctness, schema contradictions needing judgment) across the ~24-skill cohort is not yet done.

Remaining P0: run the live Phase-4 smoke (operator; needs MySQL+Kafka+emulator — only Redis/ES were up on 2026-06-24). Then remaining P1 (A5 deep per-skill semantic audit, B2 brain-MCP modernization) and P2 (June-2026 feature alignment).

---

## Part A — Release blockers (from the repo audit)

| # | What | Where | How to fix |
|---|---|---|---|
| A1 | **CI does not enforce skill compliance** — the ≤400 / standard / lint / link work can silently regress | `.github/workflows/` (codeql, forge-brain-guard, forge-hooks, release-tag, scan-codebase — none gate skills) | Add a `skills-guard` workflow running `tools/check_skill_standard.py`, `tools/dev/lint_skill_allowed_tools.py`, a ≤400-line check, and a markdown-link check on PRs touching `skills/**` |
| A2 | **No `LICENSE`** — hard blocker for a public repo | repo root (absent; `.claude-plugin/plugin.json` is v1.1.0) | Add the intended OSS license (BMAD/Spec-Kit use MIT/Apache-2.0) |
| A3 | **84 self-referential symlinks committed** (`skills/<x>/<x> → <x>/`) | `git ls-files -s skills/ \| awk '$1=="120000"'` → 84 | Remove them (`find skills -maxdepth 2 -type l -delete` after confirming nothing depends on them), add a CI check that fails on new ones. They cause infinite glob loops (a naive link-scan reported "5045 broken links" purely from the loop) |
| A4 | **End-to-end self-test fixture was missing** → now committed (`f67fb6c`); live Phase-4 smoke still operator-run | `seed-product/shopapp/`, `seed/prds/` (now present); Phase 4 needs host infra | Phases 0–3 runnable from a clean clone; run `/forge-test` on a host with MySQL/Redis/Kafka/ES + Android emulator to exercise Phase 4 driver eval |
| A5 | **~Half the skills never got a correctness audit** (only line-extracted) | eval-drivers (8), deploy-drivers (4), conductor-orchestrate, scan-codebase, forge-self-test, forge-skill-anatomy, forge-subagent-anatomy, forge-tdd, tech-plan-write, eval-product-stack-up, + loose core skills (autoplan, canary, retro, learn, dream, product-context-load, review-readiness) | Same bug-level audit applied to brain/QA/contract/reasoning/self-heal: residue, schema/path contradictions, `exit`-in-bash, brain-MCP wiring, stale facts |
| A6 | **11 merged single-file extractions taken largely on faith** | the deploy/eval/etc. `*-reference.md` files from the remote | Spot-audit each for content loss (non-blank accounting) + relative-link depth (the conductor one had 4 broken links, now fixed) |
| A8 | **Topology filename inconsistency** — `eval-product-stack-up` references both `forge-product.md` (18×) and `product.md` (13×); the seed standardized on `forge-product.md` | `skills/eval-product-stack-up/` (+ reference) | Reconcile to one name (likely `forge-product.md`) during the P1 eval/stack-up audit; surfaced while verifying the seed |
| A7 | **No security threat model / posture doc** | — | See Part B6 (this is also a market-expectation item now) |

---

## Part B — June-2026 landscape alignment (web research)

### B1. Agent Skills standard is now open & multi-platform
Anthropic opened the Agent Skills spec (Dec 2025, `agentskills.io`, SDK), adopted by
Microsoft, OpenAI, Cursor, GitHub, Atlassian, Figma; enterprise central provisioning +
a partner skills directory now exist. **Progressive disclosure is the standard's core
principle** — which the compliance sweep just satisfied repo-wide.
- **Do:** keep `name`/`description` standard-conformant (already enforced by
  `check_skill_standard.py`). Treat the Claude-only branch as deliberate, but note
  cross-platform portability is now a real, low-cost option for a future branch.
- **Do:** consider listing Forge in a Claude Code **plugin marketplace** (`.claude-plugin/marketplace.json` already exists) for discovery.

### B2. MCP 2026-07-28 RC — brain MCP modernization
The release candidate shifts to a **stateless protocol core** (no `initialize`/`initialized`
handshake, no `Mcp-Session-Id`; per-request `_meta`), formalizes **Tasks** (long-running)
and **Extensions**, adds **MCP Apps** (sandboxed server UIs), hardens auth, and starts
**12-month deprecation** of **Sampling, Roots, and Logging**.
- **Where:** `tools/mcp/forge_brain_mcp.py` (currently implements the classic
  `initialize`/`notifications/initialized` loop; logs to stderr; read-only; resources +
  prompts already shipped).
- **Do (safe, aligned):** Forge is already on the right side of most of this — read-only,
  stdlib-only, **no sampling**, **stderr logging** (matches the Logging-deprecation
  guidance), no roots. Keep it that way.
- **Do (modernize):** add client-cache hints (`ttlMs`/`cacheScope`) to `resources/list`
  / `tools/list`, and `Mcp-Method`/`Mcp-Name` header awareness; document a "2026-07-28
  posture" note. Stateless-core migration is optional for a stdio server (handshake
  still works through the 12-month window) — track it, don't rush it.
- **Avoid:** adding Sampling or Roots (now deprecated).

### B3. Native goals + memory tool + dreaming (this is the user's "goals" item)
Claude Code/agents now have **persistent goals** (objectives across sessions),
a **memory tool** (`memory_20250818`, filesystem-backed, CRUD, + **context editing** →
benchmarked 84% token reduction / 39% quality gain on long tasks), and **dreaming**
between sessions (pattern surfacing + memory restructuring). Subagents can spawn
subagents (background capped 5 levels deep).
- **Where:** Forge's `brain/` (git-backed system-of-record), `agents/dreamer`,
  council/conductor subagent orchestration.
- **Do (decide, don't blindly adopt):** the git-backed brain should stay the
  system-of-record (auditable, multi-repo, reviewable) — but:
  - Map a Forge **task/PRD → a native goal** so long conductor runs persist progress
    across sessions natively.
  - Adopt **context editing** for long conductor/eval loops to cut token cost on the
    big runs (the brain already gives the file substrate the memory tool expects).
  - **Reconcile Forge's `dreamer` with native dreaming** — position `dreamer` as
    product/brain-specific (retrospect + cross-service conflict) rather than duplicating
    the platform's session-level dreaming.
  - Audit orchestration depth against the **5-level background subagent cap**.

### B4. OTel GenAI semantic conventions
The GenAI SIG conventions now span 6 layers (LLM spans, **agent spans**, **MCP tool
spans**, content capture, metrics, and — still early — **quality-eval in spans**).
- **Where:** `tools/eval/forge_otel_export.py`, `tools/eval/forge_trajectory_eval.py`.
- **Do:** align span/attribute names to the current `gen-ai` semconv (agent spans + MCP
  tool spans especially). Forge's trajectory eval already emits eval verdicts — that puts
  it slightly **ahead** of the still-forming "eval-result-in-spans" convention, which is
  a differentiator worth stating.

### B5. Computer-use / browser agents are production
Claude's **computer-use tool** (screenshot + mouse/keyboard, OS-agnostic) and tools like
Vercel's **agent-browser** (Rust + Playwright, selector-free) are mainstream for
automated QA in 2026.
- **Where:** `skills/eval-driver-web-cdp`, `skills/qa-live-app` (CDP today).
- **Do:** offer a **computer-use / agent-browser** option for selector-free, vision-judged
  UI eval (qa-live-app already gained CDP screenshot-judging this sweep). Keep it behind
  the **D5 human-choice gate** (operator picks MCP vs CDP vs computer-use) so no driver is
  assumed. This is outside shipped plugin code, so D5/D13 are not violated.

### B6. Security — now a release expectation, not a nice-to-have
**OWASP Top 10 for Agentic Applications 2026** ranks **Agent Goal Hijacking (ASI01) #1**.
Indirect prompt injection through the **software supply chain** is the dominant
production failure (e.g., the May-2026 Gemini-CLI CVSS-10 via a malicious dependency
injecting prompts through code comments). OpenAI's defense guide centers an **instruction
hierarchy** (system > user > tool output) + sandboxing + human-in-loop.
- **Where:** Forge ingests untrusted **PRD / brain / repo** content into skills, the MCP
  server, dynamic workflows, and `dev-implementer`/`scan-codebase` (which read arbitrary
  repo text).
- **Do (write `docs/security.md` threat model):**
  - State the **instruction hierarchy**: Forge skills/HARD-GATEs > operator > ingested
    PRD/brain/repo content (treat the latter as data, never instructions).
  - Map existing guardrails to OWASP defenses: `.claude/hooks/pre-tool-use.cjs`
    (privilege separation), HARD-GATEs + `AskUserQuestion` (human-in-loop for risky
    actions), `worktree-per-project-per-task` (sandbox/isolation for `dev-implementer`),
    the read-only brain MCP (no write surface).
  - Add explicit handling for **indirect injection** from scanned repos / pasted PRDs
    (content boundary markers, "this is data" framing) and a supply-chain note (Forge
    ships **zero runtime deps** per D5/D13 — already a strong story; state it).

---

## Part C — Competitive positioning (June 2026)

The spec-driven-dev / multi-agent-SDLC field is crowded:

| Tool | Shape | Note |
|---|---|---|
| **BMAD-METHOD** v6.6.0 | 12+ agents, file-based handoffs, MIT | ~46.7k★ — the gorilla; same handoff model as Forge |
| **Kiro** (AWS) | VS Code fork, spec-in-IDE, EARS requirements | IDE-native |
| **GSD** | lean meta-prompting for Claude Code | "low-ceremony BMAD" |
| **GitHub Spec Kit** / **OpenSpec** | structured spec frameworks | open |
| **Augment Cosmos** | org-scale orchestration + shared memory | enterprise |
| **Claude Flow** | multi-agent orchestration | — |

**Forge's defensible differentiators (lead with these in the README):**
1. **Multi-repo PRODUCT orchestration** — most competitors are single-project; Forge
   negotiates contracts across repos (council → shared-dev-spec).
2. **The brain as git-backed system-of-record** — auditable, reviewable, queryable via
   a read-only MCP. (Cosmos has shared memory; Forge's is git + OKF + decision provenance.)
3. **Real multi-surface EVAL with drivers + verdict gates** — Forge actually runs and
   verifies (web/api/db/mobile, eval-judge GREEN/RED/YELLOW, self-heal loop). Most
   competitors stop at code generation; this is the strongest moat.
4. **Claude-native depth** — skills + hooks + subagents + dynamic workflows + MCP, all
   first-party.

**Gaps worth closing:** consider **EARS notation** for requirements (Kiro's edge);
make the **eval/verdict** story unmissable in the README (it's the differentiator and
it's currently buried); publish a one-page **"Forge vs BMAD/Kiro"** comparison.

---

## Part D — Prioritized action plan

**P0 — prove it runs + lock it in (release gate):**
1. A4 end-to-end smoke on the seed product.
2. A1 CI `skills-guard` (standard + lint + ≤400 + link-check + no-new-symlinks).
3. A2 `LICENSE`; A3 remove the 84 symlinks.
4. B6 `docs/security.md` threat model (OWASP-aligned).

**P1 — finish the correctness work:**
5. A5 bug-audit the un-audited cohorts (eval-drivers, deploy-drivers, conductor, scan,
   self-test, …) — same treatment as QA/contract.
6. A6 spot-audit the 11 merged extractions (content loss + link depth).
7. B2 brain-MCP modernization (cache hints, 2026-07-28 posture note).

**P2 — market alignment / features:**
8. B3 native goals + memory-tool/context-editing integration; reconcile `dreamer` with
   native dreaming.
9. B4 OTel GenAI semconv alignment of the eval exporters.
10. B5 computer-use / agent-browser eval option (behind the D5 gate).
11. C positioning: README differentiators + EARS notation + a "vs BMAD" page.

---

## Sources (June 2026)
- Anthropic Agent Skills open standard — anthropic.com/engineering, venturebeat.com, thenewstack.io
- MCP 2026-07-28 release candidate — blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate, modelcontextprotocol.io/specification
- Claude Code 2026 features (subagents, goals, memory, dreaming) — marktechpost.com, mindstudio.ai, code.claude.com/docs
- Memory tool + context editing — platform.claude.com/docs/.../memory-tool
- OTel GenAI semantic conventions — opentelemetry.io/docs/specs/semconv/gen-ai, opentelemetry.io/blog
- Computer-use / agent-browser — platform.claude.com/docs/.../computer-use-tool, github.com/vercel-labs/agent-browser
- Spec-driven-dev competitors (BMAD, Kiro, GSD, Spec Kit) — marktechpost.com, augmentcode.com, dev.to
- Security: OWASP Top 10 Agentic 2026 (ASI01 goal hijacking), supply-chain injection — helpnetsecurity.com, owasp cheat sheet, arxiv.org/html/2601.17548
