"""
RFC-07: Causality Model - Data Models

Defines the internal CausalityAttribution model aligned 1:1 with the JSON Schema contract.
"""

from dataclasses import dataclass, field
from typing import Any

from core.causality.v1.enums import CausalityType


@dataclass(frozen=True)
class CausalityAttribution:
    """
    Immutable causality attribution record (RFC-07).
    
    All fields align exactly with causality_attribution.schema.json.
    Instances are validated on construction.
    """
    causality_id: str
    discrepancy_id: str
    cause_type: CausalityType
    confidence_level: float
    supporting_events: list[str] = field(default_factory=list)
    supporting_states: list[str] = field(default_factory=list)
    supporting_rules: list[str] = field(default_factory=list)
    explanation: str = ""
    attributed_at: str = ""
    model_version: str = ""

    def __post_init__(self) -> None:
        """
        Validate invariants on construction.
        
        Raises:
            ValueError: If validation fails
        """
        # Validate non-empty strings
        if not self.causality_id:
            raise ValueError("causality_id cannot be empty")
        if not self.discrepancy_id:
            raise ValueError("discrepancy_id cannot be empty")
        if not self.explanation:
            raise ValueError("explanation cannot be empty")
        # Note: attributed_at may be empty during construction (injected by engine)
        # if not self.attributed_at:
        #     raise ValueError("attributed_at cannot be empty")
        # Note: model_version may be empty during construction (injected by engine)
        # if not self.model_version:
        #     raise ValueError("model_version cannot be empty")
        
        # Validate confidence_level range
        if not (0.0 <= self.confidence_level <= 1.0):
            raise ValueError(
                f"confidence_level must be between 0.0 and 1.0, "
                f"got {self.confidence_level}"
            )
        
        # Validate evidence requirement: at least one list must be non-empty
        has_evidence = (
            len(self.supporting_events) > 0
            or len(self.supporting_states) > 0
            or len(self.supporting_rules) > 0
        )
        if not has_evidence:
            raise ValueError(
                "At least one of supporting_events, supporting_states, "
                "or supporting_rules must be non-empty"
            )
        
        # Validate enum type
        if not isinstance(self.cause_type, CausalityType):
            raise ValueError(
                f"cause_type must be CausalityType enum, "
                f"got {type(self.cause_type)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation with enum values as strings
        """
        return {
            "causality_id": self.causality_id,
            "discrepancy_id": self.discrepancy_id,
            "cause_type": self.cause_type.value,
            "confidence_level": self.confidence_level,
            "supporting_events": list(self.supporting_events),
            "supporting_states": list(self.supporting_states),
            "supporting_rules": list(self.supporting_rules),
            "explanation": self.explanation,
            "attributed_at": self.attributed_at,
            "model_version": self.model_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CausalityAttribution":
        """
        Create CausalityAttribution from dictionary.
        
        Args:
            data: Dictionary with causality attribution data
            
        Returns:
            Validated CausalityAttribution instance
            
        Raises:
            ValueError: If validation fails
        """
        return cls(
            causality_id=data["causality_id"],
            discrepancy_id=data["discrepancy_id"],
            cause_type=CausalityType(data["cause_type"]),
            confidence_level=data["confidence_level"],
            supporting_events=data.get("supporting_events", []),
            supporting_states=data.get("supporting_states", []),
            supporting_rules=data.get("supporting_rules", []),
            explanation=data["explanation"],
            attributed_at=data["attributed_at"],
            model_version=data["model_version"],
        )
