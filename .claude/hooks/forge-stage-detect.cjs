#!/usr/bin/env node
/**
 * Forge conductor.log → stage stub name (intake | council | build | eval | pr).
 * Also exports brain path helpers shared by session-start.cjs and prompt-submit.cjs.
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

module.exports = {
  findLastPhaseMarker,
  markerToStage,
  detectStageFromLogContent,
  forgeBrainSearchPaths,
  findMostRecentConductorLog,
};
