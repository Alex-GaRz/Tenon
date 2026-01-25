"""
RFC-07: Causality Model - Closed Enumerations

Defines the closed taxonomy of causality types.
All values are aligned 1:1 with the JSON Schema contract.
"""

from enum import Enum


class CausalityType(Enum):
    """
    Closed taxonomy of causality types (RFC-07).
    
    These values MUST match exactly the enum in causality_attribution.schema.json.
    No values may be added, removed, or renamed without schema versioning.
    """
    SOURCE_DELAY = "SOURCE_DELAY"
    SOURCE_OMISSION = "SOURCE_OMISSION"
    SOURCE_DUPLICATION = "SOURCE_DUPLICATION"
    SOURCE_INCONSISTENCY = "SOURCE_INCONSISTENCY"
    INTEGRATION_MAPPING_ERROR = "INTEGRATION_MAPPING_ERROR"
    NORMALIZATION_LOSS = "NORMALIZATION_LOSS"
    CORRELATION_AMBIGUITY = "CORRELATION_AMBIGUITY"
    STATE_TRANSITION_GAP = "STATE_TRANSITION_GAP"
    EXTERNAL_SYSTEM_CHANGE = "EXTERNAL_SYSTEM_CHANGE"
    UNKNOWN_CAUSE = "UNKNOWN_CAUSE"


# Immutable constant for validation and testing
CAUSALITY_TYPE_VALUES = frozenset(ct.value for ct in CausalityType)


def validate_causality_type(value: str) -> CausalityType:
    """
    Validate and convert a string to CausalityType.
    
    Args:
        value: String representation of causality type
        
    Returns:
        CausalityType enum member
        
    Raises:
        ValueError: If value is not in the closed taxonomy
    """
    if value not in CAUSALITY_TYPE_VALUES:
        raise ValueError(
            f"Invalid cause_type '{value}'. "
            f"Must be one of: {sorted(CAUSALITY_TYPE_VALUES)}"
        )
    return CausalityType(value)
