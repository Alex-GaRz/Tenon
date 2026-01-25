"""
RFC-11 Section 4.2 - IngestDeclaration Interface
Minimal interface for emission without canonical field mutations
"""

from typing import Dict, Any, Optional


class IngestDeclaration:
    """
    RFC-11 Section 4.2 - IngestDeclaration
    Minimal interface for adapter emission
    """
    
    # RFC-11 Section 4.2 - Prohibited fields (canonical/derived)
    PROHIBITED_FIELDS = {
        "event_type",
        "state",
        "discrepancy",
        "cause",
    }
    
    def __init__(
        self,
        source_system: str,
        payload_raw: Any,
        payload_format: str,
        adapter_version: str,
        source_event_id: Optional[str] = None,
        external_reference: Optional[str] = None,
        source_timestamp: Optional[str] = None,
    ):
        """
        RFC-11 Section 4.2 - Allowed fields only
        
        Args:
            source_system: System identifier
            payload_raw: Raw payload without mutation (Section 3.2)
            payload_format: Format of payload (JSON, CSV, XML, PDF, OTHER)
            adapter_version: Version of adapter
            source_event_id: Optional external event ID
            external_reference: Optional external reference
            source_timestamp: Optional timestamp from source
        """
        self.source_system = source_system
        self.payload_raw = payload_raw
        self.payload_format = payload_format
        self.adapter_version = adapter_version
        self.source_event_id = source_event_id
        self.external_reference = external_reference
        self.source_timestamp = source_timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation
        """
        result = {
            "source_system": self.source_system,
            "payload_raw": self.payload_raw,
            "payload_format": self.payload_format,
            "adapter_version": self.adapter_version,
        }
        
        if self.source_event_id is not None:
            result["source_event_id"] = self.source_event_id
        
        if self.external_reference is not None:
            result["external_reference"] = self.external_reference
        
        if self.source_timestamp is not None:
            result["source_timestamp"] = self.source_timestamp
        
        return result
    
    @classmethod
    def validate_no_prohibited_fields(cls, data: Dict[str, Any]) -> None:
        """
        RFC-11 Section 4.2 - Validate no prohibited fields present
        
        Raises:
            ValueError: If prohibited fields found
        """
        found_prohibited = set(data.keys()) & cls.PROHIBITED_FIELDS
        if found_prohibited:
            raise ValueError(
                f"Prohibited canonical fields found: {found_prohibited}"
            )
