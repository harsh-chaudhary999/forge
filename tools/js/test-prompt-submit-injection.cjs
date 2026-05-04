#!/usr/bin/env node
/**
 * Unit tests for shouldSuppressFromConductorMergeState (.claude/hooks/prompt-submit-injection.cjs).
 *
 * `FORGE_DISABLE_GATE_INJECTION` and missing brain are enforced in prompt-submit.cjs before
 * any filesystem reads — not covered here.
 *
 * Run: node tools/js/test-prompt-submit-injection.cjs
 */

'use strict';

const path = require('path');
const assert = require('assert');

const { shouldSuppressFromConductorMergeState } = require(
  path.join(__dirname, '..', '..', '.claude', 'hooks', 'prompt-submit-injection.cjs'),
);

function test(name, fn) {
  try {
    fn();
    console.log(`ok: ${name}`);
  } catch (e) {
    console.error(`FAIL: ${name}`, e.message);
    process.exit(1);
  }
}

const MERGED = '[P5-PR-MERGED] done\n';
const ACTIVE = '[P4.1-DISPATCH] go\n';

test('no conductor bodies → do not suppress (still show static gates)', () => {
  assert.strictEqual(shouldSuppressFromConductorMergeState(false, []), false);
});

test('unscoped: one merged, one active → do not suppress', () => {
  assert.strictEqual(shouldSuppressFromConductorMergeState(false, [MERGED, ACTIVE]), false);
});

test('unscoped: all merged → suppress', () => {
  assert.strictEqual(shouldSuppressFromConductorMergeState(false, [MERGED, MERGED]), true);
});

test('scoped: primary body merged → suppress', () => {
  assert.strictEqual(shouldSuppressFromConductorMergeState(true, [MERGED]), true);
});

test('scoped: primary body active → do not suppress', () => {
  assert.strictEqual(shouldSuppressFromConductorMergeState(true, [ACTIVE]), false);
});

console.log('prompt-submit-injection: all tests passed');
