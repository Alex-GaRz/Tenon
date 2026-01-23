"""
Validation result structure.
RFC-01 + RFC-01A implementation.

Represents the outcome of any validation: PASS or REJECT with evidence.
"""

from typing import Optional
from .rejection_evidence import RejectionEvidence


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(
        self,
        valid: bool,
        evidence: Optional[RejectionEvidence] = None
    ):
        """
        Initialize validation result.
        
        Args:
            valid: True if validation passed, False if rejected
            evidence: RejectionEvidence if rejected, None if valid
        """
        self.valid = valid
        self.evidence = evidence
        
        # Invariant: if rejected, evidence must be present
        if not valid and evidence is None:
            raise ValueError("Rejected validation must provide evidence (no silent failures)")
    
    def __bool__(self):
        """Allow boolean evaluation of result."""
        return self.valid
    
    def to_dict(self):
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with status and evidence
        """
        result = {"valid": self.valid}
        if self.evidence:
            result["evidence"] = self.evidence.to_dict()
        return result
    
    def __repr__(self):
        if self.valid:
            return "ValidationResult(valid=True)"
        return f"ValidationResult(valid=False, evidence={self.evidence})"
    
    @classmethod
    def accept(cls):
        """Create a PASS result."""
        return cls(valid=True, evidence=None)
    
    @classmethod
    def reject(cls, evidence: RejectionEvidence):
        """Create a REJECT result with evidence."""
        return cls(valid=False, evidence=evidence)
