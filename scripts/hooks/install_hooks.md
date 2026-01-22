# Installing Git Hooks for RFC-00 Enforcement

Local git hooks help catch policy violations **before** they reach CI, saving time and iteration cycles.

---

## Available Hooks

- **pre-commit** — Validates NoGoals policy and warns about protected paths changes

---

## Installation (Manual)

### Unix/Linux/macOS:

```bash
# From repository root
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Windows (Git Bash):

```bash
# From repository root
cp .githooks/pre-commit .git/hooks/pre-commit
```

### Windows (PowerShell):

```powershell
# From repository root
Copy-Item .githooks\pre-commit .git\hooks\pre-commit
```

---

## Installation (Automatic via Git Config)

**Git 2.9+** supports setting a custom hooks directory:

```bash
# Point Git to .githooks directory
git config core.hooksPath .githooks
```

This makes `.githooks/pre-commit` active automatically.

**To revert:**
```bash
git config --unset core.hooksPath
```

---

## Verify Installation

After installing, test the hook:

```bash
# Should show hook is active
ls -la .git/hooks/pre-commit

# Test hook execution (should pass if no changes)
git commit --allow-empty -m "test: verify hook works"
```

If hook is working, you'll see:
```
🔍 RFC-00 pre-commit validation...
✅ No files staged
```

---

## What the Hook Does

### Pre-Commit Hook:

1. **Detects protected paths:**
   - Warns if you're committing to `/core`, `/contracts`, or `RFC-00_MANIFEST.md`
   - Reminds you to include `RFC-XX` in commit message footer

2. **Validates NoGoals:**
   - Runs `validate_nogoals.py` on staged files
   - Blocks commit if prohibited keywords detected in `/core`

3. **Non-blocking warnings:**
   - Protected paths changes only trigger warnings (not blocks)
   - Full validation happens in CI

---

## Bypassing Hooks (Emergency Only)

If you need to commit without hook validation (not recommended):

```bash
git commit --no-verify -m "emergency: describe what and why"
```

**⚠️ WARNING:** Bypassing hooks means CI will catch issues later, requiring PR rework.

---

## Troubleshooting

### Hook not executing

**Check permissions (Unix/macOS/Linux):**
```bash
chmod +x .git/hooks/pre-commit
```

**Verify hook path:**
```bash
git config core.hooksPath
# Should show: .githooks (if using config method)
# Or should be empty (if using manual copy method)
```

### Python not found

Hooks require Python 3.8+. If not in PATH:

**Unix/macOS/Linux:**
```bash
# Edit .git/hooks/pre-commit
# Change: PYTHON_CMD="python3"
# To: PYTHON_CMD="/full/path/to/python3"
```

**Windows:**
```bash
# Edit .git\hooks\pre-commit
# Change: PYTHON_CMD="python3"
# To: PYTHON_CMD="C:\Path\To\Python\python.exe"
```

### Hook too slow

If hooks slow down commits significantly:

```bash
# Disable temporarily
git config core.hooksPath ""

# Re-enable when needed
git config core.hooksPath .githooks
```

---

## Customization

To modify hook behavior:

1. Edit `.githooks/pre-commit` (source file)
2. If using manual copy method, re-copy to `.git/hooks/`
3. If using `core.hooksPath`, changes apply immediately

---

## Recommended Workflow

1. **Install hooks** when you clone the repo
2. **Keep hooks enabled** during daily work
3. **Let hooks warn you** about protected paths
4. **Fix locally** before pushing (saves CI cycles)

---

## Team Onboarding

Add to team onboarding checklist:

```markdown
- [ ] Clone Tenon repo
- [ ] Install git hooks: `git config core.hooksPath .githooks`
- [ ] Test hooks: `git commit --allow-empty -m "test: verify hooks"`
- [ ] Read: docs/governance/Commit_Policy.md
```

---

## Last Updated

**2026-01-21:** Initial hooks documentation created for RFC-00.
