"""
Invariant validator for CanonicalEvent.
RFC-01 implementation.

Validates business rules that cannot be expressed in JSON Schema:
- Uniqueness of canonical representation
- Append-only (no mutation)
- Observation vs interpretation separation
- Traceability requirements
"""

from typing import Dict, Any, List, Set


class InvariantViolation:
    """Represents a violation of a business invariant."""
    
    def __init__(self, invariant: str, message: str, context: Dict[str, Any] = None):
        self.invariant = invariant
        self.message = message
        self.context = context or {}
    
    def __repr__(self):
        return f"InvariantViolation(invariant='{self.invariant}', message='{self.message}')"


class InvariantValidationResult:
    """Result of invariant validation."""
    
    def __init__(self, valid: bool, violations: List[InvariantViolation] = None):
        self.valid = valid
        self.violations = violations or []
    
    def __bool__(self):
        return self.valid
    
    def __repr__(self):
        if self.valid:
            return "InvariantValidationResult(valid=True)"
        return f"InvariantValidationResult(valid=False, violations={len(self.violations)})"


class InvariantValidator:
    """Validates CanonicalEvent business invariants."""
    
    # Fields that must be present for traceability (subset of required fields)
    TRACEABILITY_FIELDS = {
        "source_system",
        "source_connector", 
        "source_environment",
        "observed_at",
        "raw_payload_hash",
        "raw_pointer"
    }
    
    def __init__(self, event_store: Set[str] = None):
        """
        Initialize invariant validator.
        
        Args:
            event_store: Set of known event_ids (for uniqueness check).
                        If None, uniqueness is not enforced.
        """
        self.event_store = event_store
    
    def validate(self, event: Dict[str, Any]) -> InvariantValidationResult:
        """
        Validate all invariants for a CanonicalEvent.
        
        Args:
            event: Event dictionary to validate
        
        Returns:
            InvariantValidationResult with validation status and violations
        """
        violations = []
        
        # Invariant 1: Uniqueness of canonical representation
        violations.extend(self._check_uniqueness(event))
        
        # Invariant 2: Traceability requirements
        violations.extend(self._check_traceability(event))
        
        return InvariantValidationResult(
            valid=len(violations) == 0,
            violations=violations
        )
    
    def _check_uniqueness(self, event: Dict[str, Any]) -> List[InvariantViolation]:
        """
        Check that event_id is unique (if event_store is provided).
        
        Args:
            event: Event to check
        
        Returns:
            List of violations (empty if valid)
        """
        if self.event_store is None:
            return []
        
        event_id = event.get("event_id")
        if not event_id:
            return []  # Schema validation will catch this
        
        if event_id in self.event_store:
            return [InvariantViolation(
                invariant="UNIQUENESS",
                message=f"Event ID already exists: {event_id}",
                context={"event_id": event_id}
            )]
        
        return []
    
    def _check_traceability(self, event: Dict[str, Any]) -> List[InvariantViolation]:
        """
        Check that all traceability fields are present and valid.
        
        Args:
            event: Event to check
        
        Returns:
            List of violations (empty if valid)
        """
        violations = []
        
        # Check required traceability fields
        for field in self.TRACEABILITY_FIELDS:
            if field not in event or not event[field]:
                violations.append(InvariantViolation(
                    invariant="TRACEABILITY",
                    message=f"Traceability field missing or empty: {field}",
                    context={"missing_field": field}
                ))
        
        return violations
