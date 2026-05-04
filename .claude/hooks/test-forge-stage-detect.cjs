#!/usr/bin/env node
'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const {
  findLastPhaseMarker,
  markerToStage,
  detectStageFromLogContent,
  findMostRecentConductorLog,
  loadConductorLogBundle,
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
  assert.strictEqual(markerToStage('[P4.0-SEMANTIC-EVAL]'), 'build');
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

test('findMostRecentConductorLog prefers FORGE_TASK_ID scoped path over newer mtime', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'forge-brain-'));
  try {
    fs.mkdirSync(path.join(tmp, 'prds', 'task-a'), { recursive: true });
    fs.mkdirSync(path.join(tmp, 'prds', 'task-b'), { recursive: true });
    const logA = path.join(tmp, 'prds', 'task-a', 'conductor.log');
    const logB = path.join(tmp, 'prds', 'task-b', 'conductor.log');
    fs.writeFileSync(logA, '[P1]\n', 'utf-8');
    fs.writeFileSync(logB, '[P1]\n', 'utf-8');
    const sb = fs.statSync(logB);
    const future = new Date(sb.mtimeMs + 60_000);
    fs.utimesSync(logB, future, future);
    const prevT = process.env.FORGE_TASK_ID;
    const prevP = process.env.FORGE_PRD_TASK_ID;
    try {
      process.env.FORGE_TASK_ID = 'task-a';
      delete process.env.FORGE_PRD_TASK_ID;
      assert.strictEqual(findMostRecentConductorLog(tmp), logA);
    } finally {
      if (prevT === undefined) delete process.env.FORGE_TASK_ID;
      else process.env.FORGE_TASK_ID = prevT;
      if (prevP === undefined) delete process.env.FORGE_PRD_TASK_ID;
      else process.env.FORGE_PRD_TASK_ID = prevP;
    }
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test('loadConductorLogBundle matches scoped path and reads once', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'forge-bundle-'));
  try {
    fs.mkdirSync(path.join(tmp, 'prds', 'scoped-id'), { recursive: true });
    const scoped = path.join(tmp, 'prds', 'scoped-id', 'conductor.log');
    fs.writeFileSync(scoped, '[P1]\n', 'utf-8');
    const prevT = process.env.FORGE_TASK_ID;
    const prevP = process.env.FORGE_PRD_TASK_ID;
    try {
      process.env.FORGE_TASK_ID = 'scoped-id';
      delete process.env.FORGE_PRD_TASK_ID;
      const b = loadConductorLogBundle(tmp);
      assert.strictEqual(b.primaryPath, scoped);
      assert.strictEqual(b.entries.length, 1);
      assert.strictEqual(b.primaryContent.trim(), '[P1]');
    } finally {
      if (prevT === undefined) delete process.env.FORGE_TASK_ID;
      else process.env.FORGE_TASK_ID = prevT;
      if (prevP === undefined) delete process.env.FORGE_PRD_TASK_ID;
      else process.env.FORGE_PRD_TASK_ID = prevP;
    }
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

console.log('forge-stage-detect: all tests passed');
