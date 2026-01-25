"""
RFC-07: Causality Model - Unit Tests

Validates contract compliance and closed taxonomy enforcement.
"""

import json
import pytest
from pathlib import Path

from core.causality.v1 import (
    CausalityType,
    CausalityAttribution,
    CausalityEngine,
    AppendOnlyCausalityStore,
)
from core.causality.v1.enums import CAUSALITY_TYPE_VALUES


class TestCausalityModelUnit:
    """Unit tests for RFC-07 contract and taxonomy enforcement."""
    
    def test_causality_type_contains_exact_rfc07_values(self):
        """
        AL-2: Verify CausalityType enum matches RFC-07 exactly.
        
        Expected values (10 total):
        - SOURCE_DELAY
        - SOURCE_OMISSION
        - SOURCE_DUPLICATION
        - SOURCE_INCONSISTENCY
        - INTEGRATION_MAPPING_ERROR
        - NORMALIZATION_LOSS
        - CORRELATION_AMBIGUITY
        - STATE_TRANSITION_GAP
        - EXTERNAL_SYSTEM_CHANGE
        - UNKNOWN_CAUSE
        """
        expected_values = {
            "SOURCE_DELAY",
            "SOURCE_OMISSION",
            "SOURCE_DUPLICATION",
            "SOURCE_INCONSISTENCY",
            "INTEGRATION_MAPPING_ERROR",
            "NORMALIZATION_LOSS",
            "CORRELATION_AMBIGUITY",
            "STATE_TRANSITION_GAP",
            "EXTERNAL_SYSTEM_CHANGE",
            "UNKNOWN_CAUSE",
        }
        
        actual_values = {ct.value for ct in CausalityType}
        
        assert actual_values == expected_values, (
            f"CausalityType enum mismatch.\n"
            f"Expected: {sorted(expected_values)}\n"
            f"Actual: {sorted(actual_values)}\n"
            f"Missing: {sorted(expected_values - actual_values)}\n"
            f"Extra: {sorted(actual_values - expected_values)}"
        )
        
        # Verify constant matches
        assert CAUSALITY_TYPE_VALUES == expected_values
    
    def test_invalid_cause_type_fails_validation(self):
        """
        AL-1: Reject cause_type outside the closed enum.
        """
        with pytest.raises(ValueError):
            CausalityAttribution(
                causality_id="cause-001",
                discrepancy_id="disc-001",
                cause_type="INVALID_CAUSE",  # type: ignore
                confidence_level=0.5,
                supporting_rules=["rule-001"],
                explanation="Test attribution",
                attributed_at="2026-01-25T10:00:00Z",
                model_version="1.0.0",
            )
    
    def test_confidence_level_out_of_range_fails_validation(self):
        """
        AL-7: Reject confidence_level outside [0.0, 1.0].
        """
        # Test < 0.0
        with pytest.raises(ValueError, match="confidence_level must be between"):
            CausalityAttribution(
                causality_id="cause-001",
                discrepancy_id="disc-001",
                cause_type=CausalityType.SOURCE_DELAY,
                confidence_level=-0.1,
                supporting_rules=["rule-001"],
                explanation="Test attribution",
                attributed_at="2026-01-25T10:00:00Z",
                model_version="1.0.0",
            )
        
        # Test > 1.0
        with pytest.raises(ValueError, match="confidence_level must be between"):
            CausalityAttribution(
                causality_id="cause-001",
                discrepancy_id="disc-001",
                cause_type=CausalityType.SOURCE_DELAY,
                confidence_level=1.5,
                supporting_rules=["rule-001"],
                explanation="Test attribution",
                attributed_at="2026-01-25T10:00:00Z",
                model_version="1.0.0",
            )
    
    def test_empty_explanation_fails_validation(self):
        """
        AL-7: Reject attribution with empty explanation.
        """
        with pytest.raises(ValueError, match="explanation cannot be empty"):
            CausalityAttribution(
                causality_id="cause-001",
                discrepancy_id="disc-001",
                cause_type=CausalityType.SOURCE_DELAY,
                confidence_level=0.5,
                supporting_rules=["rule-001"],
                explanation="",  # Empty!
                attributed_at="2026-01-25T10:00:00Z",
                model_version="1.0.0",
            )
    
    def test_no_evidence_fails_validation(self):
        """
        AL-7: Reject attribution with all evidence lists empty.
        """
        with pytest.raises(ValueError, match="At least one of supporting"):
            CausalityAttribution(
                causality_id="cause-001",
                discrepancy_id="disc-001",
                cause_type=CausalityType.SOURCE_DELAY,
                confidence_level=0.5,
                supporting_events=[],  # Empty
                supporting_states=[],  # Empty
                supporting_rules=[],   # Empty
                explanation="Test attribution",
                attributed_at="2026-01-25T10:00:00Z",
                model_version="1.0.0",
            )
    
    def test_valid_attribution_with_minimal_evidence(self):
        """Accept attribution with at least one evidence list non-empty."""
        # Only supporting_rules
        attr1 = CausalityAttribution(
            causality_id="cause-001",
            discrepancy_id="disc-001",
            cause_type=CausalityType.SOURCE_DELAY,
            confidence_level=0.75,
            supporting_rules=["rule-001"],
            explanation="Source delay detected",
            attributed_at="2026-01-25T10:00:00Z",
            model_version="1.0.0",
        )
        assert attr1.causality_id == "cause-001"
        
        # Only supporting_events
        attr2 = CausalityAttribution(
            causality_id="cause-002",
            discrepancy_id="disc-001",
            cause_type=CausalityType.SOURCE_OMISSION,
            confidence_level=0.85,
            supporting_events=["evt-001"],
            explanation="Source omission detected",
            attributed_at="2026-01-25T10:00:00Z",
            model_version="1.0.0",
        )
        assert attr2.causality_id == "cause-002"
        
        # Only supporting_states
        attr3 = CausalityAttribution(
            causality_id="cause-003",
            discrepancy_id="disc-001",
            cause_type=CausalityType.STATE_TRANSITION_GAP,
            confidence_level=0.65,
            supporting_states=["state-001"],
            explanation="State transition gap detected",
            attributed_at="2026-01-25T10:00:00Z",
            model_version="1.0.0",
        )
        assert attr3.causality_id == "cause-003"
    
    def test_attribution_serialization_preserves_schema_contract(self):
        """Verify to_dict/from_dict maintains schema compliance."""
        original = CausalityAttribution(
            causality_id="cause-001",
            discrepancy_id="disc-001",
            cause_type=CausalityType.INTEGRATION_MAPPING_ERROR,
            confidence_level=0.9,
            supporting_events=["evt-001", "evt-002"],
            supporting_rules=["rule-001"],
            explanation="Integration mapping error detected",
            attributed_at="2026-01-25T10:00:00Z",
            model_version="1.0.0",
        )
        
        # Serialize
        data = original.to_dict()
        
        # Verify enum value is string
        assert isinstance(data["cause_type"], str)
        assert isinstance(data["confidence_level"], (int, float))
        
        # Deserialize
        restored = CausalityAttribution.from_dict(data)
        
        # Verify restoration
        assert restored.causality_id == original.causality_id
        assert restored.cause_type == original.cause_type
        assert restored.confidence_level == original.confidence_level
        assert restored.explanation == original.explanation
    
    def test_schema_file_has_closed_taxonomy(self):
        """
        AL-3: Verify JSON schema has additionalProperties: false
        and closed enum for cause_type.
        """
        schema_path = Path(__file__).parents[1] / "contracts" / "causality" / "v1" / "causality_attribution.schema.json"
        
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        
        # Verify additionalProperties is false
        assert schema.get("additionalProperties") is False, (
            "Schema must have additionalProperties: false"
        )
        
        # Verify cause_type has closed enum
        cause_type_prop = schema["properties"]["cause_type"]
        assert "enum" in cause_type_prop, (
            "cause_type must have enum constraint"
        )
        
        expected_enum = [
            "SOURCE_DELAY",
            "SOURCE_OMISSION",
            "SOURCE_DUPLICATION",
            "SOURCE_INCONSISTENCY",
            "INTEGRATION_MAPPING_ERROR",
            "NORMALIZATION_LOSS",
            "CORRELATION_AMBIGUITY",
            "STATE_TRANSITION_GAP",
            "EXTERNAL_SYSTEM_CHANGE",
            "UNKNOWN_CAUSE",
        ]
        
        actual_enum = cause_type_prop["enum"]
        assert set(actual_enum) == set(expected_enum), (
            f"Schema enum mismatch.\n"
            f"Expected: {sorted(expected_enum)}\n"
            f"Actual: {sorted(actual_enum)}"
        )
    
    def test_confidence_level_boundary_values(self):
        """Verify boundary values for confidence_level."""
        # 0.0 is valid
        attr_min = CausalityAttribution(
            causality_id="cause-min",
            discrepancy_id="disc-001",
            cause_type=CausalityType.UNKNOWN_CAUSE,
            confidence_level=0.0,
            supporting_rules=["rule-001"],
            explanation="No confidence",
            attributed_at="2026-01-25T10:00:00Z",
            model_version="1.0.0",
        )
        assert attr_min.confidence_level == 0.0
        
        # 1.0 is valid
        attr_max = CausalityAttribution(
            causality_id="cause-max",
            discrepancy_id="disc-001",
            cause_type=CausalityType.SOURCE_DELAY,
            confidence_level=1.0,
            supporting_rules=["rule-001"],
            explanation="Certain",
            attributed_at="2026-01-25T10:00:00Z",
            model_version="1.0.0",
        )
        assert attr_max.confidence_level == 1.0
