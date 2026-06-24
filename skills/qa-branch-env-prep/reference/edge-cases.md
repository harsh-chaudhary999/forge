# qa-branch-env-prep — Edge Cases

### Branch not found on remote
Ask user (via `AskUserQuestion`): "Branch `<name>` not found on remote for `<repo>`. Options: (1) Push the branch and retry, (2) Use a different branch name, (3) Skip this repo and stay on current branch."

### Repo not in branches list
Stay on current branch. Log to manifest as "unchanged". This is expected — only repos with feature branches in scope need switching.

### Remote / branch-tracking mode with no branches provided
Valid: user is testing against an already-deployed stack (CI/staging). Skip Steps 2–4 entirely. Still write `.eval-env` and the manifest.

### Credentials in env
If `TEST_USER_PASSWORD`, `API_KEY`, or similar secrets are provided: confirm they are safe for the test environment. Never use production credentials. Redact all `*_PASSWORD`, `*_SECRET`, `*_KEY` values in the manifest.

### Monorepo (all services in one git repository)
When `forge-product.md` lists multiple services that all live in the same git repo (e.g. a monorepo at a single path), treat that repo as a single checkout target. The `branches` map entry uses the monorepo path as the key. Do not attempt separate checkouts per logical service — there is only one working tree. Record the single post-checkout SHA in the manifest against all logical services that share it.

### Restoring the operator's working tree (D30)
In-place checkout (Steps 2–4) mutates the operator's branches. Capture each repo's
pre-checkout branch + SHA in the manifest's **Pre-checkout state** table *before*
checkout. After the run completes (or on abort/error), offer to restore each repo to
its recorded original branch — do not leave the operator stranded on a feature branch
they did not ask to be on.
