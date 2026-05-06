#!/usr/bin/env node
/**
 * Forge conductor.log → stage stub name (intake | council | build | eval | pr).
 * Also exports brain path helpers and log discovery: conductor (`collectConductorLogIndex`,
 * `loadConductorLogBundle`), QA pipeline (`collectQAPipelineLogIndex`, `findMostRecentQAPipelineLog`,
 * `loadQAPipelineLogBundle`), and `loadBrainPromptBundle` (single combined `prds/` scan for
 * UserPromptSubmit — conductor + primary qa-pipeline).
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
 * Stats every candidate conductor.log (scoped single path or all tasks).
 * Session-start uses this for path-only selection. `loadConductorLogBundle` shares these rules.
 * `loadBrainPromptBundle` uses `collectUnifiedPromptGateIndices` (one merged `prds/` scan + QA).
 * @param {string} brainPath
 * @returns {{ statEntries: Array<{ path: string, mtimeMs: number }> }}
 */
function collectConductorLogIndex(brainPath) {
  const prdsDir = path.join(brainPath, 'prds');
  if (!fs.existsSync(prdsDir)) return { statEntries: [] };

  const debug = (m) => {
    if (process.env.FORGE_HOOKS_DEBUG === '1') console.error(`[conductor.log] ${m}`);
  };

  const envTaskIdRaw = process.env.FORGE_TASK_ID || process.env.FORGE_PRD_TASK_ID;
  const envTaskId = envTaskIdRaw ? String(envTaskIdRaw).trim() : '';

  if (envTaskId) {
    const scopedLog = path.join(prdsDir, envTaskId, 'conductor.log');
    if (fs.existsSync(scopedLog)) {
      try {
        const stat = fs.statSync(scopedLog);
        debug(`scoped by FORGE_TASK_ID=${envTaskId} → ${scopedLog}`);
        return { statEntries: [{ path: scopedLog, mtimeMs: stat.mtimeMs }] };
      } catch (_) {
        return { statEntries: [] };
      }
    }
  }

  const statEntries = [];
  try {
    for (const taskDir of fs.readdirSync(prdsDir)) {
      const logPath = path.join(prdsDir, taskDir, 'conductor.log');
      if (!fs.existsSync(logPath)) continue;
      try {
        const stat = fs.statSync(logPath);
        statEntries.push({ path: logPath, mtimeMs: stat.mtimeMs });
      } catch (_) {}
    }
  } catch (_) {}
  return { statEntries };
}

/**
 * One pass per brain for UserPromptSubmit: same path selection as
 * `collectConductorLogIndex`, then reads each
 * log once so suppress + next-gate do not duplicate I/O.
 *
 * @param {string} brainPath
 * @returns {{ primaryPath: string|null, primaryContent: string|null, entries: Array<{path: string, content: string, mtimeMs: number}> }}
 */
function loadConductorLogBundle(brainPath) {
  const { statEntries } = collectConductorLogIndex(brainPath);
  if (statEntries.length === 0) {
    return { primaryPath: null, primaryContent: null, entries: [] };
  }

  const entries = [];
  for (const se of statEntries) {
    try {
      const content = fs.readFileSync(se.path, 'utf-8');
      entries.push({ path: se.path, content, mtimeMs: se.mtimeMs });
    } catch (_) {
      // skip unreadable
    }
  }
  if (entries.length === 0) {
    return { primaryPath: null, primaryContent: null, entries: [] };
  }

  let best = entries[0];
  for (let i = 1; i < entries.length; i += 1) {
    if (entries[i].mtimeMs > best.mtimeMs) best = entries[i];
  }
  return {
    primaryPath: best.path,
    primaryContent: best.content,
    entries,
  };
}

/**
 * Stats every candidate `qa-pipeline.log` (scoped one path or all tasks).
 * Shared by `findMostRecentQAPipelineLog` and `loadQAPipelineLogBundle` (one scan + one read).
 * @param {string} brainPath
 * @returns {{ statEntries: Array<{ path: string, mtimeMs: number }> }}
 */
