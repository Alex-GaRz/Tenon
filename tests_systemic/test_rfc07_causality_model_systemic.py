"""
RFC-07: Causality Model - Systemic Tests

Tests required scenarios: multiple plausible causes, UNKNOWN_CAUSE.
"""

import json
import pytest
from pathlib import Path
from typing import Any

from core.causality.v1 import (
    CausalityType,
    CausalityAttribution,
    CausalityEngine,
)
from core.causality.v1.rules import BaseCausalRule


class AmbiguityCausalRule(BaseCausalRule):
    """
    Rule that emits multiple plausible causes when evidence is ambiguous.
    
    Demonstrates RFC-07 requirement: do not collapse multiple causes.
    """
    
    def __init__(self):
        super().__init__("rule-ambiguity", "1.0.0")
    
    def attribute(self, discrepancy: dict[str, Any], historical_evidence: dict[str, Any]) -> list[CausalityAttribution]:
        is_ambiguous = historical_evidence.get("is_ambiguous", False)
        
        if not is_ambiguous:
            return []
        
        discrepancy_id = discrepancy.get("discrepancy_id", "unknown")
        
        # Emit multiple plausible causes
        return [
            CausalityAttribution(
                causality_id=f"cause-delay-{discrepancy_id}",
                discrepancy_id=discrepancy_id,
                cause_type=CausalityType.SOURCE_DELAY,
                confidence_level=0.65,
                supporting_events=historical_evidence.get("delayed_events", []),
                supporting_rules=[self.rule_id],
                explanation="Evidence suggests source may have delayed transmission",
                attributed_at="",  # Will be injected
                model_version="",  # Will be injected
            ),
            CausalityAttribution(
                causality_id=f"cause-mapping-{discrepancy_id}",
                discrepancy_id=discrepancy_id,
                cause_type=CausalityType.INTEGRATION_MAPPING_ERROR,
                confidence_level=0.60,
                supporting_events=historical_evidence.get("mapping_errors", []),
                supporting_rules=[self.rule_id],
                explanation="Evidence suggests integration layer mapping error",
                attributed_at="",  # Will be injected
                model_version="",  # Will be injected
            ),
        ]


class EmptyEvidenceCausalRule(BaseCausalRule):
    """
    Conservative rule that emits UNKNOWN_CAUSE when evidence is insufficient.
    
    Demonstrates RFC-07 §8.2 conservatism requirement.
    """
    
    def __init__(self):
        super().__init__("rule-conservative", "1.0.0")
    
    def attribute(self, discrepancy: dict[str, Any], historical_evidence: dict[str, Any]) -> list[CausalityAttribution]:
        has_evidence = bool(historical_evidence.get("events") or historical_evidence.get("states"))
        
        if has_evidence:
            return []  # Has evidence, might classify
        
        # Insufficient evidence: emit UNKNOWN_CAUSE
        discrepancy_id = discrepancy.get("discrepancy_id", "unknown")
        
        return [
            CausalityAttribution(
                causality_id=f"cause-unknown-{discrepancy_id}",
                discrepancy_id=discrepancy_id,
                cause_type=CausalityType.UNKNOWN_CAUSE,
                confidence_level=0.0,
                supporting_rules=[self.rule_id],
                explanation="Insufficient evidence to attribute causality",
                attributed_at="",  # Will be injected
                model_version="",  # Will be injected
            ),
        ]


