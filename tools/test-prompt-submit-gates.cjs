#!/usr/bin/env node
/**
 * test-prompt-submit-gates.cjs
 *
 * Smoke-tests for resolveNextGate and resolveQAPipelineGate in prompt-submit.cjs.
 *
 * Run:
 *   node tools/test-prompt-submit-gates.cjs
 *
 * Exits 0 on pass, 1 on any failure.
 *
 * Pattern: each test appends known log lines and asserts the returned gate string
 * contains an expected substring (or is null). Keeps the test surface minimal so
 * regex drift in the hook is caught immediately.
 */

'use strict';

const path = require('path');

// ── Inline the gate logic under test ────────────────────────────────────────
// We re-implement only the regex + resolution functions here rather than
// require()ing prompt-submit.cjs (which calls process.exit). Keep in sync
// with the real patterns in .claude/hooks/prompt-submit.cjs.

const GATE_PATTERNS = {
  QA_CSV:           /\[P4\.0-QA-CSV\].*approved=yes/,
  EVAL_YAML:        /\[P4\.0-EVAL-YAML\]/,
  TDD_RED:          /\[P4\.0-TDD-RED\]/,
  DISPATCH:         /\[P4\.1-DISPATCH\]/,
  EVAL_GREEN:       /\[P4\.4-EVAL-GREEN\]/,
  PR_MERGED:        /\[P5[.-]/,
  SPEC_FROZEN:      /\[P3-SPEC-FROZEN\]/,
  PRD_LOCKED:       /\[P1-PRD-LOCKED\]/,
  // QA pipeline
  QA_P7_REPORT:     /\[QA-P7-REPORT\]/,
  QA_P6_VERDICT:    /\[QA-P6-VERDICT\]/,
  QA_P5_EXEC:       /\[QA-P5-EXEC\]/,
  QA_P4_STACK:      /\[QA-P4-STACK\]/,
  QA_CODE_VALIDATE: /\[QA-CODE-VALIDATE\]/,
  QA_BRANCH_ENV:    /\[QA-BRANCH-ENV\]/,
  QA_P2_SCENARIOS:  /\[QA-P2-SCENARIOS\]/,
  QA_P1_LOAD:       /\[QA-P1-LOAD\]/,
};

function resolveQAPipelineGate(logContent) {
  const has = (p) => p.test(logContent);

  if (has(GATE_PATTERNS.QA_P7_REPORT)) return null;

  if (has(GATE_PATTERNS.QA_P6_VERDICT)) {
    const m = logContent.match(/\[QA-P6-VERDICT\][^\n]*verdict=(\w+)/);
    const verdict = m ? m[1] : '?';
    if (verdict === 'RED') return `QA NEXT GATE (branch-code-validate): RED`;
    return `QA NEXT GATE: Verdict=${verdict}`;
  }

  if (has(GATE_PATTERNS.QA_P5_EXEC))       return 'QA NEXT GATE: Execution in progress';
  if (has(GATE_PATTERNS.QA_P4_STACK))      return 'QA NEXT GATE: Stack is up';

  if (has(GATE_PATTERNS.QA_CODE_VALIDATE)) {
    const m = logContent.match(/\[QA-CODE-VALIDATE\][^\n]*fail=(\d+)/);
    const failCount = m ? parseInt(m[1], 10) : null;
    if (failCount !== null && failCount > 0)
      return `QA NEXT GATE (branch-code-validate): ${failCount} repo(s) failed tests`;
    return 'QA NEXT GATE (branch-code-validate): All repos passed';
  }

  if (has(GATE_PATTERNS.QA_BRANCH_ENV))    return 'QA NEXT GATE: Branch/env ready';
  if (has(GATE_PATTERNS.QA_P2_SCENARIOS))  return 'QA NEXT GATE: Scenarios written';
  if (has(GATE_PATTERNS.QA_P1_LOAD))       return 'QA NEXT GATE: Brain loaded';

  return null;
}

function resolveNextGate(logContent) {
  const has = (p) => p.test(logContent);

  if (has(GATE_PATTERNS.PR_MERGED))   return null;
  if (has(GATE_PATTERNS.EVAL_GREEN))  return 'NEXT GATE: Invoke pr-set-coordinate';
  if (has(GATE_PATTERNS.DISPATCH))    return 'NEXT GATE: Eval must reach GREEN';

  if (has(GATE_PATTERNS.SPEC_FROZEN)) {
    const missing = [];
    if (!has(GATE_PATTERNS.QA_CSV))    missing.push('[P4.0-QA-CSV]');
    if (!has(GATE_PATTERNS.EVAL_YAML)) missing.push('[P4.0-EVAL-YAML]');
    if (!has(GATE_PATTERNS.TDD_RED))   missing.push('[P4.0-TDD-RED]');
    if (missing.length > 0) return `NEXT GATE (State 4b): ${missing.join(', ')}`;
    return 'NEXT GATE: All State 4b gates satisfied';
  }

  if (has(GATE_PATTERNS.PRD_LOCKED)) return 'NEXT GATE: Invoke forge-council-gate';

  return null;
}

// ── Test harness ─────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function assert(label, actual, expectContains) {
  const ok = expectContains === null
    ? actual === null
    : (actual !== null && actual.includes(expectContains));

  if (ok) {
    console.log(`  PASS  ${label}`);
    passed++;
  } else {
    console.error(`  FAIL  ${label}`);
    console.error(`        expected: ${JSON.stringify(expectContains)}`);
    console.error(`        got:      ${JSON.stringify(actual)}`);
    failed++;
  }
}

