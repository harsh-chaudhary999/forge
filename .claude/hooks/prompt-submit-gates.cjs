#!/usr/bin/env node
/**
 * prompt-submit-gates.cjs
 *
 * Pure gate-resolution logic shared by:
 *   - prompt-submit.cjs (Claude Code UserPromptSubmit hook)
 *   - tools/test-prompt-submit-gates.cjs (CI regression tests)
 *
 * No process.exit, no I/O — safe to require() from tests.
 */

'use strict';

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
 * Reads qa-pipeline.log content and resolves the QA phase state.
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

module.exports = {
  GATE_PATTERNS,
  resolveNextGate,
  resolveQAPipelineGate,
};
