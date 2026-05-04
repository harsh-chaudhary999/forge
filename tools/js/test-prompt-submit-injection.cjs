#!/usr/bin/env node
/**
 * Unit tests for shouldSuppressGateInjectionPure (.claude/hooks/prompt-submit-injection.cjs).
 *
 * Run: node tools/js/test-prompt-submit-injection.cjs
 */

'use strict';

const path = require('path');
const assert = require('assert');

const { shouldSuppressGateInjectionPure } = require(
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

test('disable injection → suppress regardless of logs', () => {
  assert.strictEqual(
    shouldSuppressGateInjectionPure({
      injectionDisabled: true,
      anyBrainRootExists: true,
      taskIdEnvSet: false,
      conductorLogBodies: [ACTIVE],
    }),
    true,
  );
});

test('no brain root → suppress', () => {
  assert.strictEqual(
    shouldSuppressGateInjectionPure({
      injectionDisabled: false,
      anyBrainRootExists: false,
      taskIdEnvSet: false,
      conductorLogBodies: [MERGED],
    }),
    true,
  );
});

test('no conductor bodies → do not suppress (still show static gates)', () => {
  assert.strictEqual(
    shouldSuppressGateInjectionPure({
      injectionDisabled: false,
      anyBrainRootExists: true,
      taskIdEnvSet: false,
      conductorLogBodies: [],
    }),
    false,
  );
});

test('unscoped: most-recent-done false-positive — one merged, one active → do not suppress', () => {
  assert.strictEqual(
    shouldSuppressGateInjectionPure({
      injectionDisabled: false,
      anyBrainRootExists: true,
      taskIdEnvSet: false,
      conductorLogBodies: [MERGED, ACTIVE],
    }),
    false,
  );
});

test('unscoped: all merged → suppress', () => {
  assert.strictEqual(
    shouldSuppressGateInjectionPure({
      injectionDisabled: false,
      anyBrainRootExists: true,
      taskIdEnvSet: false,
      conductorLogBodies: [MERGED, MERGED],
    }),
    true,
  );
});

test('scoped: primary body merged → suppress', () => {
  assert.strictEqual(
    shouldSuppressGateInjectionPure({
      injectionDisabled: false,
      anyBrainRootExists: true,
      taskIdEnvSet: true,
      conductorLogBodies: [MERGED],
    }),
    true,
  );
});

test('scoped: primary body active → do not suppress', () => {
  assert.strictEqual(
    shouldSuppressGateInjectionPure({
      injectionDisabled: false,
      anyBrainRootExists: true,
      taskIdEnvSet: true,
      conductorLogBodies: [ACTIVE],
    }),
    false,
  );
});

console.log('prompt-submit-injection: all tests passed');
