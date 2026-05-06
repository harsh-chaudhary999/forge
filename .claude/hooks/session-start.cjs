#!/usr/bin/env node

/**
 * session-start.cjs
 *
 * MANDATORY HOOK (D17)
 * Fires when Claude Code session starts, /clear, or context compacts
 * Reads using-forge/SKILL.md and inlines it as additionalContext
 *
 * Stage-aware injection:
 * If FORGE_BRAIN, FORGE_BRAIN_PATH, or ~/forge/brain exists and contains a conductor.log,
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
 *   FORGE_BRAIN / FORGE_BRAIN_PATH — brain root override (either name)
 *   FORGE_TASK_ID / FORGE_PRD_TASK_ID — task-scoped conductor.log
 *   FORGE_PREAMBLE_TIER       — 1–4; if set, overrides. If unset: reads ~/.forge/.active-skill-tier
 *     (single line 1–4); else parses `preamble-tier` from skills/<name>/SKILL.md for /.active-skill.
 *     After a SKILL.md parse, this hook writes ~/.forge/.active-skill-tier so the next session
 *     avoids reading the full SKILL.md (pair with ~/.forge/.active-skill).
 *   FORGE_SUPPRESS_MULTI_TASK_WARN=1 — always skip the multi-task conductor.log stderr WARN
 *   ~/.forge/.multi-task-warned      — after the first unscoped multi-log WARN, this file is written;
 *     subsequent session starts do not repeat the warning
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

const {
  detectStageFromLogContent,
  findLastPhaseMarker,
  forgeBrainSearchPaths,
  collectConductorLogIndex,
} = require(path.join(__dirname, 'forge-stage-detect.cjs'));
// Primary path from `collectConductorLogIndex` matches `loadConductorLogBundle` /
// `loadBrainPromptBundle` conductor selection — one stat pass per call here.

// Configuration
const SKILL_FILE = path.join(__dirname, '..', 'skills', 'using-forge', 'SKILL.md');
const STAGES_DIR = path.join(__dirname, '..', 'skills', 'using-forge', 'stages');
const PREAMBLE_DIR = path.join(__dirname, '..', 'skills', '_preamble');
const FORGE_RUNTIME_DIR = path.join(os.homedir(), '.forge');
const CANARY_FILE = path.join(FORGE_RUNTIME_DIR, '.canary');
const MULTI_TASK_WARN_SENTINEL = path.join(FORGE_RUNTIME_DIR, '.multi-task-warned');
const ACTIVE_SKILL_TIER_FILE = path.join(FORGE_RUNTIME_DIR, '.active-skill-tier');
const SKILL_SKILLS_DIR = path.join(__dirname, '..', 'skills');
const DEFAULT_PREAMBLE_TIER = 2;

/** @type {{ source: 'default' | 'env' | 'skill', tier: number, activeSkill: string | null }} */
let preambleTierMeta = { source: 'default', tier: DEFAULT_PREAMBLE_TIER, activeSkill: null };

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

/**
 * Reads preamble tier for ~/.forge/.active-skill: prefer ~/.forge/.active-skill-tier (one line),
 * else `preamble-tier` in skills/<name>/SKILL.md frontmatter.
 * @returns {{ tier: number, activeSkill: string } | null}
 */
function writeActiveSkillTierCache(tier) {
  try {
    if (!fs.existsSync(FORGE_RUNTIME_DIR)) {
      fs.mkdirSync(FORGE_RUNTIME_DIR, { recursive: true, mode: 0o700 });
    }
    fs.writeFileSync(ACTIVE_SKILL_TIER_FILE, `${tier}\n`, { encoding: 'utf-8', mode: 0o600 });
    log(`Wrote ${ACTIVE_SKILL_TIER_FILE} (preamble tier cache — pair with ~/.forge/.active-skill)`);
  } catch (e) {
    log(`Could not write ${ACTIVE_SKILL_TIER_FILE}: ${e.message}`);
  }
}

