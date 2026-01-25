"""
RFC-06: Discrepancy Taxonomy - Property-Based Tests

Tests determinism, monotonicity (WORM), and conservatism properties.
"""

import pytest
from datetime import datetime

from core.discrepancy.v1 import (
    DiscrepancyType,
    SeverityHint,
    Discrepancy,
    DiscrepancyDetector,
    AppendOnlyDiscrepancyStore,
)
from core.discrepancy.v1.rules import BaseDiagnosticRule


class DummyRule(BaseDiagnosticRule):
    """Dummy rule for property testing."""
    
    def __init__(self, rule_id: str, rule_version: str, discrepancies_to_emit: list[Discrepancy]):
        super().__init__(rule_id, rule_version)
        self.discrepancies_to_emit = discrepancies_to_emit
    
    def evaluate(self, money_flow, money_state_evaluation):
        return self.discrepancies_to_emit


class TestDiscrepancyTaxonomyProperties:
    """Property-based tests for RFC-06 invariants."""
    
    def test_determinism_same_inputs_same_output(self):
        """
        AL-5, RFC-06: Verify determinism - same evidence + rules + detected_at
        produces identical output in same order.
        """
        detector = DiscrepancyDetector()
        
        # Fixed inputs
        money_flow = {"flow_id": "flow-001", "amount": 100.0}
        money_state_evaluation = {"expected": 100.0, "observed": 95.0}
        detected_at = "2026-01-25T10:00:00Z"
        
        # Rule emits fixed discrepancy
        disc = Discrepancy(
            discrepancy_id="disc-001",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
            severity_hint=SeverityHint.HIGH,
            supporting_events=["evt-001"],
            rule_id="rule-001",
            rule_version="1.0.0",
            explanation="Amount mismatch",
            detected_at=detected_at,
        )
        
        rule = DummyRule("rule-001", "1.0.0", [disc])
        rules = [rule]
        
        # Execute multiple times
        result1 = detector.detect(money_flow, money_state_evaluation, rules, detected_at)
        result2 = detector.detect(money_flow, money_state_evaluation, rules, detected_at)
        result3 = detector.detect(money_flow, money_state_evaluation, rules, detected_at)
        
        # Verify identical results
        assert len(result1) == len(result2) == len(result3) == 1
        
        for r1, r2, r3 in zip(result1, result2, result3):
            assert r1.discrepancy_id == r2.discrepancy_id == r3.discrepancy_id
            assert r1.discrepancy_type == r2.discrepancy_type == r3.discrepancy_type
            assert r1.detected_at == r2.detected_at == r3.detected_at
    
    def test_determinism_output_order_is_stable(self):
        """Verify output is deterministically sorted."""
        detector = DiscrepancyDetector()
        
        money_flow = {"flow_id": "flow-001"}
        money_state_evaluation = {}
        detected_at = "2026-01-25T10:00:00Z"
        
        # Create discrepancies in deliberate disorder (with consistent rule_id)
        disc_z = Discrepancy(
            discrepancy_id="disc-z",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.TIMING_DELAY,  # T comes late
            severity_hint=SeverityHint.LOW,
            supporting_events=["evt-z"],
            rule_id="rule-mixed",  # Must match emitting rule
            rule_version="1.0.0",
            explanation="Z discrepancy",
            detected_at=detected_at,
        )
        
        disc_a = Discrepancy(
            discrepancy_id="disc-a",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,  # A comes early
            severity_hint=SeverityHint.HIGH,
            supporting_events=["evt-a"],
            rule_id="rule-mixed",  # Must match emitting rule
            rule_version="1.0.0",
            explanation="A discrepancy",
            detected_at=detected_at,
        )
        
        # Emit in reverse order
        rule = DummyRule("rule-mixed", "1.0.0", [disc_z, disc_a])
        
        result = detector.detect(money_flow, money_state_evaluation, [rule], detected_at)
        
        # Verify sorted output (AMOUNT_MISMATCH before TIMING_DELAY alphabetically)
        assert len(result) == 2
        assert result[0].discrepancy_type == DiscrepancyType.AMOUNT_MISMATCH
        assert result[1].discrepancy_type == DiscrepancyType.TIMING_DELAY
    
    def test_worm_monotonicity_append_only_increases_cardinality(self):
        """
        AL-6, AL-9: Verify WORM property - append only increases count,
        no delete operation exists.
        """
        store = AppendOnlyDiscrepancyStore()
        
        # Initial state
        assert len(store) == 0
        assert len(store.iter_all()) == 0
        
        # Append first discrepancy
        disc1 = Discrepancy(
            discrepancy_id="disc-001",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.MISSING_EVENT,
            severity_hint=SeverityHint.MEDIUM,
            supporting_events=["evt-001"],
            rule_id="rule-001",
            rule_version="1.0.0",
            explanation="First discrepancy",
            detected_at="2026-01-25T10:00:00Z",
        )
        store.append(disc1)
        
        assert len(store) == 1
        
        # Append second discrepancy
        disc2 = Discrepancy(
            discrepancy_id="disc-002",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
            severity_hint=SeverityHint.HIGH,
            supporting_events=["evt-002"],
            rule_id="rule-001",
            rule_version="1.0.0",
            explanation="Second discrepancy",
            detected_at="2026-01-25T10:05:00Z",
        )
        store.append(disc2)
        
        assert len(store) == 2
        
        # Verify both are retrievable
        assert store.get("disc-001") == disc1
        assert store.get("disc-002") == disc2
        
        # Verify no delete/update methods exist
        assert not hasattr(store, "delete")
        assert not hasattr(store, "update")
        assert not hasattr(store, "upsert")
        assert not hasattr(store, "replace")
        assert not hasattr(store, "clear")
        assert not hasattr(store, "truncate")
    
    def test_worm_append_duplicate_id_fails(self):
        """
        AL-6: Verify attempting to append duplicate discrepancy_id fails hard.
        """
        store = AppendOnlyDiscrepancyStore()
        
        disc1 = Discrepancy(
            discrepancy_id="disc-001",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.ORPHAN_EVENT,
            severity_hint=SeverityHint.LOW,
            supporting_events=["evt-001"],
            rule_id="rule-001",
            rule_version="1.0.0",
            explanation="First",
            detected_at="2026-01-25T10:00:00Z",
        )
        store.append(disc1)
        
        # Try to append with same ID
        disc2 = Discrepancy(
            discrepancy_id="disc-001",  # Duplicate!
            flow_id="flow-002",
            discrepancy_type=DiscrepancyType.DUPLICATE_EVENT,
            severity_hint=SeverityHint.MEDIUM,
            supporting_events=["evt-002"],
            rule_id="rule-002",
            rule_version="1.0.0",
            explanation="Second",
            detected_at="2026-01-25T10:05:00Z",
        )
        
        with pytest.raises(ValueError, match="WORM violation.*already exists"):
            store.append(disc2)
        
        # Verify original is unchanged
        assert len(store) == 1
        assert store.get("disc-001") == disc1
    
    def test_conservatism_insufficient_evidence_is_used(self):
        """
        AL-8: Verify system uses INSUFFICIENT_EVIDENCE when classification
        cannot be defended.
        """
        # Create discrepancy with INSUFFICIENT_EVIDENCE type
        disc = Discrepancy(
            discrepancy_id="disc-001",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.INSUFFICIENT_EVIDENCE,
            severity_hint=SeverityHint.UNKNOWN,
            supporting_events=["evt-001"],
            rule_id="rule-conservative",
            rule_version="1.0.0",
            explanation="Cannot classify with available evidence",
            detected_at="2026-01-25T10:00:00Z",
        )
        
        # Verify it's a valid discrepancy
        assert disc.discrepancy_type == DiscrepancyType.INSUFFICIENT_EVIDENCE
        
        # Verify detector accepts it
        detector = DiscrepancyDetector()
        rule = DummyRule("rule-conservative", "1.0.0", [disc])
        
        result = detector.detect(
            {},
            {},
            [rule],
            "2026-01-25T10:00:00Z"
        )
        
        assert len(result) == 1
        assert result[0].discrepancy_type == DiscrepancyType.INSUFFICIENT_EVIDENCE
    
    def test_detector_does_not_use_system_clock(self):
        """
        AL-5: Verify detector does not read system clock - detected_at is injected.
        """
        detector = DiscrepancyDetector()
        
        # Fixed timestamp from past
        fixed_timestamp = "2020-01-01T00:00:00Z"
        
        disc = Discrepancy(
            discrepancy_id="disc-001",
            flow_id="flow-001",
            discrepancy_type=DiscrepancyType.MISSING_EVENT,
            severity_hint=SeverityHint.MEDIUM,
            supporting_events=["evt-001"],
            rule_id="rule-001",
            rule_version="1.0.0",
            explanation="Test",
            detected_at="2026-01-25T10:00:00Z",  # Rule might set this
        )
        
        rule = DummyRule("rule-001", "1.0.0", [disc])
        
        # Detector should inject the provided timestamp
        result = detector.detect({}, {}, [rule], fixed_timestamp)
        
        # Result should have the injected timestamp, not current time
        assert len(result) == 1
        assert result[0].detected_at == fixed_timestamp
