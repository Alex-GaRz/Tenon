"""
RFC-07: Causality Model - Property-Based Tests

Tests determinism, no-collapse, and conservatism properties.
"""

import pytest

from core.causality.v1 import (
    CausalityType,
    CausalityAttribution,
    CausalityEngine,
    AppendOnlyCausalityStore,
)
from core.causality.v1.rules import BaseCausalRule


class DummyCausalRule(BaseCausalRule):
    """Dummy rule for property testing."""
    
    def __init__(self, rule_id: str, rule_version: str, attributions_to_emit: list[CausalityAttribution]):
        super().__init__(rule_id, rule_version)
        self.attributions_to_emit = attributions_to_emit
    
    def attribute(self, discrepancy, historical_evidence):
        return self.attributions_to_emit


class TestCausalityModelProperties:
    """Property-based tests for RFC-07 invariants."""
    
    def test_determinism_same_inputs_same_output(self):
        """
        AL-5, RFC-07: Verify determinism - same discrepancy + evidence + rules + attributed_at
        produces identical output in same order.
        """
        engine = CausalityEngine()
        
        # Fixed inputs
        discrepancy = {"discrepancy_id": "disc-001", "flow_id": "flow-001"}
        historical_evidence = {"events": ["evt-001", "evt-002"]}
        attributed_at = "2026-01-25T10:00:00Z"
        model_version = "1.0.0"
        
        # Rule emits fixed attribution
        attr = CausalityAttribution(
            causality_id="cause-001",
            discrepancy_id="disc-001",
            cause_type=CausalityType.SOURCE_DELAY,
            confidence_level=0.8,
            supporting_rules=["rule-001"],
            explanation="Source delay detected",
            attributed_at=attributed_at,
            model_version=model_version,
        )
        
        rule = DummyCausalRule("rule-001", "1.0.0", [attr])
        rules = [rule]
        
        # Execute multiple times
        result1 = engine.attribute(discrepancy, historical_evidence, rules, attributed_at, model_version)
        result2 = engine.attribute(discrepancy, historical_evidence, rules, attributed_at, model_version)
        result3 = engine.attribute(discrepancy, historical_evidence, rules, attributed_at, model_version)
        
        # Verify identical results
        assert len(result1) == len(result2) == len(result3) == 1
        
        for r1, r2, r3 in zip(result1, result2, result3):
            assert r1.causality_id == r2.causality_id == r3.causality_id
            assert r1.cause_type == r2.cause_type == r3.cause_type
            assert r1.attributed_at == r2.attributed_at == r3.attributed_at
    
    def test_determinism_output_order_is_stable(self):
        """Verify output is deterministically sorted."""
        engine = CausalityEngine()
        
        discrepancy = {"discrepancy_id": "disc-001"}
        historical_evidence = {}
        attributed_at = "2026-01-25T10:00:00Z"
        model_version = "1.0.0"
        
        # Create attributions in deliberate disorder
        attr_z = CausalityAttribution(
            causality_id="cause-z",
            discrepancy_id="disc-001",
            cause_type=CausalityType.STATE_TRANSITION_GAP,  # S comes late
            confidence_level=0.5,
            supporting_rules=["rule-z"],
            explanation="Z attribution",
            attributed_at=attributed_at,
            model_version=model_version,
        )
        
        attr_a = CausalityAttribution(
            causality_id="cause-a",
            discrepancy_id="disc-001",
            cause_type=CausalityType.CORRELATION_AMBIGUITY,  # C comes early
            confidence_level=0.9,
            supporting_rules=["rule-a"],
            explanation="A attribution",
            attributed_at=attributed_at,
            model_version=model_version,
        )
        
        # Emit in reverse order
        rule = DummyCausalRule("rule-mixed", "1.0.0", [attr_z, attr_a])
        
        result = engine.attribute(discrepancy, historical_evidence, [rule], attributed_at, model_version)
        
        # Verify sorted output (CORRELATION_AMBIGUITY before STATE_TRANSITION_GAP alphabetically)
        assert len(result) == 2
        assert result[0].cause_type == CausalityType.CORRELATION_AMBIGUITY
        assert result[1].cause_type == CausalityType.STATE_TRANSITION_GAP
    
    def test_no_collapse_multiple_causes_preserved(self):
        """
        AL-9: Verify multiple plausible causes are NOT collapsed.
        
        If rules emit 2+ attributions for same discrepancy, all are preserved.
        """
        engine = CausalityEngine()
        
        discrepancy = {"discrepancy_id": "disc-001"}
        historical_evidence = {"ambiguous": True}
        attributed_at = "2026-01-25T10:00:00Z"
        model_version = "1.0.0"
        
        # Two plausible causes
        attr1 = CausalityAttribution(
            causality_id="cause-001",
            discrepancy_id="disc-001",
            cause_type=CausalityType.SOURCE_DELAY,
            confidence_level=0.6,
            supporting_rules=["rule-001"],
            explanation="Possible source delay",
            attributed_at=attributed_at,
            model_version=model_version,
        )
        
        attr2 = CausalityAttribution(
            causality_id="cause-002",
            discrepancy_id="disc-001",
            cause_type=CausalityType.INTEGRATION_MAPPING_ERROR,
            confidence_level=0.55,
            supporting_rules=["rule-001"],
            explanation="Possible mapping error",
            attributed_at=attributed_at,
            model_version=model_version,
        )
        
        rule = DummyCausalRule("rule-001", "1.0.0", [attr1, attr2])
        
        result = engine.attribute(discrepancy, historical_evidence, [rule], attributed_at, model_version)
        
        # Both must be preserved
        assert len(result) == 2
        assert {r.cause_type for r in result} == {
            CausalityType.SOURCE_DELAY,
            CausalityType.INTEGRATION_MAPPING_ERROR,
        }
    
    def test_worm_monotonicity_append_only_increases_cardinality(self):
        """
        AL-6, AL-9: Verify WORM property - append only increases count,
        no delete operation exists.
        """
        store = AppendOnlyCausalityStore()
        
        # Initial state
        assert len(store) == 0
        
        # Append first attribution
        attr1 = CausalityAttribution(
            causality_id="cause-001",
            discrepancy_id="disc-001",
            cause_type=CausalityType.SOURCE_DELAY,
            confidence_level=0.7,
            supporting_rules=["rule-001"],
            explanation="First attribution",
            attributed_at="2026-01-25T10:00:00Z",
            model_version="1.0.0",
        )
        store.append(attr1)
        
        assert len(store) == 1
        
        # Append second attribution for SAME discrepancy
        attr2 = CausalityAttribution(
            causality_id="cause-002",  # Different causality_id
            discrepancy_id="disc-001",  # Same discrepancy!
            cause_type=CausalityType.INTEGRATION_MAPPING_ERROR,
            confidence_level=0.6,
            supporting_rules=["rule-001"],
            explanation="Second attribution for same discrepancy",
            attributed_at="2026-01-25T10:05:00Z",
            model_version="1.0.0",
        )
        store.append(attr2)
        
        assert len(store) == 2
        
        # Both must be retrievable
        assert store.get("cause-001") == attr1
        assert store.get("cause-002") == attr2
        
        # Both must appear in list_by_discrepancy
        by_disc = store.list_by_discrepancy("disc-001")
        assert len(by_disc) == 2
        
        # Verify no delete/update methods exist
        assert not hasattr(store, "delete")
        assert not hasattr(store, "update")
        assert not hasattr(store, "upsert")
        assert not hasattr(store, "replace")
        assert not hasattr(store, "clear")
        assert not hasattr(store, "truncate")
    
    def test_worm_append_duplicate_id_fails(self):
        """
        AL-6: Verify attempting to append duplicate causality_id fails hard.
        """
        store = AppendOnlyCausalityStore()
        
        attr1 = CausalityAttribution(
            causality_id="cause-001",
            discrepancy_id="disc-001",
            cause_type=CausalityType.SOURCE_DELAY,
            confidence_level=0.7,
            supporting_rules=["rule-001"],
            explanation="First",
            attributed_at="2026-01-25T10:00:00Z",
            model_version="1.0.0",
        )
        store.append(attr1)
        
        # Try to append with same causality_id
        attr2 = CausalityAttribution(
            causality_id="cause-001",  # Duplicate!
            discrepancy_id="disc-002",
            cause_type=CausalityType.SOURCE_OMISSION,
            confidence_level=0.8,
            supporting_rules=["rule-002"],
            explanation="Second",
            attributed_at="2026-01-25T10:05:00Z",
            model_version="1.0.0",
        )
        
        with pytest.raises(ValueError, match="WORM violation.*already exists"):
            store.append(attr2)
        
        # Verify original is unchanged
        assert len(store) == 1
        assert store.get("cause-001") == attr1
    
    def test_conservatism_no_rules_emits_unknown_cause(self):
        """
        AL-8: Verify engine emits UNKNOWN_CAUSE when no rules produce attribution.
        """
        engine = CausalityEngine()
        
        discrepancy = {"discrepancy_id": "disc-001"}
        historical_evidence = {}
        
        # No rules provided
        result = engine.attribute(
            discrepancy,
            historical_evidence,
            [],  # Empty rules list
            "2026-01-25T10:00:00Z",
            "1.0.0"
        )
        
        # Should emit UNKNOWN_CAUSE
        assert len(result) == 1
        assert result[0].cause_type == CausalityType.UNKNOWN_CAUSE
        assert result[0].confidence_level == 0.0
        assert result[0].explanation  # Non-empty
    
    def test_conservatism_rule_returns_empty_emits_unknown_cause(self):
        """
        AL-8: Verify engine emits UNKNOWN_CAUSE when rules return no attributions.
        """
        engine = CausalityEngine()
        
        discrepancy = {"discrepancy_id": "disc-001"}
        historical_evidence = {}
        
        # Rule that emits nothing
        rule = DummyCausalRule("rule-silent", "1.0.0", [])
        
        result = engine.attribute(
            discrepancy,
            historical_evidence,
            [rule],
            "2026-01-25T10:00:00Z",
            "1.0.0"
        )
        
        # Should emit UNKNOWN_CAUSE
        assert len(result) == 1
        assert result[0].cause_type == CausalityType.UNKNOWN_CAUSE
    
    def test_engine_does_not_use_system_clock(self):
        """
        AL-5: Verify engine does not read system clock - attributed_at is injected.
        """
        engine = CausalityEngine()
        
        # Fixed timestamp from past
        fixed_timestamp = "2020-01-01T00:00:00Z"
        
        attr = CausalityAttribution(
            causality_id="cause-001",
            discrepancy_id="disc-001",
            cause_type=CausalityType.SOURCE_DELAY,
            confidence_level=0.7,
            supporting_rules=["rule-001"],
            explanation="Test",
            attributed_at="2026-01-25T10:00:00Z",  # Rule might set this
            model_version="1.0.0",
        )
        
        rule = DummyCausalRule("rule-001", "1.0.0", [attr])
        
        # Engine should inject the provided timestamp
        result = engine.attribute(
            {"discrepancy_id": "disc-001"},
            {},
            [rule],
            fixed_timestamp,
            "1.0.0"
        )
        
        # Result should have the injected timestamp, not current time
        assert len(result) == 1
        assert result[0].attributed_at == fixed_timestamp