function resolvePreambleTierFromActiveSkill() {
  try {
    const p = path.join(FORGE_RUNTIME_DIR, '.active-skill');
    if (!fs.existsSync(p)) return null;
    const name = fs.readFileSync(p, 'utf-8').trim();
    if (!/^[a-zA-Z0-9_-]+$/.test(name)) return null;

    if (fs.existsSync(ACTIVE_SKILL_TIER_FILE)) {
      try {
        const line = fs.readFileSync(ACTIVE_SKILL_TIER_FILE, 'utf-8').trim().split(/\r?\n/)[0];
        const n = parseInt(line, 10);
        if (!Number.isNaN(n) && n >= 1 && n <= 4) {
          return { tier: Math.min(4, Math.max(1, n)), activeSkill: name };
        }
      } catch (_) {
        // fall through to SKILL.md
      }
    }

    const skillPath = path.join(SKILL_SKILLS_DIR, name, 'SKILL.md');
    if (!fs.existsSync(skillPath)) return null;
    const raw = fs.readFileSync(skillPath, 'utf-8');
    const fmMatch = raw.match(/^---\n([\s\S]*?)\n---/);
    if (!fmMatch) return null;
    const m = fmMatch[1].match(/^\s*preamble-tier:\s*(\d+)\s*$/m);
    if (!m) return null;
    const n = parseInt(m[1], 10);
    if (Number.isNaN(n)) return null;
    const tier = Math.min(4, Math.max(1, n));
    writeActiveSkillTierCache(tier);
    return { tier, activeSkill: name };
  } catch (_) {
    return null;
  }
}

function resolvePreambleTierWithMeta() {
  const raw = process.env.FORGE_PREAMBLE_TIER;
  if (raw !== undefined && String(raw).trim() !== '') {
    const n = parseInt(String(raw).trim(), 10);
    if (!Number.isNaN(n)) {
      const tier = Math.min(4, Math.max(1, n));
      preambleTierMeta = { source: 'env', tier, activeSkill: null };
      return tier;
    }
  }
  const fromSkill = resolvePreambleTierFromActiveSkill();
  if (fromSkill) {
    preambleTierMeta = { source: 'skill', tier: fromSkill.tier, activeSkill: fromSkill.activeSkill };
    return fromSkill.tier;
  }
  preambleTierMeta = { source: 'default', tier: DEFAULT_PREAMBLE_TIER, activeSkill: null };
  return DEFAULT_PREAMBLE_TIER;
}

function shouldEmitMultiTaskUnscopedWarn() {
  if (
    process.env.FORGE_SUPPRESS_MULTI_TASK_WARN &&
    String(process.env.FORGE_SUPPRESS_MULTI_TASK_WARN).trim() === '1'
  ) {
    return false;
  }
  try {
    if (fs.existsSync(MULTI_TASK_WARN_SENTINEL)) return false;
  } catch (_) {
    // treat as "may emit"
  }
  return true;
}

