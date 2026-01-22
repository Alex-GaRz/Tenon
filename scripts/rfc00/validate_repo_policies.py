#!/usr/bin/env python3
"""
RFC-00 Validator: Repository Policies

Verifica que las políticas y plantillas obligatorias del RFC-00 existan en el repo.

Exit codes:
  0 - PASS (todas las políticas presentes)
  1 - FAIL (falta alguna política)
  2 - ERROR (script error)
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple


# Lista de archivos obligatorios según RFC-00
REQUIRED_FILES = [
    # RFCs
    "docs/rfcs/RFC-00_MANIFEST.md",
    "docs/rfcs/README.md",
    
    # Governance Policies
    "docs/governance/README.md",
    "docs/governance/RFC_Amendment_Policy.md",
    "docs/governance/Protected_Paths_Policy.md",
    "docs/governance/PR_Gate_RFC-00.md",
    "docs/governance/Commit_Policy.md",
    "docs/governance/Contracts_Versioning_Policy.md",
    "docs/governance/NoGoals_Enforcement.md",
    "docs/governance/Review_Checklist.md",
    "docs/governance/CI_Status_Checks.md",
    "docs/governance/Labels_Standard.md",
    "docs/governance/DECISIONS.md",
    "docs/governance/RFC-00_STATUS.md",
    
    # GitHub Templates
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/rfc_change_request.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/CODEOWNERS",
    
    # Commit Template
    ".gitmessage",
]


def find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    
    # If not found, assume current directory is root
    return Path.cwd()


def validate_files(repo_root: Path) -> Tuple[List[str], List[str]]:
    """
    Validate that all required files exist.
    
    Returns:
        Tuple of (missing_files, present_files)
    """
    missing = []
    present = []
    
    for file_path in REQUIRED_FILES:
        full_path = repo_root / file_path
        if full_path.exists():
            present.append(file_path)
        else:
            missing.append(file_path)
    
    return missing, present


def main() -> int:
    """Main validation logic."""
    repo_root = find_repo_root()
    
    print(f"🔍 Validating RFC-00 repository policies...")
    print(f"📁 Repository root: {repo_root}")
    print()
    
    missing, present = validate_files(repo_root)
    
    if not missing:
        print("✅ PASS: All RFC-00 required policies and templates are present")
        print(f"   {len(present)} files validated")
        return 0
    
    # FAIL - missing files
    print("❌ FAIL: Missing required RFC-00 policies/templates")
    print()
    print(f"Missing {len(missing)} file(s):")
    for file_path in missing:
        print(f"  - {file_path}")
    
    print()
    print("These files are required by RFC-00. See:")
    print("  docs/governance/README.md")
    print("  docs/governance/RFC-00_STATUS.md")
    print()
    
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        sys.exit(2)
