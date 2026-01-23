"""
Rejection evidence structure.
RFC-01 + RFC-01A implementation.

Ensures no silent failures - all rejections must produce structured evidence.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class RejectionEvidence:
    """Structured evidence for a rejection decision."""
    
    def __init__(
        self,
        reason: str,
        rejected_at: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        conflicting_fields: Optional[List[str]] = None,
        matched_event_id: Optional[str] = None,
        match_score: Optional[float] = None
    ):
        """
        Initialize rejection evidence.
        
        Args:
            reason: Human-readable reason for rejection
            rejected_at: ISO 8601 timestamp of rejection (defaults to now)
            context: Additional context data
            conflicting_fields: List of fields that conflict
            matched_event_id: Event ID of matching event (for duplicates)
            match_score: Confidence score 0.0-1.0
        """
        self.reason = reason
        self.rejected_at = rejected_at or datetime.utcnow().isoformat() + "Z"
        self.context = context or {}
        self.conflicting_fields = conflicting_fields or []
        self.matched_event_id = matched_event_id
        self.match_score = match_score
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with all evidence fields
        """
        result = {
            "reason": self.reason,
            "rejected_at": self.rejected_at,
            "context": self.context
        }
        
        if self.conflicting_fields:
            result["conflicting_fields"] = self.conflicting_fields
        
        if self.matched_event_id:
            result["matched_event_id"] = self.matched_event_id
        
        if self.match_score is not None:
            result["match_score"] = self.match_score
        
        return result
    
    def __repr__(self):
        return f"RejectionEvidence(reason='{self.reason}', rejected_at='{self.rejected_at}')"