function acknowledgeMultiTaskUnscopedWarn() {
  try {
    if (!fs.existsSync(FORGE_RUNTIME_DIR)) {
      fs.mkdirSync(FORGE_RUNTIME_DIR, { recursive: true, mode: 0o700 });
    }
    fs.writeFileSync(MULTI_TASK_WARN_SENTINEL, `${new Date().toISOString()}\n`, {
      encoding: 'utf-8',
      mode: 0o600,
    });
  } catch (_) {
    // non-fatal
  }
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
      fs.mkdirSync(FORGE_RUNTIME_DIR, { recursive: true, mode: 0o700 });
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
 * Resolves conductor.log: FORGE_TASK_ID / FORGE_PRD_TASK_ID first, else mtime.
 * One `collectConductorLogIndex` pass supplies both the task count and the mtime winner.
 */
function resolveConductorLogPath(brainPath) {
  const { statEntries } = collectConductorLogIndex(brainPath);
  const nWithLog = statEntries.length;

  function primaryPathFromIndex() {
    if (statEntries.length === 0) return null;
    let best = statEntries[0];
    for (let i = 1; i < statEntries.length; i += 1) {
      if (statEntries[i].mtimeMs > best.mtimeMs) best = statEntries[i];
    }
    return best.path;
  }

  const taskIdRaw = process.env.FORGE_TASK_ID || process.env.FORGE_PRD_TASK_ID;
  if (taskIdRaw) {
    const taskId = String(taskIdRaw).trim();
    if (!/^[\w.-]+$/.test(taskId)) {
      log(`Ignoring invalid FORGE_TASK_ID/FORGE_PRD_TASK_ID: ${taskId}`);
    } else {
      const scoped = path.join(brainPath, 'prds', taskId, 'conductor.log');
      if (fs.existsSync(scoped)) {
        log(`conductor.log selection: task-scoped (FORGE_TASK_ID) → ${scoped}`);
        return scoped;
      }
      log(
        `FORGE_TASK_ID/FORGE_PRD_TASK_ID=${taskId} but missing ${scoped} — falling back to mtime heuristic`,
      );
      if (nWithLog > 1) {
        console.error(
          `[session-start] WARN: ${nWithLog} prds/*/conductor.log files exist; ` +
            `FORGE_TASK_ID points to a missing log — mtime fallback may pick the wrong task.`,
        );
      }
      const fb = primaryPathFromIndex();
      if (fb) {
        log(`conductor.log selection: mtime fallback → ${fb}`);
      }
      return fb;
    }
  } else if (nWithLog > 1 && shouldEmitMultiTaskUnscopedWarn()) {
    console.error(
      '[session-start] WARN: multiple prds/*/conductor.log files; FORGE_TASK_ID / ' +
        'FORGE_PRD_TASK_ID unset — stage injection follows newest mtime and may be wrong. ' +
        'Export FORGE_TASK_ID=<active-task-id>.',
    );
    acknowledgeMultiTaskUnscopedWarn();
  }

  const fallback = primaryPathFromIndex();
  if (fallback) {
    log(`conductor.log selection: mtime fallback → ${fallback}`);
  }
  return fallback;
}

function tryDetectStage() {
  const brainCandidates = forgeBrainSearchPaths();

  for (const brainPath of brainCandidates) {
    if (!fs.existsSync(brainPath)) continue;

    const logPath = resolveConductorLogPath(brainPath);
    if (!logPath) {
      log(`Brain found at ${brainPath} but no conductor.log — defaulting to intake`);
      return { stage: 'intake', logPath: null, logContent: null };
    }

    try {
      const logContent = fs.readFileSync(logPath, 'utf-8');
      const stage = detectStageFromLogContent(logContent);
      log(`conductor.log: ${logPath} → stage: ${stage}`);
      return { stage, logPath, logContent };
    } catch (e) {
      log(`Failed to read conductor.log: ${e.message}`);
    }
  }

  return { stage: null, logPath: null, logContent: null }; // no brain found — use full fallback
}

/**
 * Injected when a conductor.log exists — re-anchor after compact / reduce hallucination risk.
 * Pass logContent from tryDetectStage when available to avoid a second read.
 */
function buildResumeChecklist(logPath, logContent) {
  let lastMarker = '';
  try {
    const text =
      logContent !== undefined && logContent !== null ? logContent : fs.readFileSync(logPath, 'utf-8');
    lastMarker = findLastPhaseMarker(text) || '';
  } catch (_) {
    // omit marker line
  }
  const taskMatch = logPath.match(/prds[/\\]([^/\\]+)[/\\]conductor\.log$/);
  const taskId = taskMatch ? taskMatch[1] : 'TASK_ID';
  const markerLine = lastMarker
    ? `- **Last phase marker in this log:** ${lastMarker}\n`
    : '';
  return (
    `[Forge — resume / re-anchor]\n` +
    `- **Authoritative log for stage detection:** \`${logPath}\`\n` +
    markerLine +
    `- **Before substantive work:** Re-read \`~/forge/brain/prds/${taskId}/prd-locked.md\` and \`shared-dev-spec.md\` (if present); skim the **tail** of this \`conductor.log\`\n` +
    `- **Chat is not transport:** If something mattered only in a prior chat turn, it must live in brain files or you must ask the human to repeat it\n` +
    `- **Scan / graph stubs ≠ runtime truth:** Confirm APIs and flows with real source or tests before changing code\n\n` +
    `---\n\n`
  );
}

// ==================== Edge Cases & Fallback Paths ====================

// Edge Case 1: SKILL file doesn't exist
if (!fs.existsSync(SKILL_FILE)) {
  die(`using-forge/SKILL.md not found at ${SKILL_FILE}`);
}

try {
  const st = fs.statSync(SKILL_FILE);
  if (st.size === 0) {
    die(`using-forge/SKILL.md is empty. Cannot bootstrap.`);
  }
} catch (e) {
  if (e.code === 'ENOENT') {
    die(`using-forge/SKILL.md not found at ${SKILL_FILE}`);
  }
  die(`Cannot stat using-forge/SKILL.md: ${e.message}`);
}

/** Full using-forge bootstrap — load only when stage stub is missing or brain absent. */
function readUsingForgeSkillMd() {
  let skillContent = '';
  try {
    skillContent = fs.readFileSync(SKILL_FILE, 'utf-8');
  } catch (err) {
    die(`Cannot read using-forge/SKILL.md: ${err.message}`);
  }
  if (!skillContent || skillContent.trim().length === 0) {
    die(`using-forge/SKILL.md is empty. Cannot bootstrap.`);
  }
  return skillContent;
}

// ==================== Main Logic ====================

let contentToInject = '';
let stageLabel = 'full';
let activeLogPath = null;
let resumeLogContent = null;

try {
  const detected = tryDetectStage();
  const stage = detected.stage;
  activeLogPath = detected.logPath;
  resumeLogContent = detected.logContent;

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
        contentToInject = readUsingForgeSkillMd();
        stageLabel = 'full';
      }
    } else {
      log(`No stage file found for '${stage}' at ${stageFile} — falling back to full bootstrap`);
      contentToInject = readUsingForgeSkillMd();
      stageLabel = 'full';
    }
  } else {
    log('No brain found — using full Forge bootstrap');
    contentToInject = readUsingForgeSkillMd();
    stageLabel = 'full';
  }
} catch (e) {
  // Any detection error → fall back to full bootstrap silently
  log(`Stage detection error (non-fatal): ${e.message} — falling back to full bootstrap`);
  contentToInject = readUsingForgeSkillMd();
  stageLabel = 'full (fallback)';
}

