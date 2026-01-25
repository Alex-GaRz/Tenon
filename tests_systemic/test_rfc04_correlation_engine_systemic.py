import pytest
import json
from pathlib import Path
from core.correlation.v1.types import CorrelationRule
from core.correlation.v1.rules_registry import RuleRegistry
from core.correlation.v1.link_store import InMemoryAppendOnlyLinkStore
from core.correlation.v1.engine import CorrelationEngine


def load_fixture(filename: str):
    """Carga un fixture JSON desde el directorio de fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "rfc04_correlation_engine" / filename
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_test_engine():
    """Crea un engine de prueba con reglas básicas."""
    rules = [
        CorrelationRule(
            rule_id="reference_match",
            rule_version="v1",
            applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
            evidence_required=["REFERENCE_MATCH"],
            explanation_template="Match by external reference"
        ),
        CorrelationRule(
            rule_id="amount_tolerance",
            rule_version="v1",
            applicability={"event_kinds": ["payment"], "direction": "UNDIRECTED"},
            evidence_required=["AMOUNT_TOLERANCE"],
            explanation_template="Match by amount tolerance"
        )
    ]
    
    registry = RuleRegistry(rules)
    store = InMemoryAppendOnlyLinkStore()
    return CorrelationEngine(registry, store, "v1")


def test_massive_reference_collisions_explicit_ambiguity():
    """
    Colisiones masivas de external_reference: engine emite múltiples POTENTIAL_MATCH 
    con distintos targets (AMBIGÜEDAD explícita vía múltiples links).
    """
    engine = create_test_engine()
    
    # Cargar fixture con colisiones
    events = load_fixture("scenario_reference_collisions.json")
    
    # Proponer links
    links = engine.propose_links(events)
    
    # Verificar que hay múltiples links para el mismo external_reference
    reference_links = {}
    for link in links:
        # Obtener el external_reference de los eventos vinculados
        source_event = next(e for e in events if e["event_id"] == link.source_event_id)
        target_event = next(e for e in events if e["event_id"] == link.target_event_id)
        
        ext_ref = source_event.get("external_reference")
        if ext_ref and ext_ref == target_event.get("external_reference"):
            if ext_ref not in reference_links:
                reference_links[ext_ref] = []
            reference_links[ext_ref].append(link)
    
    # Debe haber al menos una referencia con múltiples links (ambigüedad)
    multiple_link_refs = [ref for ref, links_list in reference_links.items() if len(links_list) > 1]
    assert len(multiple_link_refs) > 0, "Should have references with multiple potential matches"
    
    # Verificar que los links son POTENTIAL_MATCH
    for ref in multiple_link_refs:
        for link in reference_links[ref]:
            assert link.link_type == "POTENTIAL_MATCH"


def test_out_of_order_temporal_sequence_handling():
    """
    Eventos fuera de orden temporal: engine puede emitir SEQUENCE sólo si evidencia 
    TIME_WINDOW/SEQUENCE_OBSERVED existe; si no, no inventa.
    """
    engine = create_test_engine()
    
    # Cargar fixture con eventos fuera de orden
    events = load_fixture("scenario_out_of_order.json")
    
    # Proponer links
    links = engine.propose_links(events)
    
    # Verificar que no hay links de tipo SEQUENCE sin evidencia apropiada
    sequence_links = [link for link in links if link.link_type == "SEQUENCE"]
    
    for link in sequence_links:
        # Debe tener evidencia TIME_WINDOW o SEQUENCE_OBSERVED
        has_temporal_evidence = any(
            ev.evidence_type in ["TIME_WINDOW", "SEQUENCE_OBSERVED"] 
            for ev in link.evidence
        )
        assert has_temporal_evidence, f"SEQUENCE link {link.link_id} lacks temporal evidence"


def test_replay_idempotence_and_duplicate_prevention():
    """
    Replay: ejecutar propose_links() dos veces no cambia el resultado (mismos links) 
    y persist_links() del mismo set debe fallar por duplicado de link_id (idempotencia del store por ID).
    """
    engine = create_test_engine()
    
    # Usar eventos de colisiones para tener links predecibles
    events = load_fixture("scenario_reference_collisions.json")
    
    # Primera ejecución
    links1 = engine.propose_links(events)
    
    # Segunda ejecución (replay)
    links2 = engine.propose_links(events)
    
    # Deben ser idénticos
    assert len(links1) == len(links2)
    
    # Comparar link por link (ordenados por link_id para consistencia)
    links1_sorted = sorted(links1, key=lambda l: l.link_id)
    links2_sorted = sorted(links2, key=lambda l: l.link_id)
    
    for l1, l2 in zip(links1_sorted, links2_sorted):
        assert l1.link_id == l2.link_id
        assert l1.score == l2.score
        assert l1.source_event_id == l2.source_event_id
        assert l1.target_event_id == l2.target_event_id
        assert l1.link_type == l2.link_type
    
    # Persistir primera vez debe ser exitoso
    engine.persist_links(links1)
    
    # Persistir segunda vez (mismos links) debe fallar por duplicado
    if links2:  # Solo si hay links para persistir
        with pytest.raises(ValueError, match="Duplicate link_id"):
            engine.persist_links(links2)


def test_build_money_flow_includes_relevant_links():
    """
    Verificar que build_money_flow incluye todos los links relevantes y los ordena.
    """
    engine = create_test_engine()
    
    events = load_fixture("scenario_reference_collisions.json")
    
    # Proponer y persistir links
    links = engine.propose_links(events)
    engine.persist_links(links)
    
    # Obtener algunos event_ids para build_money_flow
    if len(events) >= 2:
        selected_event_ids = [events[0]["event_id"], events[1]["event_id"]]
        
        # Construir money flow
        money_flow = engine.build_money_flow("test_flow", selected_event_ids)
        
        # Verificar estructura
        assert money_flow.flow_id == "test_flow"
        assert money_flow.version == "v1"
        assert set(money_flow.event_ids) == set(selected_event_ids)
        
        # Verificar que link_ids están ordenados lexicográficamente
        assert money_flow.link_ids == sorted(money_flow.link_ids)
        
        # Verificar que todos los links incluidos son relevantes
        for link_id in money_flow.link_ids:
            # Encontrar el link correspondiente
            relevant_link = None
            for link in links:
                if link.link_id == link_id:
                    relevant_link = link
                    break
            
            assert relevant_link is not None
            # El link debe involucrar al menos uno de los event_ids seleccionados
            assert (relevant_link.source_event_id in selected_event_ids or 
                    relevant_link.target_event_id in selected_event_ids)