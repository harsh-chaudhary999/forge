# Forge Plugin — AI Guidelines

## What This Repo Is

Forge is a plug-and-play multi-repo product orchestration plugin for Claude Code, Cursor, Gemini CLI, Project IDX, and JetBrains AI. It takes a PRD and ships it end-to-end across any product stack.

## If You Are an AI Working in This Repo

- All skills live in `skills/` at repo root (not `.claude/skills/` — that is a symlink)
- All agents live in `agents/` at repo root
- **`hooks/`** — IDE hook manifests (`hooks.json`, `hooks-cursor.json`) and the **`hooks/session-start`** shell shim (for configs that do not call `node` directly)
- **`.claude/hooks/`** — Claude Code hook implementations (`session-start.cjs`, `pre-tool-use.cjs`, …) plus git hook scripts installed for this repo — do not confuse the two directories
- The `using-forge` skill is the bootstrap; Claude Code loads it via **`hooks/hooks.json`** → **`session-start.cjs`**

## Skill Format

Every skill is a `SKILL.md` file with YAML frontmatter:
```yaml
---
name: skill-name
description: WHEN to invoke — describes the trigger, not what the skill does
type: rigid | flexible
requires: [other-skill-name]
---
```

## Execution Rules (Non-Negotiable)

- **Never write scripts to `/tmp` and execute them.** Run all bash commands inline. Writing `/tmp/verify.sh`, `/tmp/check.sh`, `/tmp/final_check.sh` etc. and then running them is forbidden — it obscures what's being executed, creates untracked side effects, and requires extra permission approvals. If a command is complex, run it directly as a multi-line heredoc or chained pipeline.
- **`/tmp` is only for data files, never for scripts.** Intermediate data files (e.g. scan output, temp lists) are acceptable. Executable scripts written to `/tmp` are not.
- **Blocking interactive prompts (every supported IDE):** Skills name **`AskUserQuestion`** in **`allowed-tools`**; hosts map per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** (Cursor → **`AskQuestion`**; CLIs / editors without the tool → **numbered choices + stop**). Human answers must not be prose-only “reply if…” without that structure.
- **Assistant dialogue (live chat):** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **no bundled** unrelated decisions in one turn; **question-forward** (no unsolicited reference-doc preface or **later-stage** status suffix on single-answer turns) except when the user asked for status or the roadmap. **Multi-question elicitation** items **4–8**. Static docs (**README**, **`commands/`**) may still list full dependency order.

## Written artifacts — precision (scans, plans, QA, eval, code, tests)

- **Forbidden:** vague quantifiers **and** claims that stop at **counts** when the job is to describe **inventory, behavior, or coverage**. Example: **"14 services"** without **which directories / which entrypoints / how listed** is still too thin.
- **Required — what / where / how** for anything another person (or agent) must verify:
  - **What** — specific artifact or fact (file, symbol, route, test step id, requirement id).
  - **Where** — absolute or repo-root path, brain path, or stable doc anchor.
  - **How** — reproducible observation (exact command + cwd, `rg`/`Read` with pattern or line range, `SCAN.json` field name + path, git `rev-parse`).
- Prefer **tables or bullet lists of paths and roles** over headline numbers. Use counts only **alongside** that detail, not instead of it.
- If not yet evidenced: **UNKNOWN** + **concrete** next probe (which path you will open, which command you will run) — never **N+** or count-only summaries.

## Instruction completeness — volume is not a skip lever

- **Large** inputs or outputs (very long files, full export lists, many brain writes) are **not** a reason to skip numbered steps, replace required work with a high-level summary, or stop early without **BLOCKED** + evidence.
- **Do** batch reads/writes, stream to files under **`~/forge/brain/`**, and continue until the **skill or command** is satisfied. Self-directed “too big” shortcuts are **forbidden**.
- A **skill’s own** explicit stop rule (e.g. its **HARD-GATE** or stated fail condition) overrides nothing — follow that skill’s letter. Do **not** conflate that with ad‑hoc “too much data.”

## Key Constraints

- **D5 (agent frameworks vs eval hosts):** Do **not** ship **LangChain** (or similar agent orchestration frameworks) **inside Forge plugin code** (skills, bundled hooks, first-party tools) as a runtime dependency. **Playwright, Puppeteer, raw CDP clients, Appium, XCTest, or browser/device automation invoked via MCP** are **not** banned for **your product’s eval** on the **operator’s machine or CI**: they run **outside** Forge’s shipped plugin code. **Before choosing a web or mobile driver implementation**, ask the human **how they want to proceed** (e.g. existing **MCP** for browser/Appium vs local **CDP** / **ADB** / **XCTest** scripts). Document the choice in the task brain if it affects reproducibility.
- D13: No runtime dependency on any external plugin at runtime.
- D15: Skills are TDD'd — developed via pressure scenarios against seed product.
- D24: HARD-GATE tags on every non-skippable step.
- D25: Anti-Pattern preambles on every discipline-enforcing skill.

## Where Things Live

| Thing | Location |
|---|---|
| Skills (full catalog) | `skills/` — count: `bash scripts/count-skills.sh` from repo root |
| Agents (4) | `agents/` |
| Commands (21) | `commands/` |
| Hook manifests + `hooks/session-start` shim | `hooks/` |
| Claude / git hook scripts (`.cjs`) | `.claude/hooks/` |
| Brain (decisions) | `brain/` |
| Seed product | `seed-product/` |
| Platform docs | `docs/platforms/` |
