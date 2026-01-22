#!/usr/bin/env python3
"""
RFC-00 Validator: NoGoals Enforcement

Detecta señales de funcionalidad prohibida por RFC-00 No-Goals:
- Ejecución de pagos/transferencias
- Posteo a libro contable oficial
- Auto-corrección de contabilidad
- Cálculo de precios/impuestos como fuente oficial

Exit codes:
  0 - PASS (no violations)
  1 - FAIL (violations detected)
  2 - ERROR (script error)
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple


# Keywords prohibidos en /core (alta prioridad - bloqueo automático)
PROHIBITED_KEYWORDS_HIGH = [
    # Ejecución de pagos/transferencias
    r'\bExecutePayment\b',
    r'\bProcessTransfer\b',
    r'\bPostTransaction\b',
    r'\bSendPayment\b',
    r'\bInitiateTransfer\b',
    
    # Posteo a libro contable
    r'\bCreateLedgerEntry\b',
    r'\bBookToGL\b',
    r'\bPostToAccounting\b',
    r'\bWriteToLedger\b',
    
    # Auto-corrección
    r'\bAutoCorrect\b',
    r'\bFixDiscrepancy\b',
    r'\bApplyCorrection\b',
    r'\bAutoResolve\b',
    
    # Pricing/Tax oficial
    r'\bCalculateTax\b',
    r'\bComputeFee\b',
    r'\bDeterminePricing\b',
]

# Imports prohibidos en /core
PROHIBITED_IMPORTS = [
    r'from stripe import.*(?:Charge|Payment|Transfer)',
    r'import stripe\.(?:Charge|Payment)',
    r'from paypal import',
    r'from adyen import',
]

# Paths prohibidos
PROHIBITED_PATHS = [
    r'core/payment_execution',
    r'core/accounting_posting',
    r'core/transfer_orchestration',
    r'core/tax_calculation',
]


class NoGoalsViolation:
    """Represents a NoGoals policy violation."""
    
    def __init__(self, file_path: str, line_num: int, line: str, reason: str):
        self.file_path = file_path
        self.line_num = line_num
        self.line = line.strip()
        self.reason = reason
    
    def __str__(self):
        return f"{self.file_path}:{self.line_num}\n  {self.line}\n  Reason: {self.reason}"


def get_changed_files(base_ref: str = "HEAD") -> List[str]:
    """Get list of changed files in /core."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            capture_output=True,
            text=True,
            check=True
        )
        
        files = [
            line.strip() 
            for line in result.stdout.splitlines() 
            if line.strip().startswith("core/")
        ]
        return files
    
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to get git diff: {e}", file=sys.stderr)
        sys.exit(2)


def check_file_content(file_path: str) -> List[NoGoalsViolation]:
    """Check file content for prohibited keywords."""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, start=1):
            # Check prohibited keywords
            for pattern in PROHIBITED_KEYWORDS_HIGH:
                if re.search(pattern, line):
                    violations.append(NoGoalsViolation(
                        file_path=file_path,
                        line_num=i,
                        line=line,
                        reason=f"Prohibited keyword: {pattern}"
                    ))
            
            # Check prohibited imports
            for pattern in PROHIBITED_IMPORTS:
                if re.search(pattern, line):
                    violations.append(NoGoalsViolation(
                        file_path=file_path,
                        line_num=i,
                        line=line,
                        reason=f"Prohibited import in /core: {pattern}"
                    ))
    
    except Exception as e:
        print(f"⚠️  WARNING: Cannot read {file_path}: {e}", file=sys.stderr)
    
    return violations


def check_prohibited_paths(files: List[str]) -> List[str]:
    """Check if any files are in prohibited paths."""
    violations = []
    
    for file_path in files:
        for pattern in PROHIBITED_PATHS:
            if re.search(pattern, file_path):
                violations.append(file_path)
                break
    
    return violations


def main() -> int:
    """Main validation logic."""
    parser = argparse.ArgumentParser(
        description="Validate NoGoals policy compliance"
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
    
    print("🔍 Validating NoGoals policy (detecting prohibited functionality)...")
    if args.verbose:
        print(f"   Scanning /core for violations")
    print()
    
    # Get changed files in /core
    changed_files = get_changed_files(args.diff)
    
    if not changed_files:
        print("✅ PASS: No /core files changed")
        return 0
    
    if args.verbose:
        print(f"Checking {len(changed_files)} file(s) in /core...")
        print()
    
    # Check for prohibited paths
    path_violations = check_prohibited_paths(changed_files)
    
    # Check file contents
    content_violations = []
    for file_path in changed_files:
        if Path(file_path).exists():
            violations = check_file_content(file_path)
            content_violations.extend(violations)
    
    # Report results
    if not path_violations and not content_violations:
        print("✅ PASS: No NoGoals violations detected")
        return 0
    
    # FAIL
    print("❌ FAIL: NoGoals violations detected")
    print()
    
    if path_violations:
        print(f"Prohibited paths ({len(path_violations)}):")
        for path in path_violations:
            print(f"  - {path}")
        print()
        print("These paths suggest execution/posting functionality prohibited in /core")
        print()
    
    if content_violations:
        print(f"Prohibited keywords/imports ({len(content_violations)}):")
        for v in content_violations:
            print(f"  {v}")
            print()
    
    print("RFC-00 No-Goals prohibit:")
    print("  - Payment/transfer execution")
    print("  - Posting to official accounting systems")
    print("  - Auto-correction of discrepancies")
    print("  - Pricing/tax calculation as official source")
    print()
    print("Tenon is designed to OBSERVE and CORRELATE, not EXECUTE.")
    print()
    print("If this is a false positive:")
    print("  - Add PR label 'nogoals-exception'")
    print("  - Provide justification in PR description")
    print("  - Requires 2 CODEOWNERS approvals")
    print()
    print("See:")
    print("  docs/governance/NoGoals_Enforcement.md")
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
