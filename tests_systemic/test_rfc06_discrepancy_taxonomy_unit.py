"""
RFC-06: Discrepancy Taxonomy - Unit Tests

Validates contract compliance and closed taxonomy enforcement.
"""

import json
import pytest
from pathlib import Path

from core.discrepancy.v1 import (
    DiscrepancyType,
    SeverityHint,
    Discrepancy,
    DiscrepancyDetector,
    AppendOnlyDiscrepancyStore,
)
from core.discrepancy.v1.enums import DISCREPANCY_TYPE_VALUES, SEVERITY_HINT_VALUES


class TestDiscrepancyTaxonomyUnit:
    """Unit tests for RFC-06 contract and taxonomy enforcement."""
    
    def test_discrepancy_type_contains_exact_rfc06_values(self):
        """
        AL-2: Verify DiscrepancyType enum matches RFC-06 exactly.
        
        Expected values (11 total):
        - NO_DISCREPANCY
        - TIMING_DELAY
        - MISSING_EVENT
        - DUPLICATE_EVENT
        - AMOUNT_MISMATCH
        - CURRENCY_MISMATCH
        - STATUS_CONFLICT
        - UNEXPECTED_REVERSAL
        - ORPHAN_EVENT
        - INCONSISTENT_FLOW
        - INSUFFICIENT_EVIDENCE
        """
        expected_values = {
            "NO_DISCREPANCY",
            "TIMING_DELAY",
            "MISSING_EVENT",
            "DUPLICATE_EVENT",
            "AMOUNT_MISMATCH",
            "CURRENCY_MISMATCH",
            "STATUS_CONFLICT",
            "UNEXPECTED_REVERSAL",
            "ORPHAN_EVENT",
            "INCONSISTENT_FLOW",
            "INSUFFICIENT_EVIDENCE",
        }
        
        actual_values = {dt.value for dt in DiscrepancyType}
        
        assert actual_values == expected_values, (
            f"DiscrepancyType enum mismatch.\n"
            f"Expected: {sorted(expected_values)}\n"
            f"Actual: {sorted(actual_values)}\n"
            f"Missing: {sorted(expected_values - actual_values)}\n"
            f"Extra: {sorted(actual_values - expected_values)}"
        )
        
        # Verify constant matches
        assert DISCREPANCY_TYPE_VALUES == expected_values
    
    def test_severity_hint_contains_exact_values(self):
        """Verify SeverityHint enum matches contract."""
        expected_values = {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}
        actual_values = {sh.value for sh in SeverityHint}
        
        assert actual_values == expected_values
        assert SEVERITY_HINT_VALUES == expected_values
    
    def test_invalid_discrepancy_type_fails_schema_validation(self):
        """
        AL-1: Reject discrepancy_type outside the closed enum.
        """
        # Test at Enum level
        from core.discrepancy.v1.enums import validate_discrepancy_type
        
        with pytest.raises(ValueError, match="Invalid.*discrepancy_type"):
            validate_discrepancy_type("INVALID_TYPE")
        
        # Also test that using wrong type in constructor fails
        with pytest.raises((ValueError, AttributeError)):
            Discrepancy(
                discrepancy_id="disc-001",
                flow_id="flow-001",
                discrepancy_type="INVALID_TYPE",  # type: ignore
                severity_hint=SeverityHint.MEDIUM,
                supporting_events=["evt-001"],
                rule_id="rule-001",
                rule_version="1.0.0",
                explanation="Test discrepancy",
                detected_at="2026-01-25T10:00:00Z",
            )
    
    def test_invalid_severity_hint_fails_validation(self):
        """Reject severity_hint outside the closed enum."""
        with pytest.raises(ValueError):
            Discrepancy(
                discrepancy_id="disc-001",
                flow_id="flow-001",
                discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                severity_hint="CRITICAL",  # type: ignore
                supporting_events=["evt-001"],
                rule_id="rule-001",
                rule_version="1.0.0",
                explanation="Test discrepancy",
                detected_at="2026-01-25T10:00:00Z",
            )
    
    def test_empty_explanation_fails_validation(self):
        """
        AL-7: Reject discrepancy with empty explanation.
        """
        with pytest.raises(ValueError, match="explanation cannot be empty"):
            Discrepancy(
                discrepancy_id="disc-001",
                flow_id="flow-001",
                discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                severity_hint=SeverityHint.MEDIUM,
                supporting_events=["evt-001"],
                rule_id="rule-001",
                rule_version="1.0.0",
                explanation="",  # Empty!
                detected_at="2026-01-25T10:00:00Z",
            )
    
    def test_no_evidence_fails_validation(self):
        """
        AL-7: Reject discrepancy with all evidence lists empty.
        """
        with pytest.raises(ValueError, match="At least one of supporting"):
            Discrepancy(
                discrepancy_id="disc-001",
                flow_id="flow-001",
                discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                severity_hint=SeverityHint.MEDIUM,
                supporting_states=[],  # Empty
                supporting_events=[],  # Empty
                supporting_links=[],   # Empty
                rule_id="rule-001",
                rule_version="1.0.0",
                explanation="Test discrepancy",
                detected_at="2026-01-25T10:00:00Z",
            )
    
    def test_valid_discrepancy_with_minimal_evidence(self):
        """Accept discrepancy with at least one evidence list non-empty."""
        # Only supporting_events
        disc1 = Discrepancy(
            discrepancy_id="disc-001",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.MISSING_EVENT,
            severity_hint=SeverityHint.HIGH,
            supporting_events=["evt-001"],
            rule_id="rule-001",
            rule_version="1.0.0",
            explanation="Missing expected event",
            detected_at="2026-01-25T10:00:00Z",
        )
        assert disc1.discrepancy_id == "disc-001"
        
        # Only supporting_states
        disc2 = Discrepancy(
            discrepancy_id="disc-002",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.STATUS_CONFLICT,
            severity_hint=SeverityHint.MEDIUM,
            supporting_states=["state-001"],
            rule_id="rule-001",
            rule_version="1.0.0",
            explanation="State conflict detected",
            detected_at="2026-01-25T10:00:00Z",
        )
        assert disc2.discrepancy_id == "disc-002"
        
        # Only supporting_links
        disc3 = Discrepancy(
            discrepancy_id="disc-003",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.ORPHAN_EVENT,
            severity_hint=SeverityHint.LOW,
            supporting_links=["link-001"],
            rule_id="rule-001",
            rule_version="1.0.0",
            explanation="Orphaned event detected",
            detected_at="2026-01-25T10:00:00Z",
        )
        assert disc3.discrepancy_id == "disc-003"
    
    def test_discrepancy_serialization_preserves_schema_contract(self):
        """Verify to_dict/from_dict maintains schema compliance."""
        original = Discrepancy(
            discrepancy_id="disc-001",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
            severity_hint=SeverityHint.HIGH,
            supporting_events=["evt-001", "evt-002"],
            supporting_states=["state-001"],
            rule_id="rule-001",
            rule_version="1.0.0",
            explanation="Amount mismatch detected",
            detected_at="2026-01-25T10:00:00Z",
        )
        
        # Serialize
        data = original.to_dict()
        
        # Verify enum values are strings
        assert isinstance(data["discrepancy_type"], str)
        assert isinstance(data["severity_hint"], str)
        
        # Deserialize
        restored = Discrepancy.from_dict(data)
        
        # Verify restoration
        assert restored.discrepancy_id == original.discrepancy_id
        assert restored.discrepancy_type == original.discrepancy_type
        assert restored.severity_hint == original.severity_hint
        assert restored.explanation == original.explanation
    
    def test_schema_file_has_closed_taxonomy(self):
        """
        AL-3: Verify JSON schema has additionalProperties: false
        and closed enum for discrepancy_type.
        """
        schema_path = Path(__file__).parents[1] / "contracts" / "discrepancy" / "v1" / "discrepancy.schema.json"
        
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        
        # Verify additionalProperties is false
        assert schema.get("additionalProperties") is False, (
            "Schema must have additionalProperties: false"
        )
        
        # Verify discrepancy_type has closed enum
        discrepancy_type_prop = schema["properties"]["discrepancy_type"]
        assert "enum" in discrepancy_type_prop, (
            "discrepancy_type must have enum constraint"
        )
        
        expected_enum = [
            "NO_DISCREPANCY",
            "TIMING_DELAY",
            "MISSING_EVENT",
            "DUPLICATE_EVENT",
            "AMOUNT_MISMATCH",
            "CURRENCY_MISMATCH",
            "STATUS_CONFLICT",
            "UNEXPECTED_REVERSAL",
            "ORPHAN_EVENT",
            "INCONSISTENT_FLOW",
            "INSUFFICIENT_EVIDENCE",
        ]
        
        actual_enum = discrepancy_type_prop["enum"]
        assert set(actual_enum) == set(expected_enum), (
            f"Schema enum mismatch.\n"
            f"Expected: {sorted(expected_enum)}\n"
            f"Actual: {sorted(actual_enum)}"
        )
