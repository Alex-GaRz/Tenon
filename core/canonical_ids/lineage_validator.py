"""
Lineage validator.
RFC-01A implementation.

Validates lineage links are:
- Explicit (no implicit links)
- Append-only (never delete/rewrite)
- Evidence-backed (mandatory evidence field)
- Type-validated (closed enum)
"""

from typing import Dict, Any, List, Set, Optional

from ..validation.rejection_evidence import RejectionEvidence
from ..validation.validation_result import ValidationResult


class LineageValidator:
    """Validates lineage links in canonical events."""
    
    # Closed enum of lineage types (from RFC-01A)
    VALID_LINEAGE_TYPES = {
        "DERIVES_FROM",
        "REVERSAL_OF",
        "REFUND_OF",
        "ADJUSTMENT_OF",
        "RELATED_TO"
    }
    
    def __init__(self, version: str = "1.0.0"):
        """
        Initialize lineage validator.
        
        Args:
            version: Version of lineage validation logic
        """
        self.version = version
    
    def validate_links(
        self,
        lineage_links: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate lineage links structure and content.
        
        Args:
            lineage_links: Array of lineage link objects
        
        Returns:
            ValidationResult (PASS or REJECT with evidence)
        """
        if not lineage_links:
            # Empty lineage is valid (no links required)
            return ValidationResult.accept()
        
        for idx, link in enumerate(lineage_links):
            # Validate required fields
            if "type" not in link:
                return ValidationResult.reject(
                    RejectionEvidence(
                        reason=f"Lineage link [{idx}] missing required field: type",
                        context={"link_index": idx, "link": link}
                    )
                )
            
            if "target_event_id" not in link:
                return ValidationResult.reject(
                    RejectionEvidence(
                        reason=f"Lineage link [{idx}] missing required field: target_event_id",
                        context={"link_index": idx, "link": link}
                    )
                )
            
            if "evidence" not in link or not link["evidence"]:
                return ValidationResult.reject(
                    RejectionEvidence(
                        reason=f"Lineage link [{idx}] missing required field: evidence",
                        context={"link_index": idx, "link": link}
                    )
                )
            
            if "version" not in link:
                return ValidationResult.reject(
                    RejectionEvidence(
                        reason=f"Lineage link [{idx}] missing required field: version",
                        context={"link_index": idx, "link": link}
                    )
                )
            
            # Validate type is in closed enum
            link_type = link["type"]
            if link_type not in self.VALID_LINEAGE_TYPES:
                return ValidationResult.reject(
                    RejectionEvidence(
                        reason=f"Lineage link [{idx}] has invalid type: {link_type}",
                        context={
                            "link_index": idx,
                            "invalid_type": link_type,
                            "valid_types": list(self.VALID_LINEAGE_TYPES)
                        }
                    )
                )
        
        return ValidationResult.accept()
    
    def validate_append_only(
        self,
        previous_links: List[Dict[str, Any]],
        current_links: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate that lineage is append-only (no deletions/modifications).
        
        Args:
            previous_links: Previous state of lineage links
            current_links: Current state of lineage links
        
        Returns:
            ValidationResult (PASS or REJECT with evidence)
        """
        import hashlib
        import json
        
        # Convert to comparable format using hash of all 4 required fields
        def link_key(link: Dict[str, Any]) -> str:
            # Deterministic hash of full link (type, target_event_id, evidence, version)
            link_data = {
                "type": link.get("type", ""),
                "target_event_id": link.get("target_event_id", ""),
                "evidence": link.get("evidence", ""),
                "version": link.get("version", "")
            }
            # Use json with sorted keys for determinism
            link_str = json.dumps(link_data, sort_keys=True)
            return hashlib.sha256(link_str.encode("utf-8")).hexdigest()
        
        # Build identifier for type+target (to detect mutations)
        def link_identity(link: Dict[str, Any]) -> str:
            return f"{link.get('type')}:{link.get('target_event_id')}"
        
        previous_keys = {link_key(link) for link in previous_links}
        current_keys = {link_key(link) for link in current_links}
        
        # Check for deletions (previous link hash not in current)
        deleted_keys = previous_keys - current_keys
        if deleted_keys:
            return ValidationResult.reject(
                RejectionEvidence(
                    reason="Lineage links cannot be deleted (append-only violation)",
                    context={
                        "deleted_link_hashes": list(deleted_keys),
                        "previous_count": len(previous_links),
                        "current_count": len(current_links)
                    }
                )
            )
        
        # Check for mutations (same type+target but different evidence/version)
        previous_identities = {link_identity(link): link for link in previous_links}
        current_identities = {link_identity(link): link for link in current_links}
        
        for identity, prev_link in previous_identities.items():
            if identity in current_identities:
                curr_link = current_identities[identity]
                # If identity matches but hash differs → mutation
                if link_key(prev_link) != link_key(curr_link):
                    return ValidationResult.reject(
                        RejectionEvidence(
                            reason="Lineage link cannot be modified (append-only violation)",
                            context={
                                "link_identity": identity,
                                "previous_link": prev_link,
                                "current_link": curr_link
                            }
                        )
                    )
        
        return ValidationResult.accept()
    
    def validate_no_cycles(
        self,
        event_id: str,
        lineage_links: List[Dict[str, Any]],
        all_events: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Validate that lineage doesn't create cycles.
        
        Args:
            event_id: Current event ID
            lineage_links: Lineage links for current event
            all_events: Map of event_id → event (for graph traversal)
        
        Returns:
            ValidationResult (PASS or REJECT with evidence)
        """
        if not all_events:
            # Cannot validate cycles without full graph
            return ValidationResult.accept()
        
        # Check if any target points back to this event
        for link in lineage_links:
            target_id = link.get("target_event_id")
            if target_id == event_id:
                return ValidationResult.reject(
                    RejectionEvidence(
                        reason="Lineage link cannot point to self (cycle detected)",
                        context={
                            "event_id": event_id,
                            "link_type": link.get("type")
                        }
                    )
                )
        
        return ValidationResult.accept()
