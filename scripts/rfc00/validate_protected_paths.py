#!/usr/bin/env python3
"""
RFC-00 Validator: Protected Paths

Valida que cambios a rutas protegidas (/core, /contracts, RFC-00) cumplan protocolo.

Exit codes:
  0 - PASS (sin cambios a rutas protegidas, o protocolo cumplido)
  1 - FAIL (cambios a rutas protegidas sin protocolo)
  2 - ERROR (script error)
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Tuple


# Rutas protegidas según Protected_Paths_Policy.md
PROTECTED_PATHS = [
    "core/",
    "contracts/",
    "docs/rfcs/RFC-00_MANIFEST.md",
]


def get_changed_files(base_ref: str = "HEAD") -> List[str]:
    """
    Get list of changed files in git diff.
    
    Args:
        base_ref: Git reference to diff against (e.g., "HEAD", "main", "HEAD~1")
    
    Returns:
        List of changed file paths
    """
    try:
        # Get diff --name-only
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            capture_output=True,
            text=True,
            check=True
        )
        
        files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return files
    
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to get git diff: {e}", file=sys.stderr)
        sys.exit(2)


def check_protected_paths(files: List[str]) -> Tuple[Set[str], List[str]]:
    """
    Check if any files are in protected paths.
    
    Returns:
        Tuple of (protected_files, violated_paths)
    """
    protected_files = set()
    violated_paths = []
    
    for file_path in files:
        for protected_path in PROTECTED_PATHS:
            if file_path.startswith(protected_path) or file_path == protected_path:
                protected_files.add(file_path)
                if protected_path not in violated_paths:
                    violated_paths.append(protected_path)
                break
    
    return protected_files, violated_paths


def check_rfc_reference_in_commits(base_ref: str = "HEAD~1") -> bool:
    """
    Check if commits contain RFC references.
    
    Returns:
        True if RFC reference found, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "log", f"{base_ref}..HEAD", "--pretty=format:%B"],
            capture_output=True,
            text=True,
            check=True
        )
        
        commit_messages = result.stdout
        
        # Look for RFC-XX or RFC-00A_XX patterns
        rfc_pattern = r"RFC-\d+|RFC-00A_\d+"
        if re.search(rfc_pattern, commit_messages, re.IGNORECASE):
            return True
        
        return False
    
    except subprocess.CalledProcessError:
        # If git log fails, assume no reference
        return False


def main() -> int:
    """Main validation logic."""
    parser = argparse.ArgumentParser(
        description="Validate protected paths policy compliance"
    )
    parser.add_argument(
        "--diff",
        default="HEAD",
        help="Git reference to diff against (default: HEAD)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    print(f"🔍 Validating protected paths...")
    if args.verbose:
        print(f"   Diff against: {args.diff}")
    print()
    
    # Get changed files
    changed_files = get_changed_files(args.diff)
    
    if not changed_files:
        print("✅ PASS: No files changed")
        return 0
    
    if args.verbose:
        print(f"Changed files ({len(changed_files)}):")
        for f in changed_files:
            print(f"  - {f}")
        print()
    
    # Check if any protected paths are touched
    protected_files, violated_paths = check_protected_paths(changed_files)
    
    if not protected_files:
        print("✅ PASS: No protected paths modified")
        return 0
    
    # Protected paths touched - check protocol
    print(f"⚠️  Protected paths modified ({len(violated_paths)}):")
    for path in violated_paths:
        print(f"  - {path}")
    print()
    
    # Check for RFC reference in commits
    has_rfc_ref = check_rfc_reference_in_commits(args.diff)
    
    if has_rfc_ref:
        print("✅ PASS: RFC reference found in commits")
        print()
        print("Note: Full protocol validation (PR template, CODEOWNERS approval)")
        print("      will be checked in PR workflow.")
        return 0
    
    # FAIL - protected paths modified without RFC reference
    print("❌ FAIL: Protected paths modified WITHOUT RFC reference")
    print()
    print("Protected files modified:")
    for f in sorted(protected_files):
        print(f"  - {f}")
    print()
    print("REQUIRED:")
    print("  - Commit messages must include 'RFC-XX' footer")
    print("  - PR must reference the authorizing RFC")
    print("  - PR template must be completed")
    print()
    print("See:")
    print("  docs/governance/Protected_Paths_Policy.md")
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
