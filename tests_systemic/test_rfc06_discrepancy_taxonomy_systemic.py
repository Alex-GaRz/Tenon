"""
RFC-06: Discrepancy Taxonomy - Systemic Tests

Tests required scenarios: AMOUNT_MISMATCH with tolerance, MISSING_EVENT.
"""

import json
import pytest
from pathlib import Path
from typing import Any

from core.discrepancy.v1 import (
    DiscrepancyType,
    SeverityHint,
    Discrepancy,
    DiscrepancyDetector,
)
from core.discrepancy.v1.rules import BaseDiagnosticRule


class AmountMismatchRule(BaseDiagnosticRule):
    """
    Rule to detect AMOUNT_MISMATCH with floating-point tolerance.
    
    If abs(expected - observed) <= tolerance: no discrepancy
    If abs(expected - observed) > tolerance: AMOUNT_MISMATCH
    """
    
    def __init__(self, tolerance: float = 0.01):
        super().__init__("rule-amount-mismatch", "1.0.0")
        self.tolerance = tolerance
    
    def evaluate(self, money_flow: dict[str, Any], money_state_evaluation: dict[str, Any]) -> list[Discrepancy]:
        expected = money_state_evaluation.get("expected_amount")
        observed = money_state_evaluation.get("observed_amount")
        
        if expected is None or observed is None:
            return []
        
        delta = abs(expected - observed)
        
        # Within tolerance: no discrepancy
        if delta <= self.tolerance:
            return []
        
        # Outside tolerance: emit AMOUNT_MISMATCH
        flow_id = money_flow.get("flow_id", "unknown")
        
        return [
            Discrepancy(
                discrepancy_id=f"disc-amount-{flow_id}",
                flow_id=flow_id,
                discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                severity_hint=SeverityHint.HIGH if delta > 10.0 else SeverityHint.MEDIUM,
                supporting_states=[money_state_evaluation.get("state_id", "state-unknown")],
                supporting_events=[],
                supporting_links=[],
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                explanation=f"Amount mismatch: expected {expected}, observed {observed}, delta {delta:.2f} exceeds tolerance {self.tolerance}",
                detected_at="",  # Will be injected by detector
            )
        ]


class MissingEventRule(BaseDiagnosticRule):
    """
    Rule to detect MISSING_EVENT in incomplete flows.
    
    If flow is marked incomplete and expected_event is missing: MISSING_EVENT
    """
    
    def __init__(self):
        super().__init__("rule-missing-event", "1.0.0")
    
    def evaluate(self, money_flow: dict[str, Any], money_state_evaluation: dict[str, Any]) -> list[Discrepancy]:
        is_incomplete = money_flow.get("is_incomplete", False)
        expected_event_types = money_state_evaluation.get("expected_event_types", [])
        observed_event_types = money_flow.get("observed_event_types", [])
        
        if not is_incomplete:
            return []
        
        missing_events = set(expected_event_types) - set(observed_event_types)
        
        if not missing_events:
            return []
        
        flow_id = money_flow.get("flow_id", "unknown")
        
        return [
            Discrepancy(
                discrepancy_id=f"disc-missing-{flow_id}",
                flow_id=flow_id,
                discrepancy_type=DiscrepancyType.MISSING_EVENT,
                severity_hint=SeverityHint.HIGH,
                supporting_states=[],
                supporting_events=money_flow.get("observed_event_ids", []),
                supporting_links=[],
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                explanation=f"Missing expected events: {sorted(missing_events)}",
                detected_at="",  # Will be injected by detector
            )
        ]


