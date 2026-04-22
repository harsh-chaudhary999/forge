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
 * Stage detection map (from conductor.log last marker):
 *   No log / [P1.*]         → intake
 *   [P2.*] / [P3.*]         → council (before spec freeze)
 *   [P3-SPEC-FROZEN] / [P3.5*] / [P4.0-*] → build
 *   [P4.1-DISPATCH] (no GREEN) → build (ongoing)
 *   [P4.4-EVAL-GREEN] / [P4.4-*] → eval → pr transition
 *   [P5.*]                  → pr
 *
 * Why this matters (Superpowers principle):
 * Every session must start with full Forge awareness. Without this inline,
 * you'll drift into unsafe patterns (skipping gates, rationalizing shortcuts).
 * This hook is the perimeter defense. It fires FIRST, before any other work.
 *
 * Cannot be skipped (this is a HARD-GATE):
 * - Rationalization: "I already know Forge, skip the boot"
 *   Truth: You drift. Pattern matching fails on new scenarios. Boot every time.
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
  try {
    if (!fs.existsSync(FORGE_RUNTIME_DIR)) {
      fs.mkdirSync(FORGE_RUNTIME_DIR, { recursive: true });
    }
    const token = 'FORGE_CANARY_' + crypto.randomBytes(4).toString('hex').toUpperCase();
    fs.writeFileSync(CANARY_FILE, token, 'utf-8');
    log(`Canary token generated and written to ${CANARY_FILE}`);
  } catch (e) {
    log(`Canary generation failed (non-fatal): ${e.message}`);
  }
}

// ==================== Stage Detection ====================

/**
 * Finds the most recently modified conductor.log across all PRD task dirs
 * in the given brain directory.
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
 * Maps conductor.log content to a pipeline stage name.
 * Returns: 'intake' | 'council' | 'build' | 'eval' | 'pr' | null
 */
function detectStage(logContent) {
  const lines = logContent.split('\n').filter(l => l.trim().length > 0);

  const has = (pattern) => lines.some(l => pattern.test(l));

  if (has(/\[P5[.-]/)) return 'pr';
  if (has(/\[P4\.4-EVAL-GREEN\]/) || has(/\[P4\.4-/)) return 'pr';
  // P4.1-DISPATCH with no GREEN = still in build/eval
  if (has(/\[P4\.1-DISPATCH\]/)) return 'eval';
  // State 4b gates (P4.0-*) = build phase
  if (has(/\[P4\.0-/)) return 'build';
  // P3-SPEC-FROZEN or P3.5 = build (spec just frozen, starting implementation)
  if (has(/\[P3-SPEC-FROZEN\]/) || has(/\[P3\.5/)) return 'build';
  // P3.* (council ongoing) or P2.* = council
  if (has(/\[P3[.-]/) || has(/\[P2[.-]/)) return 'council';
  // P1.* = intake
  if (has(/\[P1[.-]/)) return 'intake';

  // Log exists but no recognized markers — default to intake
  return 'intake';
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

    const logPath = findMostRecentConductorLog(brainPath);
    if (!logPath) {
      log(`Brain found at ${brainPath} but no conductor.log — defaulting to intake`);
      return 'intake';
    }

    try {
      const logContent = fs.readFileSync(logPath, 'utf-8');
      const stage = detectStage(logContent);
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
const preambleContent = loadPreamble(DEFAULT_PREAMBLE_TIER);
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
