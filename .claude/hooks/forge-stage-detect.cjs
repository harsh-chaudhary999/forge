#!/usr/bin/env node
/**
 * Forge conductor.log → stage stub name (intake | council | build | eval | pr).
 * Also exports brain path helpers and log discovery: `findMostRecentConductorLog`,
 * `findMostRecentQAPipelineLog` (shared by session-start.cjs and prompt-submit.cjs).
 * Used by session-start.cjs in this directory; run test-forge-stage-detect.cjs to verify.
 *
 * Rule: take the LAST [P…] phase marker in the log (document order), then map it.
 * Historical markers earlier in the file do not override newer state.
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

/** @returns {string|null} e.g. "[P4.1-DISPATCH]" or null */
function findLastPhaseMarker(logContent) {
  if (!logContent || typeof logContent !== 'string') return null;
  const matches = logContent.match(/\[P[0-9][^\]\s]*\]/g);
  if (!matches || matches.length === 0) return null;
  return matches[matches.length - 1];
}

/**
 * @param {string|null} marker
 * @returns {'intake'|'council'|'build'|'eval'|'pr'}
 */
function markerToStage(marker) {
  if (!marker) return 'intake';
  const upper = marker.toUpperCase();

  if (/^\[P5/.test(upper)) return 'pr';

  if (upper.includes('P4.4-EVAL-GREEN')) return 'pr';

  if (/^\[P4\.4/i.test(marker)) return 'eval';

  if (upper.includes('P4.1-DISPATCH')) return 'eval';

  if (/^\[P4\.0/i.test(marker)) return 'build';

  if (upper.includes('P3-SPEC-FROZEN') || /\[P3\.5/i.test(marker)) return 'build';

  if (/^\[P3/i.test(marker)) return 'council';

  if (/^\[P2/i.test(marker)) return 'council';

  if (/^\[P1/i.test(marker)) return 'intake';

  return 'intake';
}

/**
 * @param {string} logContent full conductor.log text
 * @returns {'intake'|'council'|'build'|'eval'|'pr'}
 */
function detectStageFromLogContent(logContent) {
  const marker = findLastPhaseMarker(logContent);
  return markerToStage(marker);
}

/**
 * Returns candidate brain root paths, checked in order:
 * FORGE_BRAIN env → FORGE_BRAIN_PATH env → ~/forge/brain.
 * @returns {string[]}
 */
function forgeBrainSearchPaths() {
  const out = [];
  const seen = new Set();
  for (const key of ['FORGE_BRAIN', 'FORGE_BRAIN_PATH']) {
    const s = process.env[key] && String(process.env[key]).trim();
    if (!s) continue;
    const abs = path.resolve(s);
    if (!seen.has(abs)) { seen.add(abs); out.push(abs); }
  }
  out.push(path.join(os.homedir(), 'forge', 'brain'));
  return out;
}

/**
 * Returns the path of the most recently modified conductor.log under
 * brainPath/prds/*, or null if none found.
 * @param {string} brainPath
 * @returns {string|null}
 */
function findMostRecentConductorLog(brainPath) {
  const prdsDir = path.join(brainPath, 'prds');
  if (!fs.existsSync(prdsDir)) return null;
  let mostRecentLog = null;
  let mostRecentMtime = 0;
  try {
    for (const taskDir of fs.readdirSync(prdsDir)) {
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
 * Resolves `brainPath/prds/<task-id>/qa-pipeline.log` (standalone QA /qa-run flow).
 * Same scoping as `findMostRecentConductorLog`: prefer `FORGE_TASK_ID` or
 * `FORGE_PRD_TASK_ID` when the scoped file exists; else newest mtime under prds/*.
 * @param {string} brainPath
 * @returns {string|null}
 */
function findMostRecentQAPipelineLog(brainPath) {
  const prdsDir = path.join(brainPath, 'prds');
  if (!fs.existsSync(prdsDir)) return null;

  const debug = (m) => {
    if (process.env.FORGE_HOOKS_DEBUG === '1') console.error(`[qa-pipeline.log] ${m}`);
  };

  const envTaskId = process.env.FORGE_TASK_ID || process.env.FORGE_PRD_TASK_ID;
  if (envTaskId) {
    const scopedLog = path.join(prdsDir, envTaskId, 'qa-pipeline.log');
    if (fs.existsSync(scopedLog)) {
      debug(`scoped by FORGE_TASK_ID=${envTaskId} → ${scopedLog}`);
      return scopedLog;
    }
  }

  let best = null;
  try {
    for (const taskId of fs.readdirSync(prdsDir)) {
      const logPath = path.join(prdsDir, taskId, 'qa-pipeline.log');
      if (!fs.existsSync(logPath)) continue;
      const mtime = fs.statSync(logPath).mtimeMs;
      if (!best || mtime > best.mtime) best = { path: logPath, mtime };
    }
  } catch (e) {
    debug(`scan error: ${e.message}`);
  }
  if (best) {
    debug(`mtime fallback → ${best.path} (set FORGE_TASK_ID for deterministic scoping)`);
    return best.path;
  }
  return null;
}

module.exports = {
  findLastPhaseMarker,
  markerToStage,
  detectStageFromLogContent,
  forgeBrainSearchPaths,
  findMostRecentConductorLog,
  findMostRecentQAPipelineLog,
};
