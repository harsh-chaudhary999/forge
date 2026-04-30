#!/usr/bin/env node
'use strict';

const assert = require('assert');
const {
  findLastPhaseMarker,
  markerToStage,
  detectStageFromLogContent,
  findMostRecentQAPipelineLog,
} = require('./forge-stage-detect.cjs');

function test(name, fn) {
  try {
    fn();
    console.log(`ok: ${name}`);
  } catch (e) {
    console.error(`FAIL: ${name}`, e.message);
    process.exit(1);
  }
}

test('last marker wins over older P4.4 in same log', () => {
  const log = `[P1-INTAKE] start\n[P4.4-EVAL-RED] fail\n[P4.1-DISPATCH] go\n`;
  assert.strictEqual(findLastPhaseMarker(log), '[P4.1-DISPATCH]');
  assert.strictEqual(detectStageFromLogContent(log), 'eval');
});

test('P4.4-EVAL-GREEN maps to pr', () => {
  assert.strictEqual(markerToStage('[P4.4-EVAL-GREEN]'), 'pr');
  assert.strictEqual(detectStageFromLogContent('x\n[P4.4-EVAL-GREEN]\n'), 'pr');
});

test('P4.4-EVAL-RED maps to eval not pr', () => {
  assert.strictEqual(markerToStage('[P4.4-EVAL-RED]'), 'eval');
});

test('P4.0 maps to build', () => {
  assert.strictEqual(markerToStage('[P4.0-EVAL-YAML]'), 'build');
});

test('P5 maps to pr', () => {
  assert.strictEqual(markerToStage('[P5.0-MERGE]'), 'pr');
});

test('no markers defaults intake', () => {
  assert.strictEqual(detectStageFromLogContent('no phase tags here\n'), 'intake');
});

test('P3-SPEC-FROZEN build', () => {
  assert.strictEqual(markerToStage('[P3-SPEC-FROZEN]'), 'build');
});

test('findMostRecentQAPipelineLog is exported (scoping lives with findMostRecentConductorLog)', () => {
  assert.strictEqual(typeof findMostRecentQAPipelineLog, 'function');
  assert.strictEqual(findMostRecentQAPipelineLog('/nonexistent-brain-xyz-12345'), null);
});

console.log('forge-stage-detect: all tests passed');