function collectQAPipelineLogIndex(brainPath) {
  const prdsDir = path.join(brainPath, 'prds');
  if (!fs.existsSync(prdsDir)) return { statEntries: [] };

  const debug = (m) => {
    if (process.env.FORGE_HOOKS_DEBUG === '1') console.error(`[qa-pipeline.log] ${m}`);
  };

  const envTaskIdRaw = process.env.FORGE_TASK_ID || process.env.FORGE_PRD_TASK_ID;
  const envTaskId = envTaskIdRaw ? String(envTaskIdRaw).trim() : '';

  if (envTaskId) {
    const scopedLog = path.join(prdsDir, envTaskId, 'qa-pipeline.log');
    if (fs.existsSync(scopedLog)) {
      try {
        const st = fs.statSync(scopedLog);
        debug(`scoped by FORGE_TASK_ID=${envTaskId} → ${scopedLog}`);
        return { statEntries: [{ path: scopedLog, mtimeMs: st.mtimeMs }] };
      } catch (_) {
        return { statEntries: [] };
      }
    }
  }

  const statEntries = [];
  try {
    for (const taskId of fs.readdirSync(prdsDir)) {
      const logPath = path.join(prdsDir, taskId, 'qa-pipeline.log');
      if (!fs.existsSync(logPath)) continue;
      try {
        const mtime = fs.statSync(logPath).mtimeMs;
        statEntries.push({ path: logPath, mtimeMs: mtime });
      } catch (_) {}
    }
  } catch (e) {
    debug(`scan error: ${e.message}`);
  }
  return { statEntries };
}

/**
 * Resolves `brainPath/prds/<task-id>/qa-pipeline.log` (standalone QA /qa-run flow).
 * Same scoping as conductor logs: prefer `FORGE_TASK_ID` or
 * `FORGE_PRD_TASK_ID` when the scoped file exists; else newest mtime under prds/*.
 * @param {string} brainPath
 * @returns {string|null}
 */
function findMostRecentQAPipelineLog(brainPath) {
  const { statEntries } = collectQAPipelineLogIndex(brainPath);
  if (statEntries.length === 0) return null;
  let best = statEntries[0];
  for (let i = 1; i < statEntries.length; i += 1) {
    if (statEntries[i].mtimeMs > best.mtimeMs) best = statEntries[i];
  }
  if (process.env.FORGE_HOOKS_DEBUG === '1' && statEntries.length > 1) {
    console.error(`[qa-pipeline.log] mtime fallback → ${best.path} (set FORGE_TASK_ID for deterministic scoping)`);
  }
  return best.path;
}

/**
 * Primary QA pipeline log path + content — same selection as `findMostRecentQAPipelineLog`
 * but avoids a second directory scan before read (pairs with `collectQAPipelineLogIndex`).
 * @param {string} brainPath
 * @returns {{ primaryPath: string, primaryContent: string }|null}
 */
function loadQAPipelineLogBundle(brainPath) {
  const { statEntries } = collectQAPipelineLogIndex(brainPath);
  if (statEntries.length === 0) return null;
  let best = statEntries[0];
  for (let i = 1; i < statEntries.length; i += 1) {
    if (statEntries[i].mtimeMs > best.mtimeMs) best = statEntries[i];
  }
  try {
    const primaryContent = fs.readFileSync(best.path, 'utf-8');
    return { primaryPath: best.path, primaryContent };
  } catch (_) {
    return null;
  }
}

/**
 * One `readdir` of `prds/*` (when unscoped) collects both conductor and QA stat entries;
 * matches per-file scoping rules of `collectConductorLogIndex` + `collectQAPipelineLogIndex`.
 * @param {string} brainPath
 * @returns {{ conductorStatEntries: Array<{ path: string, mtimeMs: number }>, qaStatEntries: Array<{ path: string, mtimeMs: number }> }}
 */
