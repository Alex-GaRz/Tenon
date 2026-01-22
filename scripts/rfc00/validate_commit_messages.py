#!/usr/bin/env python3
"""
RFC-00 Validator: Commit Messages

Valida que commits sigan Commit_Policy.md:
- Formato: type(scope): subject
- Subject <= 72 chars
- RFC-XX en footer si toca rutas protegidas

Exit codes:
  0 - PASS (todos los commits válidos)
  1 - FAIL (commits inválidos)
  2 - ERROR (script error)
"""

import argparse
import re
import subprocess
import sys
from typing import List, Tuple, Optional


# Valid commit types según Commit_Policy.md
VALID_TYPES = ['feat', 'fix', 'refactor', 'test', 'docs', 'chore', 'perf']

# Protected paths que requieren RFC reference
PROTECTED_PATHS = ['core/', 'contracts/', 'docs/rfcs/RFC-00_MANIFEST.md']


class CommitMessage:
    """Represents a parsed commit message."""
    
    def __init__(self, sha: str, message: str):
        self.sha = sha
        self.message = message
        self.lines = message.split('\n')
        self.subject = self.lines[0] if self.lines else ""
        self.body = '\n'.join(self.lines[1:]) if len(self.lines) > 1 else ""
    
    def validate_format(self) -> Tuple[bool, Optional[str]]:
        """
        Validate commit message format.
        
        Returns:
            (is_valid, error_message)
        """
        # Check subject format: type(scope): message
        pattern = r'^(feat|fix|refactor|test|docs|chore|perf)(\([a-z0-9-]+\))?: .+'
        
        if not re.match(pattern, self.subject):
            return False, f"Subject must follow format: type(scope): message\n  Valid types: {', '.join(VALID_TYPES)}"
        
        # Check subject length
        if len(self.subject) > 72:
            return False, f"Subject too long ({len(self.subject)} chars, max 72)"
        
        # Check subject doesn't end with period
        if self.subject.endswith('.'):
            return False, "Subject must not end with period"
        
        return True, None
    
    def has_rfc_reference(self) -> bool:
        """Check if commit has RFC reference in footer."""
        rfc_pattern = r'\bRFC-\d+|RFC-00A_\d+\b'
        return bool(re.search(rfc_pattern, self.body, re.IGNORECASE))


def get_commits(commit_range: str) -> List[CommitMessage]:
    """
    Get commits in range.
    
    Args:
        commit_range: Git commit range (e.g., "HEAD~3..HEAD", "main..feature")
    
    Returns:
        List of CommitMessage objects
    """
    try:
        result = subprocess.run(
            ["git", "log", commit_range, "--pretty=format:%H%n%B%n---END---"],
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        raw_commits = result.stdout.split('---END---')
        
        for raw in raw_commits:
            raw = raw.strip()
            if not raw:
                continue
            
            lines = raw.split('\n')
            if len(lines) < 2:
                continue
            
            sha = lines[0]
            message = '\n'.join(lines[1:])
            commits.append(CommitMessage(sha, message))
        
        return commits
    
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to get commits: {e}", file=sys.stderr)
        sys.exit(2)


def get_files_in_commit(sha: str) -> List[str]:
    """Get list of files modified in commit."""
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


def touches_protected_paths(files: List[str]) -> bool:
    """Check if any file is in protected paths."""
    for file_path in files:
        for protected in PROTECTED_PATHS:
            if file_path.startswith(protected) or file_path == protected:
                return True
    return False


def main() -> int:
    """Main validation logic."""
    parser = argparse.ArgumentParser(
        description="Validate commit message format"
    )
    parser.add_argument(
        "--commits",
        default="HEAD~1..HEAD",
        help="Git commit range to validate (default: HEAD~1..HEAD)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    print(f"🔍 Validating commit messages...")
    if args.verbose:
        print(f"   Range: {args.commits}")
    print()
    
    commits = get_commits(args.commits)
    
    if not commits:
        print("✅ PASS: No commits to validate")
        return 0
    
    if args.verbose:
        print(f"Validating {len(commits)} commit(s)...")
        print()
    
    all_valid = True
    errors = []
    
    for commit in commits:
        sha_short = commit.sha[:7]
        
        # Validate format
        is_valid, error = commit.validate_format()
        
        if not is_valid:
            all_valid = False
            errors.append(f"Commit {sha_short}: {error}")
            errors.append(f"  Subject: {commit.subject}")
            continue
        
        # Check RFC reference if touching protected paths
        files = get_files_in_commit(commit.sha)
        if touches_protected_paths(files):
            if not commit.has_rfc_reference():
                all_valid = False
                errors.append(f"Commit {sha_short}: Missing RFC reference in footer")
                errors.append(f"  Subject: {commit.subject}")
                errors.append(f"  Touches protected paths: {[f for f in files if any(f.startswith(p) for p in PROTECTED_PATHS)]}")
                continue
        
        if args.verbose:
            print(f"✅ {sha_short}: {commit.subject}")
    
    print()
    
    if all_valid:
        print(f"✅ PASS: All {len(commits)} commit(s) valid")
        return 0
    
    # FAIL
    print(f"❌ FAIL: {len(errors)} error(s) found")
    print()
    for error in errors:
        print(f"  {error}")
    print()
    print("Required format:")
    print("  type(scope): subject")
    print()
    print("Valid types:")
    print(f"  {', '.join(VALID_TYPES)}")
    print()
    print("Commits touching /core or /contracts must include:")
    print("  RFC-XX")
    print("  (in commit message footer)")
    print()
    print("See:")
    print("  docs/governance/Commit_Policy.md")
    print()
    
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        sys.exit(2)
