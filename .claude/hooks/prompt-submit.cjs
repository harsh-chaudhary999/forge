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

function log(message) {
  if (process.env.FORGE_HOOKS_DEBUG === '1') {
    console.error(`[prompt-submit] ${message}`);
  }
}

// ==================== Gate Detection ====================

const GATE_PATTERNS = {
  QA_CSV:           /\[P4\.0-QA-CSV\].*approved=yes/,
  EVAL_YAML:        /\[P4\.0-EVAL-YAML\]/,
  TDD_RED:          /\[P4\.0-TDD-RED\]/,
  DISPATCH:         /\[P4\.1-DISPATCH\]/,
  EVAL_GREEN:       /\[P4\.4-EVAL-GREEN\]/,
  PR_MERGED:        /\[P5[.-]/,
  SPEC_FROZEN:      /\[P3-SPEC-FROZEN\]/,
  PRD_LOCKED:       /\[P1-PRD-LOCKED\]/,
  // Standalone QA pipeline gates (qa-pipeline.log)
  QA_P7_REPORT:       /\[QA-P7-REPORT\]/,
  QA_P6_VERDICT:      /\[QA-P6-VERDICT\]/,
  QA_P5_EXEC:         /\[QA-P5-EXEC\]/,
  QA_P4_STACK:        /\[QA-P4-STACK\]/,
  QA_CODE_VALIDATE:   /\[QA-CODE-VALIDATE\]/,
  QA_BRANCH_ENV:      /\[QA-BRANCH-ENV\]/,
  QA_P2_SCENARIOS:    /\[QA-P2-SCENARIOS\]/,
  QA_P1_LOAD:         /\[QA-P1-LOAD\]/,
};

/**
 * Determines the next gate message based on conductor.log content.
 * Returns a string or null if no specific next-gate applies.
 */
/**
 * Reads qa-pipeline.log from a brain task directory and resolves the QA phase state.
 * Returns a next-gate string if a QA pipeline is in flight, or null if complete/not started.
 *
 * NOTE: This function receives log content already scoped to a specific task log.
 * The scoping logic is in findMostRecentQAPipelineLog (FORGE_TASK_ID → mtime fallback).
 */
function resolveQAPipelineGate(logContent) {
  const has = (pattern) => pattern.test(logContent);

  // QA pipeline fully done
  if (has(GATE_PATTERNS.QA_P7_REPORT)) return null;

  // Verdict rendered — write report
  if (has(GATE_PATTERNS.QA_P6_VERDICT)) {
    const verdictMatch = logContent.match(/\[QA-P6-VERDICT\][^\n]*verdict=(\w+)/);
    const verdict = verdictMatch ? verdictMatch[1] : '?';
    if (verdict === 'RED') {
      return `QA NEXT GATE: Verdict is RED — invoke self-heal-triage to classify failure, fix the issue, then re-run /qa-run. Do NOT report success without a GREEN re-run.`;
    }
    return `QA NEXT GATE: Verdict=${verdict} — write QA run report to brain (qa/qa-run-report-<ts>.md) and log [QA-P7-REPORT].`;
  }

  // Execution started — need verdict
  if (has(GATE_PATTERNS.QA_P5_EXEC)) {
    return `QA NEXT GATE: Execution in progress — invoke eval-judge to produce GREEN/RED/YELLOW verdict, then log [QA-P6-VERDICT].`;
  }

  // Stack up done — start execution
  if (has(GATE_PATTERNS.QA_P4_STACK)) {
    return `QA NEXT GATE: Stack is up — invoke eval-coordinate-multi-surface with scenario files from brain/prds/<task-id>/eval/ and log [QA-P5-EXEC].`;
  }

  // Code validate complete — go straight to verdict (skip P4/P5)
  if (has(GATE_PATTERNS.QA_CODE_VALIDATE)) {
    const failMatch = logContent.match(/\[QA-CODE-VALIDATE\][^\n]*fail=(\d+)/);
    const failCount = failMatch ? parseInt(failMatch[1], 10) : null;
    if (failCount !== null && failCount > 0) {
      return `QA NEXT GATE (branch-code-validate): ${failCount} repo(s) failed tests — invoke eval-judge with test output, render RED verdict, then invoke self-heal-triage. Log [QA-P6-VERDICT].`;
    }
    return `QA NEXT GATE (branch-code-validate): All repos passed — invoke eval-judge to render GREEN verdict, then log [QA-P6-VERDICT] and write report.`;
  }

  // Branch/env ready — stack up (or skip based on run mode)
  if (has(GATE_PATTERNS.QA_BRANCH_ENV)) {
    return `QA NEXT GATE: Branch/env ready — for branch-local: invoke eval-product-stack-up and log [QA-P4-STACK]. For url-only/branch-tracking: go directly to QA-P5. For branch-code-validate: [QA-CODE-VALIDATE] should already be logged.`;
  }

  // Scenarios written — branch/env prep
  if (has(GATE_PATTERNS.QA_P2_SCENARIOS)) {
    return `QA NEXT GATE: Scenarios written — invoke qa-branch-env-prep (ask run mode: url-only / branch-local / branch-tracking), then log [QA-BRANCH-ENV].`;
  }

  // Brain loaded — generate scenarios
  if (has(GATE_PATTERNS.QA_P1_LOAD)) {
    return `QA NEXT GATE: Brain loaded — invoke qa-prd-analysis → qa-write-scenarios to generate eval YAML, then log [QA-P2-SCENARIOS].`;
  }

  return null;
}

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
