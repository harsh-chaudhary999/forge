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
 * crossed and which are still pending. If no brain/log found, emits no next-gate
 * line — existing static gate reminder is injected as before.
 *
 * Why this matters:
 * SessionStart fires once. After 20 messages agents forget gates exist.
 * This hook keeps the 8 non-negotiable rules in working context on every
 * turn — the cost is negligible, the drift prevention is real.
 * The next-gate line adds specificity: instead of "all gates matter",
 * the agent sees "YOUR NEXT REQUIRED STEP IS X".
 *
 * Cannot be skipped:
 * - Rationalization: "I already know the gates, this is noise"
 *   Truth: You drift. Pattern matching degrades over long conversations.
 *   Consistent injection is the only defense against silent rationalization.
 *
 * Output: additionalContext injected into every prompt turn
 * Cross-platform: works on Linux, macOS, Windows
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  forgeBrainSearchPaths,
  findMostRecentConductorLog,
} = require(path.join(__dirname, 'forge-stage-detect.cjs'));

const {
  resolveNextGate,
  resolveQAPipelineGate,
} = require(path.join(__dirname, 'prompt-submit-gates.cjs'));

function log(message) {
  if (process.env.FORGE_HOOKS_DEBUG === '1') {
    console.error(`[prompt-submit] ${message}`);
  }
}

/**
 * Finds the relevant qa-pipeline.log for the current session.
 *
 * Scoping strategy (matches session-start.cjs conductor log selection):
 *   1. If FORGE_TASK_ID or FORGE_PRD_TASK_ID is set and brain/prds/<id>/qa-pipeline.log
 *      exists → use that file (recommended when multiple tasks exist).
 *   2. Else → fall back to the most recently modified qa-pipeline.log under prds/ (mtime
 *      heuristic). WARNING: with concurrent QA runs this can pick the wrong task.
 *      Set FORGE_TASK_ID in your shell to make injection deterministic.
 *
 * Returns the resolved log path, or null if none found.
 */
function findMostRecentQAPipelineLog(brainPath) {
  const prdsDir = path.join(brainPath, 'prds');
  if (!fs.existsSync(prdsDir)) return null;

  // Prefer task-scoped log when env provides a task ID
  const envTaskId = process.env.FORGE_TASK_ID || process.env.FORGE_PRD_TASK_ID;
  if (envTaskId) {
    const scopedLog = path.join(prdsDir, envTaskId, 'qa-pipeline.log');
    if (fs.existsSync(scopedLog)) {
      log(`QA pipeline log: scoped by FORGE_TASK_ID=${envTaskId}`);
      return scopedLog;
    }
  }

  // mtime fallback — ambiguous when multiple tasks have active QA runs
  let best = null;
  try {
    for (const taskId of fs.readdirSync(prdsDir)) {
      const logPath = path.join(prdsDir, taskId, 'qa-pipeline.log');
      if (!fs.existsSync(logPath)) continue;
      const mtime = fs.statSync(logPath).mtimeMs;
      if (!best || mtime > best.mtime) best = { path: logPath, mtime };
    }
  } catch (e) {
    log(`QA pipeline log scan error: ${e.message}`);
  }
  if (best) log(`QA pipeline log: mtime fallback → ${best.path} (set FORGE_TASK_ID for deterministic scoping)`);
  return best ? best.path : null;
}

function tryGetNextGate() {
  const brainCandidates = forgeBrainSearchPaths();

  for (const brainPath of brainCandidates) {
    if (!fs.existsSync(brainPath)) continue;

    // Check conductor.log first (main pipeline)
    const logPath = findMostRecentConductorLog(brainPath);
    if (logPath) {
      try {
        const logContent = fs.readFileSync(logPath, 'utf-8');
        const gate = resolveNextGate(logContent);
        if (gate) return gate;
      } catch (e) {
        log(`Failed to read conductor.log: ${e.message}`);
      }
    }

    // Check qa-pipeline.log (standalone QA pipeline)
    const qaLogPath = findMostRecentQAPipelineLog(brainPath);
    if (qaLogPath) {
      try {
        const qaLogContent = fs.readFileSync(qaLogPath, 'utf-8');
        const qaGate = resolveQAPipelineGate(qaLogContent);
        if (qaGate) return qaGate;
      } catch (e) {
        log(`Failed to read qa-pipeline.log: ${e.message}`);
      }
    }
  }

  return null;
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

let contextLines = [staticReminder];

try {
  const nextGate = tryGetNextGate();
  if (nextGate) {
    contextLines = [
      `<forge-next-gate>\n${nextGate}\n</forge-next-gate>`,
      staticReminder,
    ];
    log(`Next-gate injected: ${nextGate.split('\n')[0]}`);
  } else {
    log('No next-gate resolved — static reminder only');
  }
} catch (e) {
  // Any error in next-gate detection → silently fall through to static only
  log(`Next-gate detection error (non-fatal): ${e.message}`);
}

const output = {
  hookSpecificOutput: {
    hookEventName: 'UserPromptSubmit',
    additionalContext: contextLines.join('\n\n'),
  },
};

process.stdout.write(JSON.stringify(output));
process.exit(0);
