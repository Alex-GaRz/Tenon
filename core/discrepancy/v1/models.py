"""
RFC-06: Discrepancy Taxonomy - Data Models

Defines the internal Discrepancy model aligned 1:1 with the JSON Schema contract.
"""

from dataclasses import dataclass, field
from typing import Any

from core.discrepancy.v1.enums import DiscrepancyType, SeverityHint


@dataclass(frozen=True)
class Discrepancy:
    """
    Immutable discrepancy record (RFC-06).
    
    All fields align exactly with discrepancy.schema.json.
    Instances are validated on construction.
    """
    discrepancy_id: str
    flow_id: str
    discrepancy_type: DiscrepancyType
    severity_hint: SeverityHint
    supporting_states: list[str] = field(default_factory=list)
    supporting_events: list[str] = field(default_factory=list)
    supporting_links: list[str] = field(default_factory=list)
    rule_id: str = ""
    rule_version: str = ""
    explanation: str = ""
    detected_at: str = ""

    def __post_init__(self) -> None:
        """
        Validate invariants on construction.
        
        Raises:
            ValueError: If validation fails
        """
        # Validate non-empty strings
        if not self.discrepancy_id:
            raise ValueError("discrepancy_id cannot be empty")
        if not self.flow_id:
            raise ValueError("flow_id cannot be empty")
        if not self.rule_id:
            raise ValueError("rule_id cannot be empty")
        if not self.rule_version:
            raise ValueError("rule_version cannot be empty")
        if not self.explanation:
            raise ValueError("explanation cannot be empty")
        # Note: detected_at may be empty during construction (injected by detector)
        # if not self.detected_at:
        #     raise ValueError("detected_at cannot be empty")
        
        # Validate evidence requirement: at least one list must be non-empty
        has_evidence = (
            len(self.supporting_states) > 0
            or len(self.supporting_events) > 0
            or len(self.supporting_links) > 0
        )
        if not has_evidence:
            raise ValueError(
                "At least one of supporting_states, supporting_events, "
                "or supporting_links must be non-empty"
            )
        
        # Validate enum types
        if not isinstance(self.discrepancy_type, DiscrepancyType):
            raise ValueError(
                f"discrepancy_type must be DiscrepancyType enum, "
                f"got {type(self.discrepancy_type)}"
            )
        if not isinstance(self.severity_hint, SeverityHint):
            raise ValueError(
                f"severity_hint must be SeverityHint enum, "
                f"got {type(self.severity_hint)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation with enum values as strings
        """
        return {
            "discrepancy_id": self.discrepancy_id,
            "flow_id": self.flow_id,
            "discrepancy_type": self.discrepancy_type.value,
            "severity_hint": self.severity_hint.value,
            "supporting_states": list(self.supporting_states),
            "supporting_events": list(self.supporting_events),
            "supporting_links": list(self.supporting_links),
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "explanation": self.explanation,
            "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Discrepancy":
        """
        Create Discrepancy from dictionary.
        
        Args:
            data: Dictionary with discrepancy data
            
        Returns:
            Validated Discrepancy instance
            
        Raises:
            ValueError: If validation fails
        """
        return cls(
            discrepancy_id=data["discrepancy_id"],
            flow_id=data["flow_id"],
            discrepancy_type=DiscrepancyType(data["discrepancy_type"]),
            severity_hint=SeverityHint(data["severity_hint"]),
            supporting_states=data.get("supporting_states", []),
            supporting_events=data.get("supporting_events", []),
            supporting_links=data.get("supporting_links", []),
            rule_id=data["rule_id"],
            rule_version=data["rule_version"],
            explanation=data["explanation"],
            detected_at=data["detected_at"],
        )
