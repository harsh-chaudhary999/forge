#!/usr/bin/env node

/**
 * session-start.cjs
 *
 * MANDATORY HOOK (D17)
 * Fires when Claude Code session starts, /clear, or context compacts
 * Reads using-forge/SKILL.md and inlines it as additionalContext
 *
 * Stage-aware injection:
 * If FORGE_BRAIN_PATH or ~/forge/brain exists and contains a conductor.log,
 * injects the stage-specific stub (skills/using-forge/stages/<stage>.md)
 * instead of the full using-forge/SKILL.md, reducing token use and improving
 * LLM attention on rules that matter for the current pipeline phase.
 *
 * Fallback: if stage detection fails for any reason, falls back to the full
 * using-forge/SKILL.md — existing behavior is preserved unconditionally.
 *
 * Conductor log selection:
 *   - If FORGE_TASK_ID or FORGE_PRD_TASK_ID is set and brain/prds/<id>/conductor.log
 *     exists → use that file (recommended when multiple tasks exist).
 *   - Else → use the most recently modified per-task conductor.log under prds/ (mtime
 *     heuristic; can pick the wrong task if another log was touched recently — set FORGE_TASK_ID).
 *
 * Stage detection (LAST phase marker in the chosen log wins):
 *   Parse all tokens matching [P…] in document order; use the LAST one only.
 *   Map:
 *     [P5…]                    → pr
 *     [P4.4-EVAL-GREEN]        → pr (eval done; PR / merge phase)
 *     other [P4.4-…]           → eval (eval in flight or RED, etc.)
 *     [P4.1-DISPATCH]          → eval (per stages/eval.md)
 *     [P4.0-…]                 → build (State 4b prep)
 *     [P3-SPEC-FROZEN], [P3.5…] → build
 *     other [P3…], [P2…]       → council
 *     [P1…]                    → intake
 *   No recognizable marker     → intake
 *
 * Environment:
 *   FORGE_BRAIN_PATH          — brain root override
 *   FORGE_TASK_ID / FORGE_PRD_TASK_ID — task-scoped conductor.log
 *   FORGE_PREAMBLE_TIER       — 1–4 (default 2); missing tier file skips preamble slice
 *   FORGE_HOOKS_DEBUG=1       — stderr traces (selection + stage)
 *   FORGE_DISABLE_CANARY=1    — skip writing ~/.forge/.canary (pre-tool-use skips check too)
 *
 * Why this matters:
 * Every session must start with Forge awareness. This hook fires FIRST.
 *
 * Usage:
 *   This runs automatically via Claude Code session hook
 *   Requires: .claude/skills/using-forge/SKILL.md
 *
 * Cross-platform: works on Linux, macOS, Windows
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

const { detectStageFromLogContent } = require(path.join(__dirname, 'forge-stage-detect.cjs'));

// Configuration
const SKILL_FILE = path.join(__dirname, '..', 'skills', 'using-forge', 'SKILL.md');
const STAGES_DIR = path.join(__dirname, '..', 'skills', 'using-forge', 'stages');
const PREAMBLE_DIR = path.join(__dirname, '..', 'skills', '_preamble');
const FORGE_RUNTIME_DIR = path.join(os.homedir(), '.forge');
const CANARY_FILE = path.join(FORGE_RUNTIME_DIR, '.canary');
const DEFAULT_PREAMBLE_TIER = 2;

function log(message) {
  if (process.env.FORGE_HOOKS_DEBUG === '1') {
    console.error(`[session-start] ${message}`);
  }
}

function die(message) {
  console.error(`\n❌ FATAL: ${message}`);
  console.error(`\nSession cannot start without Forge bootstrap.`);
  console.error(`Fix: Check that .claude/skills/using-forge/SKILL.md exists.`);
  process.exit(1);
}

function resolvePreambleTier() {
  const raw = process.env.FORGE_PREAMBLE_TIER;
  if (raw === undefined || String(raw).trim() === '') {
    return DEFAULT_PREAMBLE_TIER;
  }
  const n = parseInt(String(raw).trim(), 10);
  if (Number.isNaN(n)) return DEFAULT_PREAMBLE_TIER;
  return Math.min(4, Math.max(1, n));
}

function loadPreamble(tier) {
  const preambleFile = path.join(PREAMBLE_DIR, `tier-${tier}.md`);
  if (!fs.existsSync(preambleFile)) {
    log(`Preamble tier-${tier}.md not found — skipping preamble injection`);
    return '';
  }
  try {
    return fs.readFileSync(preambleFile, 'utf-8');
  } catch (e) {
    log(`Cannot read preamble tier-${tier}: ${e.message} — skipping`);
    return '';
  }
}

function generateCanary() {
  const v = process.env.FORGE_DISABLE_CANARY;
  if (v && String(v).trim().toLowerCase() === '1') {
    log('FORGE_DISABLE_CANARY=1 — skipping canary generation');
    return;
  }
  try {
    if (!fs.existsSync(FORGE_RUNTIME_DIR)) {
      fs.mkdirSync(FORGE_RUNTIME_DIR, { recursive: true });
    }
    const token = 'FORGE_CANARY_' + crypto.randomBytes(16).toString('hex').toUpperCase();
    fs.writeFileSync(CANARY_FILE, token, { encoding: 'utf-8', mode: 0o600 });
    log(`Canary token generated and written to ${CANARY_FILE}`);
  } catch (e) {
    log(`Canary generation failed (non-fatal): ${e.message}`);
  }
}

// ==================== Stage Detection ====================

/**
 * Most recently modified conductor.log under brain/prds (each task subdir).
 */