class TestCausalityModelSystemic:
    """Systemic tests for required RFC-07 scenarios."""
    
    def test_multiple_plausible_causes_preserved(self):
        """
        AL-10(iii): Multiple plausible causes produce ≥2 distinct attributions.
        
        No collapse - all causes are preserved in WORM store.
        """
        engine = CausalityEngine()
        rule = AmbiguityCausalRule()
        
        discrepancy = {"discrepancy_id": "disc-ambiguous-001"}
        historical_evidence = {
            "is_ambiguous": True,
            "delayed_events": ["evt-001"],
            "mapping_errors": ["evt-002"],
        }
        
        result = engine.attribute(
            discrepancy,
            historical_evidence,
            [rule],
            "2026-01-25T10:00:00Z",
            "1.0.0"
        )
        
        # Should have at least 2 attributions
        assert len(result) >= 2
        
        # Should have distinct cause types
        cause_types = {attr.cause_type for attr in result}
        assert len(cause_types) >= 2
        
        # Should include both plausible causes
        assert CausalityType.SOURCE_DELAY in cause_types
        assert CausalityType.INTEGRATION_MAPPING_ERROR in cause_types
        
        # Both should have non-empty explanations
        for attr in result:
            assert attr.explanation
            assert attr.confidence_level > 0.0
    
    def test_insufficient_evidence_emits_unknown_cause(self):
        """
        AL-10(iv): Lack of evidence produces UNKNOWN_CAUSE with explanation.
        """
        engine = CausalityEngine()
        rule = EmptyEvidenceCausalRule()
        
        discrepancy = {"discrepancy_id": "disc-insufficient-001"}
        historical_evidence = {}  # Empty evidence
        
        result = engine.attribute(
            discrepancy,
            historical_evidence,
            [rule],
            "2026-01-25T10:00:00Z",
            "1.0.0"
        )
        
        # Should emit UNKNOWN_CAUSE
        assert len(result) == 1
        
        attr = result[0]
        assert attr.cause_type == CausalityType.UNKNOWN_CAUSE
        assert attr.confidence_level == 0.0
        assert attr.explanation  # Non-empty
        assert "insufficient" in attr.explanation.lower() or "unknown" in attr.explanation.lower()
    
    def test_scenario_multiple_causes_from_fixture(self):
        """Load and execute scenario_multiple_causes.json fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "rfc07_causality" / "scenario_multiple_causes.json"
        
        with open(fixture_path, "r", encoding="utf-8") as f:
            scenario = json.load(f)
        
        engine = CausalityEngine()
        rule = AmbiguityCausalRule()
        
        discrepancy = scenario["discrepancy"]
        historical_evidence = scenario["historical_evidence"]
        expected_outcome = scenario["expected_outcome"]
        
        result = engine.attribute(
            discrepancy,
            historical_evidence,
            [rule],
            scenario["attributed_at"],
            scenario["model_version"]
        )
        
        # Verify multiple attributions
        assert len(result) >= expected_outcome["min_attribution_count"]
        
        # Verify expected cause types are present
        cause_types = {attr.cause_type.value for attr in result}
        for expected_cause in expected_outcome["expected_cause_types"]:
            assert expected_cause in cause_types, (
                f"Expected cause_type '{expected_cause}' not found in result"
            )
    
    def test_scenario_unknown_cause_from_fixture(self):
        """Load and execute scenario_unknown_cause.json fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "rfc07_causality" / "scenario_unknown_cause.json"
        
        with open(fixture_path, "r", encoding="utf-8") as f:
            scenario = json.load(f)
        
        engine = CausalityEngine()
        rule = EmptyEvidenceCausalRule()
        
        discrepancy = scenario["discrepancy"]
        historical_evidence = scenario["historical_evidence"]
        expected_outcome = scenario["expected_outcome"]
        
        result = engine.attribute(
            discrepancy,
            historical_evidence,
            [rule],
            scenario["attributed_at"],
            scenario["model_version"]
        )
        
        # Verify UNKNOWN_CAUSE
        assert len(result) == 1
        assert result[0].cause_type.value == expected_outcome["cause_type"]
        assert result[0].confidence_level == expected_outcome["confidence_level"]
        assert result[0].explanation  # Non-empty
    
    def test_no_collapse_in_store(self):
        """
        Verify store preserves multiple attributions for same discrepancy.
        """
        from core.causality.v1 import AppendOnlyCausalityStore
        
        store = AppendOnlyCausalityStore()
        
        # Add two attributions for same discrepancy
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
        
        attr2 = CausalityAttribution(
            causality_id="cause-002",
            discrepancy_id="disc-001",  # Same discrepancy!
            cause_type=CausalityType.INTEGRATION_MAPPING_ERROR,
            confidence_level=0.65,
            supporting_rules=["rule-001"],
            explanation="Second attribution",
            attributed_at="2026-01-25T10:00:00Z",
            model_version="1.0.0",
        )
        
        store.append(attr1)
        store.append(attr2)
        
        # Both must be retrievable
        by_disc = store.list_by_discrepancy("disc-001")
        assert len(by_disc) == 2
        
        # Verify distinct cause types
        cause_types = {attr.cause_type for attr in by_disc}
        assert len(cause_types) == 2
