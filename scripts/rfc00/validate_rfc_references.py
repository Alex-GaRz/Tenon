#!/usr/bin/env python3
"""
RFC-00 Validator: RFC References

Valida que PRs que tocan rutas protegidas incluyan referencias RFC válidas.
Este script es llamado por CI con contexto de PR.

Exit codes:
  0 - PASS (referencias RFC presentes o no requeridas)
  1 - FAIL (referencias RFC faltantes)
  2 - ERROR (script error)
"""

import argparse
import os
import re
import sys
from typing import Optional, List


def extract_rfc_references(text: str) -> List[str]:
    """
    Extract RFC references from text.
    
    Returns:
        List of RFC references found (e.g., ['RFC-04', 'RFC-00A_001'])
    """
    # Pattern: RFC-XX or RFC-00A_XXX
    pattern = r'\b(RFC-\d+|RFC-00A_\d+)\b'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return [m.upper() for m in matches]


def validate_pr_body(pr_body: str) -> bool:
    """
    Validate that PR body contains RFC reference.
    
    Returns:
        True if valid RFC reference found
    """
    if not pr_body:
        return False
    
    # Check for "N/A" or "non-core change" exemptions
    if re.search(r'N/A\s*[-:]?\s*non-core', pr_body, re.IGNORECASE):
        return True
    
    # Check for RFC references
    refs = extract_rfc_references(pr_body)
    return len(refs) > 0


def main() -> int:
    """Main validation logic."""
    parser = argparse.ArgumentParser(
        description="Validate RFC references in PR"
    )
    parser.add_argument(
        "--pr-body",
        help="PR body text (from GitHub Actions context)"
    )
    parser.add_argument(
        "--pr-body-file",
        help="Path to file containing PR body"
    )
    parser.add_argument(
        "--require-rfc",
        action="store_true",
        help="Fail if no RFC reference found (use when protected paths touched)"
    )
    
    args = parser.parse_args()
    
    print("🔍 Validating RFC references...")
    print()
    
    # Get PR body
    pr_body = None
    if args.pr_body:
        pr_body = args.pr_body
    elif args.pr_body_file:
        try:
            with open(args.pr_body_file, 'r', encoding='utf-8') as f:
                pr_body = f.read()
        except Exception as e:
            print(f"❌ ERROR: Cannot read PR body file: {e}", file=sys.stderr)
            return 2
    else:
        # Try to get from environment (GitHub Actions)
        pr_body = os.environ.get("PR_BODY", "")
    
    if not pr_body:
        if args.require_rfc:
            print("❌ FAIL: No PR body provided and RFC reference required")
            return 1
        else:
            print("⚠️  WARNING: No PR body to validate")
            return 0
    
    # Validate
    is_valid = validate_pr_body(pr_body)
    
    if is_valid:
        refs = extract_rfc_references(pr_body)
        if refs:
            print(f"✅ PASS: RFC reference(s) found: {', '.join(refs)}")
        else:
            print("✅ PASS: Marked as non-core change (N/A)")
        return 0
    
    if args.require_rfc:
        print("❌ FAIL: RFC reference required but not found")
        print()
        print("This PR modifies protected paths (/core, /contracts, or RFC-00).")
        print()
        print("REQUIRED:")
        print("  - PR body must include 'RFC-XX' reference")
        print("  - OR mark as 'N/A - non-core change' (only if truly not touching core)")
        print()
        print("Examples:")
        print("  RFC: RFC-04")
        print("  RFC: RFC-00A_001 (for amendments)")
        print("  RFC: N/A - non-core change (only for docs/governance)")
        print()
        print("See:")
        print("  docs/governance/Protected_Paths_Policy.md")
        print()
        return 1
    else:
        print("⚠️  WARNING: No RFC reference found (not required for this PR)")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        sys.exit(2)
