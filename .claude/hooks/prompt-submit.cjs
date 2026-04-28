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

function log(message) {
  if (process.env.FORGE_HOOKS_DEBUG === '1') {
    console.error(`[prompt-submit] ${message}`);
  }
}

// ==================== Gate Detection ====================

const GATE_PATTERNS = {
  QA_CSV:       /\[P4\.0-QA-CSV\].*approved=yes/,
  EVAL_YAML:    /\[P4\.0-EVAL-YAML\]/,
  TDD_RED:      /\[P4\.0-TDD-RED\]/,
  DISPATCH:     /\[P4\.1-DISPATCH\]/,
  EVAL_GREEN:   /\[P4\.4-EVAL-GREEN\]/,
  PR_MERGED:    /\[P5[.-]/,
  SPEC_FROZEN:  /\[P3-SPEC-FROZEN\]/,
  PRD_LOCKED:   /\[P1-PRD-LOCKED\]/,
};

/**
 * Finds the most recently modified conductor.log in the brain prds/ directory.
 */
function findMostRecentConductorLog(brainPath) {
  const prdsDir = path.join(brainPath, 'prds');
  if (!fs.existsSync(prdsDir)) return null;

  let mostRecentLog = null;
  let mostRecentMtime = 0;

  try {
    const taskDirs = fs.readdirSync(prdsDir);
    for (const taskDir of taskDirs) {
      const logPath = path.join(prdsDir, taskDir, 'conductor.log');
      if (!fs.existsSync(logPath)) continue;
      try {
        const stat = fs.statSync(logPath);
        if (stat.mtimeMs > mostRecentMtime) {
          mostRecentMtime = stat.mtimeMs;
          mostRecentLog = logPath;
        }
      } catch (_) {}
    }
  } catch (_) {}

  return mostRecentLog;
}

/**
 * Determines the next gate message based on conductor.log content.
 * Returns a string or null if no specific next-gate applies.
 */
function resolveNextGate(logContent) {
  const has = (pattern) => pattern.test(logContent);

  // Already fully done
  if (has(GATE_PATTERNS.PR_MERGED)) return null;

  // Eval GREEN → move to PR
  if (has(GATE_PATTERNS.EVAL_GREEN)) {
    return 'NEXT GATE: Invoke pr-set-coordinate → pr-set-merge-order → merge PRs in locked order → log [P5-PR-MERGED]';
  }

  // Dispatched but not GREEN → eval running
  if (has(GATE_PATTERNS.DISPATCH)) {
    return 'NEXT GATE: Eval must reach GREEN (all scenarios pass in one run) before PR set. If RED: invoke self-heal-locate-fault → self-heal-triage (max 3 iterations).';
  }

  // Spec frozen → need State 4b gates before dispatch
  if (has(GATE_PATTERNS.SPEC_FROZEN)) {
    const missing = [];
    if (!has(GATE_PATTERNS.QA_CSV))    missing.push('[P4.0-QA-CSV] — run qa-prd-analysis → qa-manual-test-cases-from-prd → get user approval');
    if (!has(GATE_PATTERNS.EVAL_YAML)) missing.push('[P4.0-EVAL-YAML] — write eval scenarios under prds/<id>/eval/*.yaml');
    if (!has(GATE_PATTERNS.TDD_RED))   missing.push('[P4.0-TDD-RED] — write failing test, observe FAIL before any implementation');

    if (missing.length > 0) {
      return `NEXT GATE (State 4b — required before [P4.1-DISPATCH]):\n${missing.map(m => `  • ${m}`).join('\n')}`;
    }
    return 'NEXT GATE: All State 4b gates satisfied. Log [P4.1-DISPATCH] and begin eval phase.';
  }

  // PRD locked → council
  if (has(GATE_PATTERNS.PRD_LOCKED)) {
    return 'NEXT GATE: Invoke forge-council-gate → council-multi-repo-negotiate (4 surfaces + 5 contracts) → spec-freeze → log [P3-SPEC-FROZEN]';
  }

  return null; // early stages or unrecognized state — no specific next-gate
}

/**
 * Attempts to read conductor.log and resolve a next-gate message.
 * Returns the next-gate string or null if unavailable.
 */
function forgeBrainSearchPaths() {
  const out = [];
  const seen = new Set();
  for (const key of ['FORGE_BRAIN', 'FORGE_BRAIN_PATH']) {
    const s = process.env[key] && String(process.env[key]).trim();
    if (!s) continue;
    const abs = path.resolve(s);
    if (!seen.has(abs)) {
      seen.add(abs);
      out.push(abs);
    }
  }
  out.push(path.join(os.homedir(), 'forge', 'brain'));
  return out;
}

function tryGetNextGate() {
  const brainCandidates = forgeBrainSearchPaths();

  for (const brainPath of brainCandidates) {
    if (!fs.existsSync(brainPath)) continue;

    const logPath = findMostRecentConductorLog(brainPath);
    if (!logPath) continue;

    try {
      const logContent = fs.readFileSync(logPath, 'utf-8');
      return resolveNextGate(logContent);
    } catch (e) {
      log(`Failed to read conductor.log: ${e.message}`);
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
