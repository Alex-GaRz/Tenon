import pytest
import json
from core.correlation.v1.types import CorrelationRule
from core.correlation.v1.rules_registry import RuleRegistry
from core.correlation.v1.link_store import InMemoryAppendOnlyLinkStore
from core.correlation.v1.engine import CorrelationEngine


def test_determinism_same_events_same_results():
    """
    Determinismo: misma lista de eventos (idéntica) + mismas reglas => 
    mismos link_id, score, evidence (misma serialización).
    """
    # Preparar reglas
    rules = [
        CorrelationRule(
            rule_id="reference_match",
            rule_version="v1",
            applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
            evidence_required=["REFERENCE_MATCH"],
            explanation_template="Match by external reference"
        )
    ]
    
    registry = RuleRegistry(rules)
    store1 = InMemoryAppendOnlyLinkStore()
    store2 = InMemoryAppendOnlyLinkStore()
    
    engine1 = CorrelationEngine(registry, store1, "v1")
    engine2 = CorrelationEngine(registry, store2, "v1")
    
    # Mismos eventos exactos
    events = [
        {
            "event_id": "event_001",
            "external_reference": "REF123",
            "amount": 100.0,
            "currency": "USD",
            "timestamp": "2026-01-25T10:00:00Z"
        },
        {
            "event_id": "event_002",
            "external_reference": "REF123",
            "amount": 100.0,
            "currency": "USD",
            "timestamp": "2026-01-25T10:01:00Z"
        }
    ]
    
    # Ejecutar propose_links en ambos engines
    links1 = engine1.propose_links(events)
    links2 = engine2.propose_links(events)
    
    # Deben ser idénticos
    assert len(links1) == len(links2)
    
    if links1:  # Si hay links propuestos
        link1 = links1[0]
        link2 = links2[0]
        
        assert link1.link_id == link2.link_id
        assert link1.score == link2.score
        assert len(link1.evidence) == len(link2.evidence)
        
        # Comparar evidencia elemento por elemento
        for ev1, ev2 in zip(link1.evidence, link2.evidence):
            assert ev1.evidence_type == ev2.evidence_type
            assert ev1.pointer == ev2.pointer
            assert ev1.details == ev2.details


def test_monotonicity_persist_links():
    """
    Monotonicidad: persist_links(L1) seguido de persist_links(L2) => 
    store contiene L1∪L2 y nunca pierde L1.
    """
    rules = [
        CorrelationRule(
            rule_id="reference_match",
            rule_version="v1",
            applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
            evidence_required=["REFERENCE_MATCH"],
            explanation_template="Match by external reference"
        )
    ]
    
    registry = RuleRegistry(rules)
    store = InMemoryAppendOnlyLinkStore()
    engine = CorrelationEngine(registry, store, "v1")
    
    # Primer conjunto de eventos
    events1 = [
        {
            "event_id": "event_001",
            "external_reference": "REF123",
            "amount": 100.0,
            "currency": "USD",
            "timestamp": "2026-01-25T10:00:00Z"
        },
        {
            "event_id": "event_002",
            "external_reference": "REF123",
            "amount": 100.0,
            "currency": "USD",
            "timestamp": "2026-01-25T10:01:00Z"
        }
    ]
    
    # Segundo conjunto de eventos (diferentes)
    events2 = [
        {
            "event_id": "event_003",
            "external_reference": "REF456",
            "amount": 200.0,
            "currency": "USD",
            "timestamp": "2026-01-25T11:00:00Z"
        },
        {
            "event_id": "event_004",
            "external_reference": "REF456",
            "amount": 200.0,
            "currency": "USD",
            "timestamp": "2026-01-25T11:01:00Z"
        }
    ]
    
    # Proponer y persistir primer conjunto
    links1 = engine.propose_links(events1)
    engine.persist_links(links1)
    
    # Contar links después de L1
    links_after_l1 = list(store.iter_all())
    l1_count = len(links_after_l1)
    l1_link_ids = {link.link_id for link in links_after_l1}
    
    # Proponer y persistir segundo conjunto
    links2 = engine.propose_links(events2)
    engine.persist_links(links2)
    
    # Contar links después de L1 + L2
    links_after_l1_l2 = list(store.iter_all())
    total_count = len(links_after_l1_l2)
    
    # Verificar monotonicidad
    assert total_count >= l1_count  # No perdimos links
    
    # Verificar que todos los links originales siguen ahí
    current_link_ids = {link.link_id for link in links_after_l1_l2}
    assert l1_link_ids.issubset(current_link_ids)


def test_no_self_link_collapse():
    """
    "No colapso": mismo event_id no se correlaciona consigo mismo (no self-link).
    """
    rules = [
        CorrelationRule(
            rule_id="reference_match",
            rule_version="v1",
            applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
            evidence_required=["REFERENCE_MATCH"],
            explanation_template="Match by external reference"
        )
    ]
    
    registry = RuleRegistry(rules)
    store = InMemoryAppendOnlyLinkStore()
    engine = CorrelationEngine(registry, store, "v1")
    
    # Un solo evento que podría intentar correlacionarse consigo mismo
    events = [
        {
            "event_id": "event_001",
            "external_reference": "REF123",
            "amount": 100.0,
            "currency": "USD",
            "timestamp": "2026-01-25T10:00:00Z"
        }
    ]
    
    # Proponer links
    links = engine.propose_links(events)
    
    # No debe haber self-links
    for link in links:
        assert link.source_event_id != link.target_event_id
    
    # También probar con eventos duplicados (mismo event_id)
    events_with_duplicate = [
        {
            "event_id": "event_001",
            "external_reference": "REF123",
            "amount": 100.0,
            "currency": "USD",
            "timestamp": "2026-01-25T10:00:00Z"
        },
        {
            "event_id": "event_001",  # Mismo event_id
            "external_reference": "REF123",
            "amount": 100.0,
            "currency": "USD",
            "timestamp": "2026-01-25T10:00:00Z"
        }
    ]
    
    links_duplicate = engine.propose_links(events_with_duplicate)
    
    # No debe haber self-links
    for link in links_duplicate:
        assert link.source_event_id != link.target_event_id