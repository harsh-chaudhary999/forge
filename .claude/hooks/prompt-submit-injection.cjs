#!/usr/bin/env node
/**
 * Pure merge-state check for UserPromptSubmit suppression — safe to unit test (no I/O).
 *
 * `prompt-submit.cjs` handles `FORGE_DISABLE_GATE_INJECTION` and missing brain **before** any
 * log I/O; this module only answers “given conductor bodies, should we suppress for PR_MERGED?”
 *
 * Used by prompt-submit.cjs and tools/js/test-prompt-submit-injection.cjs.
 */

'use strict';

const path = require('path');
const { GATE_PATTERNS } = require(path.join(__dirname, 'prompt-submit-gates.cjs'));

/**
 * Whether PR_MERGED state implies omitting static gates + next-gate injection.
 *
 * @param {boolean} taskIdEnvSet FORGE_TASK_ID or FORGE_PRD_TASK_ID non-empty
 * @param {string[]} conductorLogBodies primary scoped body, or every task’s body when unscoped
 * @returns {boolean}
 */
function shouldSuppressFromConductorMergeState(taskIdEnvSet, conductorLogBodies) {
  const bodies = conductorLogBodies || [];
  if (bodies.length === 0) return false;
  if (taskIdEnvSet) {
    return GATE_PATTERNS.PR_MERGED.test(bodies[0]);
  }
  return bodies.every((c) => GATE_PATTERNS.PR_MERGED.test(c));
}

module.exports = {
  shouldSuppressFromConductorMergeState,
};
