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
  lastTerminologyOpen,
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

function assertAll(label, actual, substrings) {
  const miss = substrings.find((s) => actual == null || !String(actual).includes(s));
  if (!miss) {
    console.log(`  PASS  ${label}`);
    passed++;
  } else {
    console.error(`  FAIL  ${label}`);
    console.error(`        expected all of: ${JSON.stringify(substrings)}; missing: ${JSON.stringify(miss)}`);
    console.error(`        got: ${JSON.stringify(actual)}`);
    failed++;
  }
}

console.log('\n── conductor flow gates ─────────────────────────────────────────');

assert('empty log → null (no gate)',
  resolveNextGate(''),
  null);

assert('orphan [TERMINOLOGY] without pipeline markers (e.g. no [P1-PRD-LOCKED]) → null (terminology is not a standalone gate)',
  resolveNextGate('[TERMINOLOGY] task_id=orphan open_doubts=pending'),
  null);

assert('lastTerminologyOpen: single [TERMINOLOGY] line with pending → true (do not use any-line regex on full log)',
  lastTerminologyOpen('[TERMINOLOGY] task_id=foo file=present status=draft open_doubts=pending') ? 'OK' : 'NO',
  'OK');

assert('PRD + [TERMINOLOGY] open_doubts=pending → terminology gate (before council/freeze)',
  resolveNextGate('[P1-PRD-LOCKED] task_id=X\n[TERMINOLOGY] task_id=X file=present status=draft open_doubts=pending'),
  'Product terminology');

assert('PRD + [TERMINOLOGY] open_doubts=none → still council (no block)',
  resolveNextGate('[P1-PRD-LOCKED] task_id=X\n[TERMINOLOGY] task_id=X open_doubts=none'),
  'forge-council-gate');

assert('PRD + two [TERMINOLOGY] lines, last open_doubts=none → council (no stale-pending false positive)',
  resolveNextGate('[P1-PRD-LOCKED] task_id=X\n[TERMINOLOGY] task_id=X file=present open_doubts=pending\n[TERMINOLOGY] task_id=X file=present open_doubts=none'),
  'forge-council-gate');

assert('PRD locked → council gate (no [TERMINOLOGY] line)',
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

assertAll('spec frozen + TERMINOLOGY pending → State 4b + ALSO (both verified)',
  resolveNextGate('[P1-PRD-LOCKED]\n[P3-SPEC-FROZEN]\n[TERMINOLOGY] task_id=X file=present status=draft open_doubts=pending'),
  ['[P4.0-QA-CSV]', 'ALSO: [TERMINOLOGY]']);

assert('spec frozen, all 4b, two [TERMINOLOGY] last none → no ALSO (no false positive from earlier pending)',
  resolveNextGate(
    '[P3-SPEC-FROZEN]\n[P4.0-QA-CSV] approved=yes\n[P4.0-EVAL-YAML]\n[P4.0-TDD-RED]\n[TERMINOLOGY] first open_doubts=pending\n[TERMINOLOGY] task_id=X file=present open_doubts=none',
  ),
  'All State 4b gates satisfied',
);

const doubleLog = 'All 4b done, last line is none, but legacy regex would also match first pending: ';
assert(
  `${doubleLog} lastTerminologyOpen is false`,
  lastTerminologyOpen(
    '[TERMINOLOGY] open_doubts=pending\n[TERMINOLOGY] open_doubts=none',
  )
    ? 'BAD'
    : 'OK',
  'OK',
);
assert(
  `${doubleLog} first line none, last pending is open`,
  lastTerminologyOpen('[TERMINOLOGY] open_doubts=none\n[TERMINOLOGY] open_doubts=pending') ? 'OK' : 'BAD',
  'OK',
);

assert(
  'lastTerminologyOpen: hand-edit quoted form open_doubts="pending"',
  lastTerminologyOpen('[TERMINOLOGY] task_id=x open_doubts="pending"') ? 'OK' : 'NO',
  'OK',
);

assert('spec frozen, all 4b done, TERMINOLOGY pending (single line) → dispatch line + ALSO terminology',
  resolveNextGate('[P3-SPEC-FROZEN]\n[P4.0-QA-CSV] approved=yes\n[P4.0-EVAL-YAML]\n[P4.0-TDD-RED]\n[TERMINOLOGY] task_id=X file=present open_doubts=pending'),
  'ALSO: [TERMINOLOGY]');

assert('dispatch logged → eval running',
  resolveNextGate('[P4.1-DISPATCH]'),
  'Eval must reach GREEN');

assertAll('DISPATCH + last [TERMINOLOGY] pending → eval hint + ALSO (pre-PR framing, not "ship")',
  resolveNextGate('[P4.1-DISPATCH]\n[TERMINOLOGY] task_id=X open_doubts=pending'),
  ['Eval must reach GREEN', 'ALSO: [TERMINOLOGY]', 'before PRs are raised'],
);

assert('eval GREEN → PR gate',
  resolveNextGate('[P4.4-EVAL-GREEN]'),
  'pr-set-coordinate');

assertAll('EVAL_GREEN + last [TERMINOLOGY] pending → pr-set + ALSO (terminology not silent pre-PR)',
  resolveNextGate('[P4.4-EVAL-GREEN]\n[TERMINOLOGY] task_id=X open_doubts=pending'),
  ['pr-set-coordinate', 'ALSO: [TERMINOLOGY]'],
);

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

assert('QA-P2 scenarios written → branch/env prep (incl. branch-code-validate in hint)',
  resolveQAPipelineGate('[QA-P1-LOAD]\n[QA-P2-SCENARIOS] total=87'),
  'branch-code-validate');

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
