#!/usr/bin/env node

/**
 * prompt-submit.cjs
 *
 * DISCIPLINE REINFORCER
 * Fires on every user message (UserPromptSubmit).
 * Injects a compact reminder of all active Forge HARD-GATEs into context
 * so the agent can't drift or rationalize shortcuts mid-conversation.
 *
 * Next-gate injection:
 * Reads conductor.log from the brain directory (FORGE_BRAIN, FORGE_BRAIN_PATH, or ~/forge/brain)
 * and prepends a targeted "NEXT GATE" reminder based on which gates have been
 * crossed and which are still pending. Log paths and file contents are loaded
 * once per brain via `loadBrainPromptBundle` in forge-stage-detect.cjs (conductor + qa index).
 *
 * Static HARD-GATE block suppression (emits no additionalContext):
 *   FORGE_DISABLE_GATE_INJECTION=1
 *   No Forge brain root exists on disk (no FORGE_BRAIN / FORGE_BRAIN_PATH / ~/forge/brain)
 *   When FORGE_TASK_ID / FORGE_PRD_TASK_ID is set: the **scoped** primary conductor.log
 *     contains [P5…] (PR merged for that task)
 *   When task id is **unset**: **every** per-task conductor.log under prds (across all
 *     existing brain roots) contains [P5…] — avoids false silence when the mtime-newest log is a done
 *     task but another task is still active
 * When suppressed, the static list is not injected; next-gate lines are also omitted.
 *
 * Why this matters:
 * SessionStart fires once. After 20 messages agents forget gates exist.
 * When injection is active, this hook keeps the 8 non-negotiable rules in
 * working context on each turn (suppressed when no brain, all tasks merged, or opt-out).
 * The next-gate line adds specificity: instead of "all gates matter",
 * the agent sees "YOUR NEXT REQUIRED STEP IS X".
 *
 * Output: additionalContext injected into every prompt turn
 * Cross-platform: works on Linux, macOS, Windows
 */

const fs = require('fs');
const path = require('path');
const { forgeBrainSearchPaths, loadBrainPromptBundle } = require(path.join(
  __dirname,
  'forge-stage-detect.cjs',
));

const { resolveNextGate, resolveQAPipelineGate } = require(path.join(
  __dirname,
  'prompt-submit-gates.cjs',
));

const { shouldSuppressFromConductorMergeState } = require(path.join(__dirname, 'prompt-submit-injection.cjs'));

/** Evaluated once per process — env-based paths rarely change mid-session. */
const BRAIN_PATHS = forgeBrainSearchPaths();

function log(message) {
  if (process.env.FORGE_HOOKS_DEBUG === '1') {
    console.error(`[prompt-submit] ${message}`);
  }
}

/**
 * @returns {{ suppress: boolean, nextGate: string|null }}
 */
function computeGateInjection() {
  const injectionDisabled =
    process.env.FORGE_DISABLE_GATE_INJECTION !== undefined &&
    String(process.env.FORGE_DISABLE_GATE_INJECTION).trim() === '1';

  const anyBrainRootExists = BRAIN_PATHS.some((p) => fs.existsSync(p));

  if (injectionDisabled) {
    return { suppress: true, nextGate: null };
  }
  if (!anyBrainRootExists) {
    return { suppress: true, nextGate: null };
  }

  const taskIdRaw = process.env.FORGE_TASK_ID || process.env.FORGE_PRD_TASK_ID;
  const taskIdEnvSet = !!(taskIdRaw && String(taskIdRaw).trim());

  /** @type {Map<string, ReturnType<typeof loadBrainPromptBundle>>} */
  const bundleByBrain = new Map();
  for (const brainPath of BRAIN_PATHS) {
    if (!fs.existsSync(brainPath)) continue;
    bundleByBrain.set(brainPath, loadBrainPromptBundle(brainPath));
  }

  const allConductorBodies = [];
  for (const brainPath of BRAIN_PATHS) {
    if (!fs.existsSync(brainPath)) continue;
    const bundle = bundleByBrain.get(brainPath);
    if (!bundle) continue;
    for (const e of bundle.entries) {
      allConductorBodies.push(e.content);
    }
  }

  let primaryBodiesForSuppress = allConductorBodies;
  if (taskIdEnvSet) {
    let primaryContent = null;
    for (const brainPath of BRAIN_PATHS) {
      if (!fs.existsSync(brainPath)) continue;
      const bundle = bundleByBrain.get(brainPath);
      if (bundle && bundle.primaryContent !== null && bundle.primaryContent !== undefined) {
        primaryContent = bundle.primaryContent;
        break;
      }
    }
    primaryBodiesForSuppress = primaryContent !== null ? [primaryContent] : [];
  }

  const suppress = shouldSuppressFromConductorMergeState(taskIdEnvSet, primaryBodiesForSuppress);

  if (suppress) {
    return { suppress: true, nextGate: null };
  }

  let nextGate = null;
  for (const brainPath of BRAIN_PATHS) {
    if (!fs.existsSync(brainPath)) continue;
    const bundle = bundleByBrain.get(brainPath);
    if (bundle && bundle.primaryContent) {
      const g = resolveNextGate(bundle.primaryContent);
      if (g) {
        nextGate = g;
        break;
      }
    }

    if (bundle && bundle.qaPrimaryContent) {
      const qaGate = resolveQAPipelineGate(bundle.qaPrimaryContent);
      if (qaGate) {
        nextGate = qaGate;
        break;
      }
    }
  }

  return { suppress: false, nextGate };
}

// ==================== Main Logic ====================

const staticReminder = [
  '<forge-active-gates>',
  'HARD-GATES (non-negotiable, no exceptions):',
  '• forge-intake-gate    — PRD locked in brain before council',
  '• forge-council-gate   — All 4 surfaces + 5 contracts negotiated before spec freeze',
  '• forge-eval-gate      — Eval GREEN before any PR is raised',
  '• forge-worktree-gate  — Every task in a fresh worktree (D30)',
  '• forge-tdd            — Test written and watched FAIL before any implementation code',
  '• forge-verification   — Run commands and log real output before claiming done',
  '• forge-brain-persist  — Every decision committed to brain (never just in chat)',
  '• forge-trust-code     — Reviewer reads actual diff — never trusts implementer report',
  'If you are tempted to skip any gate: STOP. Invoke the skill. No exceptions.',
  '</forge-active-gates>',
].join('\n');

let additionalContext = '';

try {
  const { suppress, nextGate } = computeGateInjection();

  if (!suppress) {
    let contextLines = [staticReminder];
    if (nextGate) {
      contextLines = [
        `<forge-next-gate>\n${nextGate}\n</forge-next-gate>`,
        staticReminder,
      ];
      log(`Next-gate injected: ${nextGate.split('\n')[0]}`);
    } else {
      log('No next-gate resolved — static reminder only');
    }
    additionalContext = contextLines.join('\n\n');
  } else {
    log('Gate injection suppressed (no brain, merged complete, or FORGE_DISABLE_GATE_INJECTION=1)');
  }
} catch (e) {
  log(`Gate injection error (non-fatal): ${e.message}`);
}

const output = {
  hookSpecificOutput: {
    hookEventName: 'UserPromptSubmit',
    additionalContext,
  },
};

process.stdout.write(JSON.stringify(output));
process.exit(0);
