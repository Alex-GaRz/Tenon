"""
RFC-06: Discrepancy Taxonomy - Closed Enumerations

Defines the closed taxonomy of discrepancy types and severity hints.
All values are aligned 1:1 with the JSON Schema contract.
"""

from enum import Enum


class DiscrepancyType(Enum):
    """
    Closed taxonomy of discrepancy types (RFC-06).
    
    These values MUST match exactly the enum in discrepancy.schema.json.
    No values may be added, removed, or renamed without schema versioning.
    """
    NO_DISCREPANCY = "NO_DISCREPANCY"
    TIMING_DELAY = "TIMING_DELAY"
    MISSING_EVENT = "MISSING_EVENT"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    STATUS_CONFLICT = "STATUS_CONFLICT"
    UNEXPECTED_REVERSAL = "UNEXPECTED_REVERSAL"
    ORPHAN_EVENT = "ORPHAN_EVENT"
    INCONSISTENT_FLOW = "INCONSISTENT_FLOW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class SeverityHint(Enum):
    """
    Severity classification for discrepancies.
    
    These values MUST match exactly the enum in discrepancy.schema.json.
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


# Immutable constants for validation and testing
DISCREPANCY_TYPE_VALUES = frozenset(dt.value for dt in DiscrepancyType)
SEVERITY_HINT_VALUES = frozenset(sh.value for sh in SeverityHint)


def validate_discrepancy_type(value: str) -> DiscrepancyType:
    """
    Validate and convert a string to DiscrepancyType.
    
    Args:
        value: String representation of discrepancy type
        
    Returns:
        DiscrepancyType enum member
        
    Raises:
        ValueError: If value is not in the closed taxonomy
    """
    if value not in DISCREPANCY_TYPE_VALUES:
        raise ValueError(
            f"Invalid discrepancy_type '{value}'. "
            f"Must be one of: {sorted(DISCREPANCY_TYPE_VALUES)}"
        )
    return DiscrepancyType(value)


def validate_severity_hint(value: str) -> SeverityHint:
    """
    Validate and convert a string to SeverityHint.
    
    Args:
        value: String representation of severity hint
        
    Returns:
        SeverityHint enum member
        
    Raises:
        ValueError: If value is not in the closed taxonomy
    """
    if value not in SEVERITY_HINT_VALUES:
        raise ValueError(
            f"Invalid severity_hint '{value}'. "
            f"Must be one of: {sorted(SEVERITY_HINT_VALUES)}"
        )
    return SeverityHint(value)