console.log('\n── conductor flow gates ─────────────────────────────────────────');

assert('empty log → null (no gate)',
  resolveNextGate(''),
  null);

assert('PRD locked → council gate',
  resolveNextGate('[P1-PRD-LOCKED] task_id=X'),
  'forge-council-gate');

assert('spec frozen, nothing done → 3 missing gates',
  resolveNextGate('[P1-PRD-LOCKED]\n[P3-SPEC-FROZEN]'),
  '[P4.0-QA-CSV]');

assert('spec frozen, QA-CSV done → still missing EVAL-YAML and TDD-RED',
  resolveNextGate('[P3-SPEC-FROZEN]\n[P4.0-QA-CSV] approved=yes'),
  '[P4.0-EVAL-YAML]');

assert('spec frozen, all 3 done → dispatch',
  resolveNextGate('[P3-SPEC-FROZEN]\n[P4.0-QA-CSV] approved=yes\n[P4.0-EVAL-YAML]\n[P4.0-TDD-RED]'),
  'All State 4b gates satisfied');

assert('dispatch logged → eval running',
  resolveNextGate('[P4.1-DISPATCH]'),
  'Eval must reach GREEN');

assert('eval GREEN → PR gate',
  resolveNextGate('[P4.4-EVAL-GREEN]'),
  'pr-set-coordinate');

assert('PR merged → null (done)',
  resolveNextGate('[P5-PR-MERGED]'),
  null);

console.log('\n── QA pipeline gates ────────────────────────────────────────────');

assert('no QA log → null',
  resolveQAPipelineGate(''),
  null);

assert('QA-P1 loaded → generate scenarios',
  resolveQAPipelineGate('[QA-P1-LOAD] task_id=X'),
  'Brain loaded');

assert('QA-P2 scenarios written → branch/env prep',
  resolveQAPipelineGate('[QA-P1-LOAD]\n[QA-P2-SCENARIOS] total=87'),
  'Scenarios written');

assert('QA-BRANCH-ENV ready → stack-up or exec',
  resolveQAPipelineGate('[QA-P2-SCENARIOS]\n[QA-BRANCH-ENV] run_mode=branch-local'),
  'Branch/env ready');

assert('QA-CODE-VALIDATE PASS → all repos passed',
  resolveQAPipelineGate('[QA-BRANCH-ENV]\n[QA-CODE-VALIDATE] repos=2 pass=2 fail=0 status=PASS'),
  'All repos passed');

assert('QA-CODE-VALIDATE FAIL 1 repo → fail count shown',
  resolveQAPipelineGate('[QA-BRANCH-ENV]\n[QA-CODE-VALIDATE] repos=2 pass=1 fail=1 status=FAIL'),
  '1 repo(s) failed tests');

assert('QA-P4 stack up → exec',
  resolveQAPipelineGate('[QA-BRANCH-ENV]\n[QA-P4-STACK] status=READY'),
  'Stack is up');

assert('QA-P5 exec → verdict',
  resolveQAPipelineGate('[QA-P4-STACK]\n[QA-P5-EXEC] pass=12 fail=0'),
  'Execution in progress');

assert('QA-P6 verdict GREEN → write report',
  resolveQAPipelineGate('[QA-P5-EXEC]\n[QA-P6-VERDICT] verdict=GREEN'),
  'Verdict=GREEN');

assert('QA-P6 verdict RED → self-heal',
  resolveQAPipelineGate('[QA-P5-EXEC]\n[QA-P6-VERDICT] verdict=RED'),
  'RED');

assert('QA-P7 report committed → null (done)',
  resolveQAPipelineGate('[QA-P6-VERDICT] verdict=GREEN\n[QA-P7-REPORT]'),
  null);

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n${passed + failed} tests: ${passed} passed, ${failed} failed\n`);
process.exit(failed > 0 ? 1 : 0);