function findMostRecentConductorLog(brainPath) {
  const prdsDir = path.join(brainPath, 'prds');
  if (!fs.existsSync(prdsDir)) return null;

  let mostRecentLog = null;
  let mostRecentMtime = 0;

  try {
    const taskDirs = fs.readdirSync(prdsDir);
    for (const taskDir of taskDirs) {
      const logPath = path.join(prdsDir, taskDir, 'conductor.log');
      if (!fs.existsSync(logPath)) continue;
      try {
        const stat = fs.statSync(logPath);
        if (stat.mtimeMs > mostRecentMtime) {
          mostRecentMtime = stat.mtimeMs;
          mostRecentLog = logPath;
        }
      } catch (_) {
        // skip unreadable stat
      }
    }
  } catch (_) {
    return null;
  }

  return mostRecentLog;
}

/**
 * Resolves conductor.log: FORGE_TASK_ID / FORGE_PRD_TASK_ID first, else mtime.
 */
function resolveConductorLogPath(brainPath) {
  const taskIdRaw = process.env.FORGE_TASK_ID || process.env.FORGE_PRD_TASK_ID;
  if (taskIdRaw) {
    const taskId = String(taskIdRaw).trim();
    const scoped = path.join(brainPath, 'prds', taskId, 'conductor.log');
    if (fs.existsSync(scoped)) {
      log(`conductor.log selection: task-scoped (FORGE_TASK_ID) → ${scoped}`);
      return scoped;
    }
    log(
      `FORGE_TASK_ID/FORGE_PRD_TASK_ID=${taskId} but missing ${scoped} — falling back to mtime heuristic`,
    );
  }
  const fallback = findMostRecentConductorLog(brainPath);
  if (fallback) {
    log(`conductor.log selection: mtime fallback → ${fallback}`);
  }
  return fallback;
}

/**
 * Attempts to detect the current pipeline stage from brain files.
 * Returns stage name or null if detection is not possible.
 */
function tryDetectStage() {
  const brainCandidates = [
    process.env.FORGE_BRAIN_PATH,
    path.join(process.env.HOME || '/root', 'forge', 'brain'),
  ].filter(Boolean);

  for (const brainPath of brainCandidates) {
    if (!fs.existsSync(brainPath)) continue;

    const logPath = resolveConductorLogPath(brainPath);
    if (!logPath) {
      log(`Brain found at ${brainPath} but no conductor.log — defaulting to intake`);
      return 'intake';
    }

    try {
      const logContent = fs.readFileSync(logPath, 'utf-8');
      const stage = detectStageFromLogContent(logContent);
      log(`conductor.log: ${logPath} → stage: ${stage}`);
      return stage;
    } catch (e) {
      log(`Failed to read conductor.log: ${e.message}`);
    }
  }

  return null; // no brain found — use full fallback
}

// ==================== Edge Cases & Fallback Paths ====================

// Edge Case 1: SKILL file doesn't exist
if (!fs.existsSync(SKILL_FILE)) {
  die(`using-forge/SKILL.md not found at ${SKILL_FILE}`);
}

// Edge Case 2: Cannot read SKILL file
let skillContent = '';
try {
  skillContent = fs.readFileSync(SKILL_FILE, 'utf-8');
} catch (e) {
  die(`Cannot read using-forge/SKILL.md: ${e.message}`);
}

// Edge Case 3: SKILL file is empty
if (!skillContent || skillContent.trim().length === 0) {
  die(`using-forge/SKILL.md is empty. Cannot bootstrap.`);
}

// ==================== Main Logic ====================

let contentToInject = skillContent; // default: full bootstrap
let stageLabel = 'full';

try {
  const stage = tryDetectStage();

  if (stage) {
    const stageFile = path.join(STAGES_DIR, `${stage}.md`);
    if (fs.existsSync(stageFile)) {
      const stageContent = fs.readFileSync(stageFile, 'utf-8');
      if (stageContent && stageContent.trim().length > 0) {
        contentToInject = stageContent;
        stageLabel = stage;
        log(`Stage-aware injection: ${stage}`);
      } else {
        log(`Stage file for '${stage}' is empty — falling back to full bootstrap`);
      }
    } else {
      log(`No stage file found for '${stage}' at ${stageFile} — falling back to full bootstrap`);
    }
  } else {
    log('No brain found — using full Forge bootstrap');
  }
} catch (e) {
  // Any detection error → fall back to full bootstrap silently
  log(`Stage detection error (non-fatal): ${e.message} — falling back to full bootstrap`);
  contentToInject = skillContent;
  stageLabel = 'full (fallback)';
}

// Generate session canary token for prompt injection detection
generateCanary();

// Prepend shared preamble to session context
const preambleTier = resolvePreambleTier();
const preambleContent = loadPreamble(preambleTier);
const preamblePrefix = preambleContent
  ? `${preambleContent}\n\n---\n\n`
  : '';

const stageNote = stageLabel !== 'full'
  ? `[Forge Session — Stage: ${stageLabel.toUpperCase()}]\n\n`
  : '';

const wrappedContent = `<EXTREMELY_IMPORTANT>
${stageNote}${preamblePrefix}${contentToInject}
</EXTREMELY_IMPORTANT>`;

const output = {
  hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: wrappedContent,
  },
};

process.stdout.write(JSON.stringify(output));

log(`✅ Forge bootstrap loaded [stage: ${stageLabel}]`);
log(`Injected size: ${contentToInject.length} chars (full: ${skillContent.length} chars)`);

process.exit(0);