function collectUnifiedPromptGateIndices(brainPath) {
  const prdsDir = path.join(brainPath, 'prds');
  if (!fs.existsSync(prdsDir)) return { conductorStatEntries: [], qaStatEntries: [] };

  const envTaskIdRaw = process.env.FORGE_TASK_ID || process.env.FORGE_PRD_TASK_ID;
  const envTaskId = envTaskIdRaw ? String(envTaskIdRaw).trim() : '';

  function scanAllConductors(out) {
    try {
      for (const taskDir of fs.readdirSync(prdsDir)) {
        const logPath = path.join(prdsDir, taskDir, 'conductor.log');
        if (!fs.existsSync(logPath)) continue;
        try {
          out.push({ path: logPath, mtimeMs: fs.statSync(logPath).mtimeMs });
        } catch (_) {}
      }
    } catch (_) {}
  }

  function scanAllBoth(condOut, qaOut) {
    try {
      for (const taskDir of fs.readdirSync(prdsDir)) {
        const cPath = path.join(prdsDir, taskDir, 'conductor.log');
        const qPath = path.join(prdsDir, taskDir, 'qa-pipeline.log');
        if (fs.existsSync(cPath)) {
          try {
            condOut.push({ path: cPath, mtimeMs: fs.statSync(cPath).mtimeMs });
          } catch (_) {}
        }
        if (fs.existsSync(qPath)) {
          try {
            qaOut.push({ path: qPath, mtimeMs: fs.statSync(qPath).mtimeMs });
          } catch (_) {}
        }
      }
    } catch (_) {}
  }

  const conductorStatEntries = [];
  const qaStatEntries = [];

  if (!envTaskId) {
    scanAllBoth(conductorStatEntries, qaStatEntries);
    return { conductorStatEntries, qaStatEntries };
  }

  const cScoped = path.join(prdsDir, envTaskId, 'conductor.log');
  const qScoped = path.join(prdsDir, envTaskId, 'qa-pipeline.log');

  let haveCond = false;
  if (fs.existsSync(cScoped)) {
    try {
      conductorStatEntries.push({ path: cScoped, mtimeMs: fs.statSync(cScoped).mtimeMs });
      haveCond = true;
    } catch (_) {}
  }
  let haveQa = false;
  if (fs.existsSync(qScoped)) {
    try {
      qaStatEntries.push({ path: qScoped, mtimeMs: fs.statSync(qScoped).mtimeMs });
      haveQa = true;
    } catch (_) {}
  }

  if (!haveCond && !haveQa) {
    scanAllBoth(conductorStatEntries, qaStatEntries);
  } else {
    if (!haveCond) scanAllConductors(conductorStatEntries);
    // Task-scoped (envTaskId set) but this task has no qa-pipeline.log: intentionally do nothing
    // for QA — do not scan other tasks' qa-pipeline.log (cross-task QA contamination was the bug).
    // There is no fallback branch here; qaStatEntries stays empty when haveQa is false.
  }

  return { conductorStatEntries, qaStatEntries };
}

/**
 * UserPromptSubmit: conductor bundle + primary qa-pipeline.log — **one** unified index pass per brain
 * (`collectUnifiedPromptGateIndices`), then reads conductor logs + primary QA body.
 * @param {string} brainPath
 * @returns {{ primaryPath: string|null, primaryContent: string|null, entries: Array<{path: string, content: string, mtimeMs: number}>, qaPrimaryPath: string|null, qaPrimaryContent: string|null }}
 */
function loadBrainPromptBundle(brainPath) {
  const { conductorStatEntries, qaStatEntries } = collectUnifiedPromptGateIndices(brainPath);

  const entries = [];
  for (const se of conductorStatEntries) {
    try {
      const content = fs.readFileSync(se.path, 'utf-8');
      entries.push({ path: se.path, content, mtimeMs: se.mtimeMs });
    } catch (_) {}
  }

  let primaryPath = null;
  let primaryContent = null;
  if (entries.length > 0) {
    let best = entries[0];
    for (let i = 1; i < entries.length; i += 1) {
      if (entries[i].mtimeMs > best.mtimeMs) best = entries[i];
    }
    primaryPath = best.path;
    primaryContent = best.content;
  }

  let qaPrimaryPath = null;
  let qaPrimaryContent = null;
  if (qaStatEntries.length > 0) {
    let qb = qaStatEntries[0];
    for (let i = 1; i < qaStatEntries.length; i += 1) {
      if (qaStatEntries[i].mtimeMs > qb.mtimeMs) qb = qaStatEntries[i];
    }
    try {
      qaPrimaryPath = qb.path;
      qaPrimaryContent = fs.readFileSync(qb.path, 'utf-8');
    } catch (_) {}
  }

  return {
    primaryPath,
    primaryContent,
    entries,
    qaPrimaryPath,
    qaPrimaryContent,
  };
}

module.exports = {
  findLastPhaseMarker,
  markerToStage,
  detectStageFromLogContent,
  forgeBrainSearchPaths,
  collectConductorLogIndex,
  loadConductorLogBundle,
  collectUnifiedPromptGateIndices,
  loadBrainPromptBundle,
  collectQAPipelineLogIndex,
  findMostRecentQAPipelineLog,
  loadQAPipelineLogBundle,
};
