#!/usr/bin/env node

/**
 * forge-team-gates.cjs
 *
 * AGENT-TEAM GATE BRIDGE
 * Fires on TaskCreated / TaskCompleted / TeammateIdle — Claude Code agent-team
 * events (experimental: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1). These events only
 * fire when a team is active, so this hook is inert in ordinary sessions.
 *
 * Two layers:
 *   1. AUDIT (always, never blocks): append a structured, append-only line to the
 *      brain's team-events log so Forge's auditable trajectory covers team activity
 *      too. Task-scoped to prds/<FORGE_TASK_ID>/team-events.log when a task id is
 *      set, else <brain>/team-events.log. No brain on disk → no-op.
 *   2. ENFORCE (opt-in: FORGE_TEAM_GATES=strict|block|1): conservatively block events
 *      that contradict a Forge HARD-GATE, via exit code 2 + a stderr message naming
 *      the gate. OFF by default so it never surprises an experimental team.
 *
 * Exit semantics (per the agent-team hook contract — these events do NOT support
 * hookSpecificOutput.additionalContext; the lever is exit code):
 *   TaskCreated / TaskCompleted — exit 2 blocks the action, stderr is the feedback.
 *   TeammateIdle               — exit 2 keeps the teammate working, stderr is feedback.
 *   exit 0 always = allow.
 *
 * The strict-mode checks are deliberately conservative (only clear merge/ship claims
 * without brain evidence, or a teammate going idle on a RED eval) because a hook
 * cannot fully adjudicate a Forge gate from a task event — see docs/agent-teams.md.
 */

const fs = require('fs');
const path = require('path');

function debug(msg) {
  if (process.env.FORGE_HOOKS_DEBUG === '1') console.error(`[forge-team-gates] ${msg}`);
}

// Brain root candidates — env first (so an override always wins), then the shared
// resolver, then ~/forge/brain. First existing one wins.
function brainRoots() {
  const out = [];
  const env = process.env.FORGE_BRAIN || process.env.FORGE_BRAIN_PATH;
  if (env) out.push(env);
  try {
    const { forgeBrainSearchPaths } = require(path.join(__dirname, 'forge-stage-detect.cjs'));
    const paths = forgeBrainSearchPaths();
    if (Array.isArray(paths)) out.push(...paths);
  } catch (_) {
    /* shared resolver optional */
  }
  const home = process.env.HOME || process.env.USERPROFILE || '';
  if (home) out.push(path.join(home, 'forge', 'brain'));
  return out;
}

function firstExistingBrain() {
  for (const p of brainRoots()) {
    try {
      if (p && fs.existsSync(p)) return p;
    } catch (_) {
      /* ignore */
    }
  }
  return null;
}

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (_) {
    return '';
  }
}

// ── Parse the event payload ───────────────────────────────────────────────
const raw = readStdin();
let payload = {};
try {
  payload = raw ? JSON.parse(raw) : {};
} catch (_) {
  payload = {};
}
const eventKnown = !!payload.hook_event_name;
const event = payload.hook_event_name || 'TeammateIdle';
const blob = JSON.stringify(payload).toLowerCase();
const teammate = payload.teammate_name || payload.team_name || 'teammate';
const activeTask = (process.env.FORGE_TASK_ID || process.env.FORGE_PRD_TASK_ID || '').trim();

// ── Layer 1: audit (never blocks) ──────────────────────────────────────────
function audit() {
  const brain = firstExistingBrain();
  if (!brain) return;
  let logPath;
  if (activeTask) {
    const dir = path.join(brain, 'prds', activeTask);
    try {
      fs.mkdirSync(dir, { recursive: true });
    } catch (_) {
      /* ignore */
    }
    logPath = path.join(dir, 'team-events.log');
  } else {
    logPath = path.join(brain, 'team-events.log');
  }
  const marker = event.replace(/([a-z])([A-Z])/g, '$1-$2').toUpperCase(); // TaskCompleted → TASK-COMPLETED
  const line = `${nowIso()} [TEAM-${marker}] teammate=${teammate}\n`;
  try {
    fs.appendFileSync(logPath, line);
    debug(`audited ${event} -> ${logPath}`);
  } catch (e) {
    debug(`audit failed: ${e.message}`);
  }
}

// ── Layer 2: enforce (opt-in) ──────────────────────────────────────────────
function strictMode() {
  const v = String(process.env.FORGE_TEAM_GATES || '').trim().toLowerCase();
  return v === 'strict' || v === 'block' || v === '1';
}

function block(message) {
  process.stderr.write(`[forge-team-gates] ${message}\n`);
  process.exit(2);
}

function anyConductorHas(brain, marker) {
  const prds = path.join(brain, 'prds');
  try {
    for (const d of fs.readdirSync(prds)) {
      const lp = path.join(prds, d, 'conductor.log');
      try {
        if (fs.existsSync(lp) && fs.readFileSync(lp, 'utf8').includes(marker)) return true;
      } catch (_) {
        /* ignore */
      }
    }
  } catch (_) {
    /* no prds/ */
  }
  return false;
}

function enforce() {
  if (!strictMode() || !eventKnown) return;
  const brain = firstExistingBrain();
  if (!brain) return; // no system of record → nothing to enforce against

  if (event === 'TaskCompleted') {
    // Only block completion of tasks that CLAIM a merge/ship/release when the brain
    // shows no PR-merged ([P5…) marker. forge-eval-gate + review-readiness.
    const claimsShip = /\b(merged|shipped|released|deployed|merge|ship|release|deploy)\b/.test(blob);
    if (claimsShip && !anyConductorHas(brain, '[P5')) {
      block(
        'TaskCompleted claims a merge/ship/release but no [P5…] (PR merged) marker exists in the brain. ' +
          'forge-eval-gate + review-readiness: eval GREEN and the PR set merged must be recorded before "done". ' +
          'Unset FORGE_TEAM_GATES to disable this gate.',
      );
    }
  } else if (event === 'TeammateIdle' && activeTask) {
    // Don't let a teammate go idle while the active task's last eval is RED/FAIL.
    const lp = path.join(brain, 'prds', activeTask, 'conductor.log');
    try {
      if (fs.existsSync(lp)) {
        const lastEval = (fs.readFileSync(lp, 'utf8').match(/\[P4\.4-EVAL-[A-Z-]+\]/g) || []).pop();
        if (lastEval && /(FAIL|RED)/.test(lastEval)) {
          block(
            `Eval is ${lastEval} for task ${activeTask} — self-heal is not complete (self-heal-loop-cap). ` +
              'Do not go idle. Unset FORGE_TEAM_GATES to disable this gate.',
          );
        }
      }
    } catch (_) {
      /* ignore */
    }
  }
  // TaskCreated: audit only — creation gating is too disruptive to enforce here.
}

try {
  audit();
} catch (e) {
  debug(`audit error: ${e.message}`);
}
try {
  enforce();
} catch (e) {
  debug(`enforce error: ${e.message}`);
}
process.exit(0);
