# Edge Cases: How to Handle Unusual Situations

> Moved verbatim from `SKILL.md` for progressive disclosure (forge-skill-anatomy v2.1.0). Full symptom → root cause → action plan → escalation for each unusual brain situation. The one-line summaries and decision triggers stay in `../SKILL.md`.

### Edge Case 1: Brain Not Initialized

**Symptom:** `brain/` directory doesn't exist or is not in git

**Root cause:**
- First-time setup on a repo
- User cloned without initializing brain
- Shallow clone that excluded brain/

**Action Plan:**

1. Check if brain directory exists:
   ```bash
   ls -la brain/
   ```

2. If not found, initialize:
   ```bash
   mkdir -p brain/decisions/{architecture,product,engineering,ops}
   mkdir -p brain/drafts/{pending,resolved}
   mkdir -p brain/archived
   mkdir -p brain/products
   mkdir -p brain/links
   touch brain/README.md
   git add brain/
   git commit -m "brain: initialize structure"
   ```

3. Seed with empty README

**Escalation:** NEEDS_INFRA_CHANGE
- Document in project setup guide
- Add to git post-clone hook
- Include in forge-init script

### Edge Case 2: Brain Corrupted or Lost

**Symptom:** 
- Brain directory exists but not tracked in git
- File permissions wrong (not readable)
- Brain structure partially missing (some categories empty)

**Root cause:**
- User force-pushed, lost history
- Brain copied manually without .git
- Incomplete migration from old system

**Action Plan:**

1. Check git status:
   ```bash
   cd brain/
   git status
   git log --oneline | head -5
   ```

2. If not tracked, restore from backup:
   ```bash
   git reset --hard origin/main
   ```

3. If partially missing, check what's gone:
   ```bash
   find brain/ -type d | sort
   ```

4. Recreate missing structure:
   ```bash
   mkdir -p brain/decisions/{architecture,product,engineering,ops}
   mkdir -p brain/drafts/{pending,resolved}
   ```

5. Verify integrity:
   ```bash
   brain-read: verify structure
   ```

**Escalation:** NEEDS_COORDINATION
- Notify team of brain state
- Restore from backup if necessary
- Document what was lost

### Edge Case 3: Brain in Wrong Directory

**Symptom:**
- User cloned a different branch
- Brain exists but in unexpected path
- Multiple brain directories (confusion)

**Root cause:**
- User cloned wrong repository
- Symlink points to wrong location
- Team forked codebase and split brain structure

**Action Plan:**

1. Verify current directory:
   ```bash
   pwd
   ls -la .git/
   ```

2. Check where brain actually is:
   ```bash
   find . -name "brain" -type d
   ```

3. If it's a symlink, check target:
   ```bash
   ls -la brain/
   # Shows: brain -> /path/to/real/brain
   ```

4. Ensure the correct repository:
   ```bash
   git remote -v
   git branch
   ```

5. Guide to correct location:
   ```bash
   # If in wrong repo, clone correct one:
   git clone https://correct-repo.git
   cd correct-repo
   ```

**Escalation:** NEEDS_CONTEXT
- Document team's brain organization
- Clarify which repos share brain
- Update onboarding guide
