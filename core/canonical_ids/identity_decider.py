"""
Identity decision engine.
RFC-01A implementation.

Makes explicit identity decisions: ACCEPT / REJECT_DUPLICATE / FLAG_AMBIGUOUS.
Conservative approach: insufficient evidence → FLAG_AMBIGUOUS (never silent ACCEPT).
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

from ..validation.rejection_evidence import RejectionEvidence
from ..validation.validation_result import ValidationResult


class IdentityDecision(str, Enum):
    """Identity decision outcomes."""
    ACCEPT = "ACCEPT"
    REJECT_DUPLICATE = "REJECT_DUPLICATE"
    FLAG_AMBIGUOUS = "FLAG_AMBIGUOUS"


class IdentityMatch:
    """Result of identity matching."""
    
    def __init__(
        self,
        decision: IdentityDecision,
        matched_event_id: Optional[str] = None,
        match_score: float = 0.0,
        conflicting_fields: Optional[List[str]] = None,
        reason: str = ""
    ):
        self.decision = decision
        self.matched_event_id = matched_event_id
        self.match_score = match_score
        self.conflicting_fields = conflicting_fields or []
        self.reason = reason


class IdentityDecider:
    """
    Makes identity decisions for canonical events.
    
    Conservative strategy:
    - Exact match on idempotency_key → REJECT_DUPLICATE
    - Partial match (some fields differ) → FLAG_AMBIGUOUS
    - No match → ACCEPT
    - Insufficient data → FLAG_AMBIGUOUS (never silent ACCEPT)
    """
    
    def __init__(self, version: str = "1.0.0"):
        """
        Initialize identity decider.
        
        Args:
            version: Version of the decision algorithm
        """
        self.version = version
    
    def decide(
        self,
        idempotency_key: str,
        event: Dict[str, Any],
        existing_events: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> IdentityMatch:
        """
        Conservative strategy:
        - Check for exact hash match (Collision on Key)
        - Check for identifier collision (Same Source ID, different hash)
        """
        if not existing_events:
            return IdentityMatch(decision=IdentityDecision.ACCEPT, reason="No existing events")

        # 1. Búsqueda por Llave Exacta (Hash Collision)
        if idempotency_key in existing_events:
            existing_event = existing_events[idempotency_key]
            conflicts = self._find_conflicts(event, existing_event)
            
            if not conflicts:
                return IdentityMatch(
                    decision=IdentityDecision.REJECT_DUPLICATE,
                    matched_event_id=existing_event.get("event_id"),
                    match_score=1.0,
                    reason=f"Exact duplicate of event {existing_event.get('event_id')}"
                )
            else:
                return IdentityMatch(
                    decision=IdentityDecision.FLAG_AMBIGUOUS,
                    matched_event_id=existing_event.get("event_id"),
                    match_score=0.5,
                    conflicting_fields=conflicts,
                    reason=f"Partial match (same key, different fields) with event {existing_event.get('event_id')}"
                )

        # 2. Búsqueda por Colisión de Identificador (Conservative Approach)
        # Si la llave es nueva, pero el source_event_id ya existe, es AMBIGUO.
        source_id = event.get("source_event_id")
        if source_id:
            for existing_evt in existing_events.values():
                if existing_evt.get("source_event_id") == source_id:
                    conflicts = self._find_conflicts(event, existing_evt)
                    return IdentityMatch(
                        decision=IdentityDecision.FLAG_AMBIGUOUS,
                        matched_event_id=existing_evt.get("event_id"),
                        match_score=0.5,
                        conflicting_fields=conflicts,
                        reason=f"Identity collision on source_event_id: {source_id}"
                    )
        
        return IdentityMatch(
            decision=IdentityDecision.ACCEPT,
            reason="No existing event matches this identity"
        )
    
    def _find_conflicts(
        self,
        event1: Dict[str, Any],
        event2: Dict[str, Any]
    ) -> List[str]:
        """
        Find conflicting fields between two events.
        
        Args:
            event1: First event
            event2: Second event
        
        Returns:
            List of field names that differ
        """
        # Critical fields to compare (financial/semantic)
        critical_fields = [
            "amount",
            "currency",
            "direction",
            "event_type",
            "source_system"
        ]
        
        conflicts = []
        for field in critical_fields:
            val1 = event1.get(field)
            val2 = event2.get(field)
            
            if val1 != val2:
                conflicts.append(field)
        
        return conflicts
    
    def build_identity_decision_record(
        self,
        idempotency_key: str,
        event_id: str,
        match: IdentityMatch
    ) -> Dict[str, Any]:
        """
        Build IdentityDecision record compatible with schema.
        
        Args:
            idempotency_key: Idempotency key
            event_id: Canonical event ID
            match: Identity match result
        
        Returns:
            Dictionary compatible with IdentityDecision.schema.json
        """
        evidence_obj = {
            "reason": match.reason
        }
        
        if match.matched_event_id:
            evidence_obj["matched_event_id"] = match.matched_event_id
        
        if match.conflicting_fields:
            evidence_obj["conflicting_fields"] = match.conflicting_fields
        
        if match.match_score is not None:
            evidence_obj["match_score"] = match.match_score
        
        return {
            "idempotency_key": idempotency_key,
            "decision": match.decision.value,
            "event_id": event_id,
            "decided_at": datetime.utcnow().isoformat() + "Z",
            "evidence": evidence_obj,
            "decider_version": self.version
        }
    
    def to_validation_result(
        self,
        match: IdentityMatch,
        idempotency_key: str = "",
        event_id: str = ""
    ) -> ValidationResult:
        """
        Convert IdentityMatch to ValidationResult.
        
        Args:
            match: Identity match result
            idempotency_key: Optional idempotency key for decision record
            event_id: Optional event ID for decision record
        
        Returns:
            ValidationResult (ACCEPT or REJECT with evidence)
        """
        if match.decision == IdentityDecision.ACCEPT:
            return ValidationResult.accept()
        
        # Build context with decision and optional identity_decision_record
        context = {"decision": match.decision.value}
        
        if idempotency_key and event_id:
            context["identity_decision_record"] = self.build_identity_decision_record(
                idempotency_key, event_id, match
            )
        
        # REJECT_DUPLICATE or FLAG_AMBIGUOUS → rejection with evidence
        evidence = RejectionEvidence(
            reason=match.reason,
            matched_event_id=match.matched_event_id,
            match_score=match.match_score,
            conflicting_fields=match.conflicting_fields,
            context=context
        )
        
        return ValidationResult.reject(evidence)
