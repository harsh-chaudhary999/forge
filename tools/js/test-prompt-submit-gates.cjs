#!/usr/bin/env node
/**
 * test-prompt-submit-gates.cjs
 *
 * Smoke-tests for resolveNextGate and resolveQAPipelineGate from
 * .claude/hooks/prompt-submit-gates.cjs (same module used by prompt-submit.cjs).
 *
 * Run:
 *   node tools/js/test-prompt-submit-gates.cjs
 *
 * Exits 0 on pass, 1 on any failure.
 */

'use strict';

const path = require('path');

const {
  resolveNextGate,
  resolveQAPipelineGate,
} = require(
  path.join(__dirname, '..', '..', '.claude', 'hooks', 'prompt-submit-gates.cjs')
);

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

console.log(`\n${passed + failed} tests: ${passed} passed, ${failed} failed\n`);
process.exit(failed > 0 ? 1 : 0);