// Generate session canary token for prompt injection detection
generateCanary();

// Prepend shared preamble to session context
const preambleTier = resolvePreambleTierWithMeta();
const preambleContent = loadPreamble(preambleTier);
const preamblePrefix = preambleContent
  ? `${preambleContent}\n\n---\n\n`
  : '';

const tierHint =
  preambleTierMeta.source === 'skill' && preambleTierMeta.activeSkill
    ? `\n\n*(Forge: preamble tier ${preambleTier} from active skill \`${preambleTierMeta.activeSkill}\` — see ~/.forge/.active-skill-tier or preamble-tier in SKILL.md; override with FORGE_PREAMBLE_TIER.)*\n`
    : '';

const stageNote = stageLabel !== 'full'
  ? `[Forge Session — Stage: ${stageLabel.toUpperCase()}]\n\n`
  : '';

const resumeBlock = activeLogPath ? buildResumeChecklist(activeLogPath, resumeLogContent) : '';

const criticalBlock = `<EXTREMELY_IMPORTANT>
${stageNote}${resumeBlock}${preamblePrefix}${contentToInject}
</EXTREMELY_IMPORTANT>`;

const output = {
  hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: criticalBlock + tierHint,
  },
};

process.stdout.write(JSON.stringify(output));

log(`✅ Forge bootstrap loaded [stage: ${stageLabel}]`);
log(`Injected size: ${contentToInject.length} chars`);

process.exit(0);
