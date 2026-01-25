import pytest
from core.correlation.v1.types import CorrelationRule, CorrelationEvidence
from core.correlation.v1.linker import link_events
from core.correlation.v1.scoring import score_from_evidence
from core.correlation.v1.rules_registry import RuleRegistry
from core.correlation.v1.link_store import InMemoryAppendOnlyLinkStore


def test_link_events_rejects_score_out_of_range():
    """link_events rechaza score fuera de rango."""
    rule = CorrelationRule(
        rule_id="test_rule",
        rule_version="v1",
        applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
        evidence_required=["REFERENCE_MATCH"],
        explanation_template="Test rule"
    )
    
    evidence = [CorrelationEvidence(
        evidence_type="REFERENCE_MATCH",
        pointer="test/pointer",
        details={}
    )]
    
    # Score fuera del rango superior
    with pytest.raises(ValueError, match="Score must be between 0.0 and 1.0"):
        link_events(
            source_event_id="event1",
            target_event_id="event2",
            link_type="POTENTIAL_MATCH",
            rule=rule,
            evidence=evidence,
            score=1.5,
            engine_version="v1",
            created_at="2026-01-25T00:00:00Z",
            link_id="test_link"
        )
    
    # Score fuera del rango inferior
    with pytest.raises(ValueError, match="Score must be between 0.0 and 1.0"):
        link_events(
            source_event_id="event1",
            target_event_id="event2",
            link_type="POTENTIAL_MATCH",
            rule=rule,
            evidence=evidence,
            score=-0.1,
            engine_version="v1",
            created_at="2026-01-25T00:00:00Z",
            link_id="test_link"
        )


def test_link_events_rejects_empty_evidence():
    """link_events rechaza evidence vacío."""
    rule = CorrelationRule(
        rule_id="test_rule",
        rule_version="v1",
        applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
        evidence_required=["REFERENCE_MATCH"],
        explanation_template="Test rule"
    )
    
    with pytest.raises(ValueError, match="Evidence cannot be empty"):
        link_events(
            source_event_id="event1",
            target_event_id="event2",
            link_type="POTENTIAL_MATCH",
            rule=rule,
            evidence=[],
            score=0.5,
            engine_version="v1",
            created_at="2026-01-25T00:00:00Z",
            link_id="test_link"
        )


def test_link_events_rejects_self_link():
    """link_events rechaza correlación de un evento consigo mismo."""
    rule = CorrelationRule(
        rule_id="test_rule",
        rule_version="v1",
        applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
        evidence_required=["REFERENCE_MATCH"],
        explanation_template="Test rule"
    )
    
    evidence = [CorrelationEvidence(
        evidence_type="REFERENCE_MATCH",
        pointer="test/pointer",
        details={}
    )]
    
    with pytest.raises(ValueError, match="Source and target event IDs cannot be the same"):
        link_events(
            source_event_id="event1",
            target_event_id="event1",
            link_type="POTENTIAL_MATCH",
            rule=rule,
            evidence=evidence,
            score=0.5,
            engine_version="v1",
            created_at="2026-01-25T00:00:00Z",
            link_id="test_link"
        )


def test_score_from_evidence_always_returns_valid_range():
    """score_from_evidence siempre retorna [0,1]."""
    # Evidencia que debería dar score alto
    high_evidence = [
        CorrelationEvidence(
            evidence_type="REFERENCE_MATCH",
            pointer="test/pointer1",
            details={}
        ),
        CorrelationEvidence(
            evidence_type="AMOUNT_TOLERANCE",
            pointer="test/pointer2",
            details={"tolerance_percentage": 0.001}
        )
    ]
    
    score = score_from_evidence(high_evidence)
    assert 0.0 <= score <= 1.0
    
    # Evidencia con contradicción
    contradictory_evidence = [
        CorrelationEvidence(
            evidence_type="CONTRADICTION_FLAG",
            pointer="test/pointer3",
            details={}
        )
    ]
    
    score = score_from_evidence(contradictory_evidence)
    assert 0.0 <= score <= 1.0
    
    # Sin evidencia
    score = score_from_evidence([])
    assert score == 0.0


def test_rule_registry_list_rules_stable_order():
    """RuleRegistry.list_rules orden estable (rule_id, rule_version)."""
    rules = [
        CorrelationRule(
            rule_id="rule_b",
            rule_version="v2",
            applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
            evidence_required=["REFERENCE_MATCH"],
            explanation_template="Rule B v2"
        ),
        CorrelationRule(
            rule_id="rule_a",
            rule_version="v1",
            applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
            evidence_required=["REFERENCE_MATCH"],
            explanation_template="Rule A v1"
        ),
        CorrelationRule(
            rule_id="rule_b",
            rule_version="v1",
            applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
            evidence_required=["REFERENCE_MATCH"],
            explanation_template="Rule B v1"
        )
    ]
    
    registry = RuleRegistry(rules)
    sorted_rules = registry.list_rules()
    
    # Verificar orden: (rule_a, v1), (rule_b, v1), (rule_b, v2)
    assert len(sorted_rules) == 3
    assert sorted_rules[0].rule_id == "rule_a" and sorted_rules[0].rule_version == "v1"
    assert sorted_rules[1].rule_id == "rule_b" and sorted_rules[1].rule_version == "v1"
    assert sorted_rules[2].rule_id == "rule_b" and sorted_rules[2].rule_version == "v2"


def test_append_only_link_store_rejects_duplicate_link_id():
    """AppendOnlyLinkStore rechaza link_id duplicado."""
    store = InMemoryAppendOnlyLinkStore()
    
    rule = CorrelationRule(
        rule_id="test_rule",
        rule_version="v1",
        applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
        evidence_required=["REFERENCE_MATCH"],
        explanation_template="Test rule"
    )
    
    evidence = [CorrelationEvidence(
        evidence_type="REFERENCE_MATCH",
        pointer="test/pointer",
        details={}
    )]
    
    link1 = link_events(
        source_event_id="event1",
        target_event_id="event2",
        link_type="POTENTIAL_MATCH",
        rule=rule,
        evidence=evidence,
        score=0.5,
        engine_version="v1",
        created_at="2026-01-25T00:00:00Z",
        link_id="duplicate_link"
    )
    
    link2 = link_events(
        source_event_id="event3",
        target_event_id="event4",
        link_type="POTENTIAL_MATCH",
        rule=rule,
        evidence=evidence,
        score=0.7,
        engine_version="v1",
        created_at="2026-01-25T00:00:00Z",
        link_id="duplicate_link"  # Mismo link_id
    )
    
    # Primer append debe ser exitoso
    store.append(link1)
    
    # Segundo append debe fallar por link_id duplicado
    with pytest.raises(ValueError, match="Duplicate link_id: duplicate_link"):
        store.append(link2)