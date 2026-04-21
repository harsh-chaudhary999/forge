# Forge phase session styles (all hosts)

Forge is **host-agnostic**: the same pipeline runs in Cursor, Claude Code, Antigravity, Gemini CLI, Codex, Copilot CLI, OpenCode, JetBrains AI, etc. What differs per product is only **how you steer the assistant** — some UIs expose explicit **modes** (e.g. planning vs coding); others use **prompts**, **permissions**, or **read-only** sessions.

**Forge cannot switch your host’s mode or permissions programmatically.** Hooks and `commands/*.md` inject text; they do not control the IDE’s toggle for “plan vs agent” or equivalent. This document defines a **portable convention**: match **Forge phase** to **session style** on whatever host you use.

---

## Two session styles (Forge-native)

| Style | Use during | Goal |
|--------|------------|------|
| **Planning-style** | **`/intake`**, **`/council`**, **`/plan`** (authoring or **human review** of tech plans before approval) | Lock scope, contracts, and brain artifacts with explicit reasoning; **minimize** large autonomous diffs until intent is frozen. |
| **Execution-style** | **`/build`**, **`/eval`**, **`/heal`**, heavy refactors after plans are approved | Run tools, terminals, stack-up, multi-file edits, and iteration until gates pass. |

**Rule of thumb:** If the step **writes or locks** `~/forge/brain/prds/<task-id>/` **contract** artifacts (`prd-locked.md`, `shared-dev-spec.md`, approved tech plans), bias toward **planning-style**. If the step **changes product repos** or **runs the product stack**, bias toward **execution-style**.

Forge gates (State 4b, `eval/*.yaml`, TDD, etc.) apply **regardless** of host session style.

---

## How to apply this on your host

There is no single global setting. Pick the mechanism your product actually offers:

- **Explicit modes** (e.g. *Plan* vs *Agent*, *Ask* vs *Agent*) — switch when you change Forge phase, as your UI allows.
- **No modes** (CLI-only, context-only) — use **prompts**: for planning-style phases, ask for analysis and drafts **without** applying edits until you say proceed; for execution-style, authorize edits, tests, and subprocesses.
- **Read-only / sandbox** — some hosts can start a session that cannot write files; that can approximate planning-style **only if** you still allow writing **brain** paths when locking intake/council output (adjust host policy or use a writable brain clone).

The assistant should **remind you to change style** when the active Forge phase changes (see `commands/forge.md` and `skills/using-forge`).

---

## Host-specific labels (examples, not exhaustive)

| Host / surface | Examples of “planning-style” vs “execution-style” | Notes |
|----------------|---------------------------------------------------|--------|
| **Cursor** | **Plan** vs **Agent** | UI toggle; see `cursor.md`. |
| **Claude Code** | Narrow permission / review-first prompts vs full **Agent** with tools | No Forge-enforced split; use phase-appropriate prompts and human checkpoints. |
| **Google Antigravity** | Review-first tasking vs autonomous multi-file runs | Follow IDE guidance for when to constrain tools. |
| **Gemini CLI** | Instruction to “propose only” vs “implement and run tests” | No slash-command layer unless added; skills by invocation. |
| **OpenAI Codex** | High-level design in prose first vs “edit files and run commands” | Context-only; no Forge hooks — style is 100% prompt discipline. |
| **GitHub Copilot CLI** | Same as Codex — prompt and permission discipline | See `copilot-cli.md` for tool mapping. |
| **JetBrains AI / Junie** | Chat vs inline apply; scope of allowed changes | See `jetbrains.md`. |
| **OpenCode** | Same as other CLIs — prompt and tool policy per phase | Project plugin loads Forge context from the repo. |

If your host adds new modes later, map them to the **two Forge styles** above — not the other way around.
