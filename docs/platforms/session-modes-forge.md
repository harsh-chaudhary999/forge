# Forge phase session styles (Claude Code)

Match the **Forge phase** to a **session style**. Forge cannot switch Claude Code's
permission mode programmatically — hooks and `commands/*.md` inject text; they do
not flip "plan vs agent" or your tool allowlist. This is a convention you apply.

---

## Two session styles

| Style | Use during | Goal |
|--------|------------|------|
| **Planning-style** | **`/intake`**, **`/council`**, **`/plan`** (authoring or **human review** of tech plans before approval) | Lock scope, contracts, and brain artifacts with explicit reasoning; **minimize** large autonomous diffs until intent is frozen. |
| **Execution-style** | **`/build`**, **`/eval`**, **`/heal`**, heavy refactors after plans are approved | Run tools, terminals, stack-up, multi-file edits, and iteration until gates pass. |

**Rule of thumb:** If the step **writes or locks** `~/forge/brain/prds/<task-id>/`
contract artifacts (`prd-locked.md`, `shared-dev-spec.md`, approved tech plans),
bias toward **planning-style**. If the step **changes product repos** or **runs the
product stack**, bias toward **execution-style**.

Forge gates (State 4b, `qa/semantic-automation.csv` + manifest, TDD, etc.) apply
**regardless** of session style.

### How to apply it in Claude Code

- **Plan mode** (review-first) for planning-style phases — ask for analysis and
  drafts, applying edits only after you approve; or run with a narrow permission
  allowlist.
- **Full agent** (with tools) for execution-style phases — authorize edits, tests,
  and subprocesses.
- The assistant should **remind you to change style** when the active Forge phase
  changes (see `commands/forge.md` and `skills/using-forge`).

### Blocking interactive prompts

Human-needed answers (intake, QA, waivers, confirmations) use a **blocking
interactive prompt** — the **`AskUserQuestion`** tool — never prose-only "reply
with…". Full dialogue norms (one-step horizon, question-forward, bundled-turn
rules) live in **`docs/forge-one-step-horizon.md`** and **`skills/_shared/human-input.md`**.
