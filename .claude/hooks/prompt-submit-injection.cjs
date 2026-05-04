#!/usr/bin/env node
/**
 * Pure helpers for UserPromptSubmit gate injection — safe to unit test (no I/O).
 *
 * Used by prompt-submit.cjs and tools/js/test-prompt-submit-injection.cjs.
 */

'use strict';

const path = require('path');
const { GATE_PATTERNS } = require(path.join(__dirname, 'prompt-submit-gates.cjs'));

/**
 * Whether to omit static HARD-GATE block + next-gate hints entirely.
 *
 * @param {object} o
 * @param {boolean} o.injectionDisabled FORGE_DISABLE_GATE_INJECTION === 1
 * @param {boolean} o.anyBrainRootExists at least one configured brain directory exists
 * @param {boolean} o.taskIdEnvSet FORGE_TASK_ID or FORGE_PRD_TASK_ID non-empty
 * @param {string[]} o.conductorLogBodies bodies to evaluate:
 *   — taskIdEnvSet: exactly the **primary** conductor.log for the active scope (first brain that has one)
 *   — otherwise: **every** conductor.log across all relevant brains (none missed)
 * @returns {boolean}
 */
function shouldSuppressGateInjectionPure(o) {
  if (o.injectionDisabled || !o.anyBrainRootExists) return true;
  const bodies = o.conductorLogBodies || [];
  if (bodies.length === 0) return false;
  if (o.taskIdEnvSet) {
    return GATE_PATTERNS.PR_MERGED.test(bodies[0]);
  }
  return bodies.every((c) => GATE_PATTERNS.PR_MERGED.test(c));
}

module.exports = {
  shouldSuppressGateInjectionPure,
};