class TestDiscrepancyTaxonomySystemic:
    """Systemic tests for required RFC-06 scenarios."""
    
    def test_amount_mismatch_within_tolerance_no_discrepancy(self):
        """
        AL-10(i): AMOUNT_MISMATCH within tolerance produces no discrepancy.
        
        Case A: abs(delta) <= tolerance => empty or NO_DISCREPANCY
        """
        detector = DiscrepancyDetector()
        rule = AmountMismatchRule(tolerance=1.0)
        
        money_flow = {"flow_id": "flow-001"}
        money_state_evaluation = {
            "state_id": "state-001",
            "expected_amount": 100.0,
            "observed_amount": 100.5,  # Delta = 0.5 <= 1.0
        }
        
        result = detector.detect(
            money_flow,
            money_state_evaluation,
            [rule],
            "2026-01-25T10:00:00Z"
        )
        
        # No discrepancy should be emitted
        assert len(result) == 0
    
    def test_amount_mismatch_outside_tolerance_emits_discrepancy(self):
        """
        AL-10(i): AMOUNT_MISMATCH outside tolerance emits AMOUNT_MISMATCH.
        
        Case B: abs(delta) > tolerance => emit AMOUNT_MISMATCH with evidence
        """
        detector = DiscrepancyDetector()
        rule = AmountMismatchRule(tolerance=1.0)
        
        money_flow = {"flow_id": "flow-002"}
        money_state_evaluation = {
            "state_id": "state-002",
            "expected_amount": 100.0,
            "observed_amount": 95.0,  # Delta = 5.0 > 1.0
        }
        
        result = detector.detect(
            money_flow,
            money_state_evaluation,
            [rule],
            "2026-01-25T10:00:00Z"
        )
        
        # Should emit one AMOUNT_MISMATCH
        assert len(result) == 1
        
        disc = result[0]
        assert disc.discrepancy_type == DiscrepancyType.AMOUNT_MISMATCH
        assert disc.flow_id == "flow-002"
        assert disc.severity_hint in [SeverityHint.MEDIUM, SeverityHint.HIGH]
        assert "state-002" in disc.supporting_states
        assert disc.explanation  # Non-empty
        assert "5.00" in disc.explanation or "5.0" in disc.explanation
        assert disc.detected_at == "2026-01-25T10:00:00Z"
    
    def test_missing_event_in_incomplete_flow(self):
        """
        AL-10(ii): MISSING_EVENT in asymmetric/incomplete flow.
        
        Emits MISSING_EVENT with evidence and explanation.
        """
        detector = DiscrepancyDetector()
        rule = MissingEventRule()
        
        money_flow = {
            "flow_id": "flow-003",
            "is_incomplete": True,
            "observed_event_types": ["INITIATED", "PENDING"],
            "observed_event_ids": ["evt-001", "evt-002"],
        }
        
        money_state_evaluation = {
            "expected_event_types": ["INITIATED", "PENDING", "COMPLETED"],
        }
        
        result = detector.detect(
            money_flow,
            money_state_evaluation,
            [rule],
            "2026-01-25T10:00:00Z"
        )
        
        # Should emit one MISSING_EVENT
        assert len(result) == 1
        
        disc = result[0]
        assert disc.discrepancy_type == DiscrepancyType.MISSING_EVENT
        assert disc.flow_id == "flow-003"
        assert disc.severity_hint == SeverityHint.HIGH
        assert len(disc.supporting_events) > 0
        assert disc.explanation  # Non-empty
        assert "COMPLETED" in disc.explanation
        assert disc.detected_at == "2026-01-25T10:00:00Z"
    
    def test_scenario_amount_mismatch_from_fixture(self):
        """Load and execute scenario_amount_mismatch.json fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "rfc06_discrepancy" / "scenario_amount_mismatch.json"
        
        with open(fixture_path, "r", encoding="utf-8") as f:
            scenario = json.load(f)
        
        detector = DiscrepancyDetector()
        rule = AmountMismatchRule(tolerance=scenario["tolerance"])
        
        for case in scenario["cases"]:
            money_flow = case["money_flow"]
            money_state_evaluation = case["money_state_evaluation"]
            expected_outcome = case["expected_outcome"]
            
            result = detector.detect(
                money_flow,
                money_state_evaluation,
                [rule],
                scenario["detected_at"]
            )
            
            if expected_outcome["discrepancy_count"] == 0:
                assert len(result) == 0, f"Expected no discrepancy for case {case['case_id']}"
            else:
                assert len(result) == expected_outcome["discrepancy_count"]
                assert result[0].discrepancy_type.value == expected_outcome["discrepancy_type"]
    
    def test_scenario_missing_event_from_fixture(self):
        """Load and execute scenario_missing_event.json fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "rfc06_discrepancy" / "scenario_missing_event.json"
        
        with open(fixture_path, "r", encoding="utf-8") as f:
            scenario = json.load(f)
        
        detector = DiscrepancyDetector()
        rule = MissingEventRule()
        
        money_flow = scenario["money_flow"]
        money_state_evaluation = scenario["money_state_evaluation"]
        expected_outcome = scenario["expected_outcome"]
        
        result = detector.detect(
            money_flow,
            money_state_evaluation,
            [rule],
            scenario["detected_at"]
        )
        
        assert len(result) == 1
        assert result[0].discrepancy_type.value == expected_outcome["discrepancy_type"]
        assert len(result[0].supporting_events) > 0
        assert result[0].explanation
