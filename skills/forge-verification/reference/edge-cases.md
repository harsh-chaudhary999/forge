# forge-verification — Additional Edge Cases

## Additional Edge Cases

### Edge Case 1: Verification Tool Is Broken (False Positives, Crashes, Invalid Output)
**Situation:** Verification tool itself is buggy or invalid. It crashes, produces nonsensical output, or has false positives.

**Example:** Test framework hangs on invalid assertion syntax. Verification script crashes mid-test. Coverage report shows 200% coverage (mathematically impossible).

**Do NOT:** Trust output from broken tools or claim verification passed based on suspect output.

**Action:**
1. Identify: is the tool broken or is the code broken?
   - Run tool on known-good code (previous commit, simple example)
   - Does tool work on that code? Then your code is broken (not the tool)
   - Does tool still fail on known-good code? Then tool is broken
2. If tool is broken:
   - Do NOT use it to verify your code
   - Escalate as **BLOCKED** (verification tool unavailable)
   - Find alternate verification method or wait for tool fix
   - Document tool failure in brain
3. If code is broken:
   - Fix code
   - Re-run verification
   - Proceed normally
4. Never ship based on verification from broken tools

---

### Edge Case 2: Verification Output Is Unreadable (Logs Too Large, Format Unclear, Summary Insufficient)
**Situation:** Verification runs, produces output, but output is hard to parse or understand.

**Example:** Test output is 50MB log with no summary. Test names are cryptic (test_0001, test_0002). Output format differs from expected (JSON instead of TAP, etc.).

**Do NOT:** Summarize output in words ("looks like it passed"). Output must be human-readable.

**Action:**
1. Examine raw output:
   - Is it parseable? (valid JSON, TAP format, etc.)
   - Is it complete? (no truncation, all assertions visible)
   - Is it meaningful? (test names describe what they test)
2. If output is too large:
   - Filter to relevant sections (failures, summary, stats)
   - Or re-run with verbose=false, summary-only
   - Document what was filtered and why
3. If output format is unclear:
   - Re-run with standard format (TAP, JSON, human-readable)
   - Or write parser to convert to readable format
4. If output is still unclear:
   - Escalate as **BLOCKED** (verification output uninterpretable)
   - Tool maintainers must improve output readability
5. Document readable output in brain (with context)

---

### Edge Case 3: Verification Passes but Humans Spot Issues (Tool Missed Bugs)
**Situation:** Verification suite passes all tests, but human testing or production finds bugs. Tool missed real issues.

**Example:** All unit tests pass. Integration tests pass. Manual testing discovers "user can't export data" feature doesn't work.

**Do NOT:** Ignore human findings. Verification tools are not infallible.

**Action:**
1. Investigate: why did verification miss this?
   - Was the scenario not tested? (missing test case)
   - Was test written incorrectly? (false positive)
   - Was behavior regression not caught? (old test, changed code)
2. Add test case:
   - Write test that reproduces the human-found issue
   - Verify test fails on current code
   - Fix code
   - Verify test passes
   - Re-run all verification (not just new test)
3. Document in brain:
   - What was missed by verification
   - Why test was missing
   - Action taken (added test, fixed code)
4. Review verification coverage:
   - Are there other scenarios humans would test that verification misses?
   - Add them to verification suite
5. Key lesson: Verification catches what you test. Humans catch what you didn't test.

---

Output: **PASS** (with evidence from working tools) or **BLOCKED** (verification tool broken, output unreadable, infrastructure down, unresolvable flakiness)

---

### Edge Case 4: Test Count Drops Between Runs (Silent Test Deletion)

**Symptom:** Verification passes on run N (47 tests, all pass). On run N+1 after a code change, 44 tests pass — but the implementer claims "nothing was deleted." The 3 missing tests were silently removed.

**Do NOT:** Accept a passing run if the test count has decreased without a documented reason.

**Action:**
1. Compare test counts between the prior run and the current run — flag any decrease
2. Ask the implementer: which tests were removed, and why? Require a commit that shows the deletion
3. If tests were removed because they were "duplicates" or "flaky," require evidence before accepting the removal
4. If tests were removed because the feature was descoped, verify against the spec that the descope was intentional
5. A decrease in test count is a red flag, not a neutral fact — treat it as BLOCKED until explained
6. Escalation: BLOCKED if test count decreases without justification committed to git

---

### Edge Case 5: Verification Passes Locally but CI Shows Different Results

**Symptom:** Local `npm test` shows 47/47 passing. CI pipeline shows 41/47 with 6 failures. The implementer argues "it works on my machine."

**Do NOT:** Accept local verification as evidence when CI contradicts it.

**Action:**
1. CI is authoritative — it runs in a clean environment without local dev state
2. Identify the failing tests in CI output — they often fail due to environment differences (missing env vars, different Node version, different file permissions)
3. Require the implementer to reproduce CI failures locally: `CI=true npm test` or use the same env vars as CI
4. Do not approve or merge until CI passes — "works locally" is not verification evidence
5. Common CI-only failures: hardcoded localhost references, missing `.env` entries, implicit dependency on global tools not in CI
6. Escalation: BLOCKED until CI passes; NEEDS_COORDINATION if CI infrastructure itself is broken (not the code)

---
