# Branch Protection Configuration for Tenon Repository

This document provides the **exact configuration** needed in GitHub Settings to enforce RFC-00 policies.

---

## ⚠️ CRITICAL: Manual Configuration Required

The workflows created in ITERACIÓN 4 are **ready to run**, but GitHub branch protection **must be configured manually** in repository settings.

**Without this configuration, PRs can bypass CI checks.**

---

## Configuration Steps

### 1. Navigate to Branch Protection Settings

1. Go to repository: `https://github.com/your-org/Tenon`
2. Click **Settings** (requires admin permissions)
3. Click **Branches** (left sidebar)
4. Click **Add branch protection rule** (or edit existing rule for `main`)

---

### 2. Branch Name Pattern

```
main
```

---

### 3. Protect Matching Branches

Enable the following settings:

#### ✅ Require a pull request before merging

- [x] **Require approvals:** `1` (minimum)
- [x] **Dismiss stale pull request approvals when new commits are pushed**
- [x] **Require review from Code Owners**

---

#### ✅ Require status checks to pass before merging

- [x] **Require branches to be up to date before merging**

**Add required status checks:**

Click "Add required status checks" and search for:

```
RFC-00 Guardrails / validate-pr-template
RFC-00 Guardrails / validate-commit-messages
RFC-00 Guardrails / validate-repo-policies
RFC-00 Guardrails / validate-nogoals
Protected Paths / validate-protected-paths
Protected Paths / validate-rfc-references
Protected Paths / require-codeowners
```

**Note:** Status checks will only appear in the list **after the first PR runs the workflows**. You may need to:
1. Open a test PR first
2. Let workflows run
3. Then return to settings to add them as required

---

#### ✅ Require conversation resolution before merging

- [x] **All conversations on code must be resolved before merging**

---

#### ✅ Do not allow bypassing the above settings

- [x] **Do not allow bypassing the above settings** (recommended)
  
  **OR** (if you need admin bypass for emergencies):
  
- [ ] Allow specified actors to bypass (select specific admin users only)

---

#### ✅ Restrict who can push to matching branches (Optional but Recommended)

- [x] **Restrict pushes that create matching branches**
- Select: Repository admins + specific teams (e.g., `@tenon-core-leads`)

---

### 4. Save Changes

Click **Create** or **Save changes**

---

## Testing Branch Protection

After configuration, test that protection works:

### Test 1: PR without template should fail

```bash
# Create test branch
git checkout -b test/empty-pr
echo "test" > test.txt
git add test.txt
git commit -m "test: empty commit"
git push origin test/empty-pr

# Open PR with empty body (no template)
# Expected: "validate-pr-template" check FAILS
```

### Test 2: PR touching /core without RFC should fail

```bash
# Create test branch
git checkout -b test/no-rfc-core
echo "# test" >> core/test.py
git add core/test.py
git commit -m "test: modify core without RFC"
git push origin test/no-rfc-core

# Open PR (use template but no RFC reference)
# Expected: "validate-rfc-references" check FAILS
```

### Test 3: PR with valid RFC should pass

```bash
# Create test branch
git checkout -b test/valid-rfc
echo "# docs update" >> docs/governance/README.md
git add docs/governance/README.md
git commit -m "docs(governance): update README

RFC: N/A - non-core change"
git push origin test/valid-rfc

# Open PR with complete template
# Expected: All checks PASS
```

---

## Verification Checklist

After configuration, verify:

- [ ] Branch protection rule exists for `main`
- [ ] "Require pull request" is enabled
- [ ] "Require review from Code Owners" is enabled
- [ ] All 7 status checks are listed as required
- [ ] Test PR without template FAILS at "validate-pr-template"
- [ ] Test PR touching /core without RFC FAILS at "validate-rfc-references"
- [ ] Test PR with complete protocol PASSES all checks

---

## Common Issues

### Issue: Status checks not appearing in list

**Cause:** Workflows haven't run yet on a PR.

**Solution:**
1. Open any test PR
2. Let workflows execute
3. Return to branch protection settings
4. Status checks should now appear in autocomplete

### Issue: "Require review from Code Owners" grayed out

**Cause:** `.github/CODEOWNERS` file not found or invalid.

**Solution:**
1. Verify `.github/CODEOWNERS` exists
2. Check syntax is valid
3. Ensure teams/users referenced exist

### Issue: PRs can still merge without checks

**Cause:** Status checks not marked as "required".

**Solution:**
1. Go to branch protection settings
2. Ensure all 7 checks are in "Required status checks" list
3. Ensure "Require status checks to pass before merging" is checked

---

## Emergency Bypass Procedure

If branch protection must be bypassed (production emergency):

1. **Document in advance:**
   - Create issue explaining emergency
   - Get approval from 2+ CODEOWNERS

2. **Bypass method:**
   - Admin user can force-merge if "Do not allow bypassing" is unchecked
   - OR temporarily disable branch protection (not recommended)

3. **Follow-up (mandatory within 48h):**
   - Create "follow-up PR" with full protocol
   - Document in `docs/governance/DECISIONS.md`
   - Add to emergency fixes log

See: [docs/governance/PR_Gate_RFC-00.md](PR_Gate_RFC-00.md) — Exceptions section

---

## Team Setup for CODEOWNERS

The `.github/CODEOWNERS` file references GitHub teams. These must be created:

### Required Teams:

1. **@tenon-architects** — Senior architects, approve core/contracts/RFCs
2. **@tenon-core-leads** — Core system maintainers
3. **@tenon-contracts-leads** — Contract/schema maintainers
4. **@tenon-governance-leads** — Governance policy maintainers
5. **@tenon-devops-leads** — CI/CD and tooling maintainers
6. **@tenon-adapters-leads** — Adapter maintainers

### Creating Teams:

1. Go to `https://github.com/orgs/your-org/teams`
2. Click "New team"
3. Set team name (e.g., `tenon-architects`)
4. Add members
5. Set permissions (Write or Maintain for PRs)

**Temporary workaround (for initial setup):**

Edit `.github/CODEOWNERS` to use individual users instead of teams:

```diff
- /core/** @tenon-architects @tenon-core-leads
+ /core/** @alice @bob @charlie
```

---

## Maintenance

**Review quarterly:**
- Are all required checks still listed?
- Are CODEOWNERS teams up to date?
- Are bypass permissions still appropriate?

**After adding new workflows:**
- Update this document with new required checks
- Update branch protection settings

---

## Status

**Current State (ITERACIÓN 4 Complete):**

- ✅ Workflows created and ready
- 🔴 Branch protection NOT YET CONFIGURED (manual step required)
- 🔴 CODEOWNERS teams NOT YET CREATED (manual step required)

**To mark RFC-00 as PASS:**
1. Configure branch protection (this document)
2. Create CODEOWNERS teams
3. Run test PRs to verify (Test 1, 2, 3 above)
4. Update `docs/governance/RFC-00_STATUS.md`

---

## Last Updated

**2026-01-21:** Initial branch protection configuration guide created for RFC-00 ITERACIÓN 4.
