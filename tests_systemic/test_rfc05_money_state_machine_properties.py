import pytest
from core.money_state.v1.types import MoneyStateEvaluation
from core.money_state.v1.transitions import list_transitions
from core.money_state.v1.state_store import InMemoryAppendOnlyStateStore
from core.money_state.v1.machine import MoneyStateMachine


def test_determinism_same_inputs_identical_evaluation():
    """
    Determinismo: mismo flujo + mismos eventos + mismos links + mismas versiones + 
    mismo evaluated_at/evidence_pointer => evaluación idéntica (state, reason, confidence).
    """
    transitions = list_transitions()
    store1 = InMemoryAppendOnlyStateStore()
    store2 = InMemoryAppendOnlyStateStore()
    
    machine1 = MoneyStateMachine(transitions, store1, "v1", "v1")
    machine2 = MoneyStateMachine(transitions, store2, "v1", "v1")
    
    # Inputs idénticos
    flow_id = "test_flow_001"
    canonical_events = [
        {
            "event_id": "event_001",
            "event_type": "payment_initiated",
            "amount": 100.0,
            "currency": "USD",
            "timestamp": "2026-01-25T10:00:00Z"
        },
        {
            "event_id": "event_002",
            "event_type": "settlement_confirmed",
            "amount": 100.0,
            "currency": "USD",
            "timestamp": "2026-01-25T10:05:00Z"
        }
    ]
    correlation_links = [
        {
            "link_id": "link_001",
            "source_event_id": "event_001",
            "target_event_id": "event_002",
            "link_type": "SEQUENCE"
        }
    ]
    evaluated_at = "2026-01-25T12:00:00Z"
    evidence_pointer = "evidence/determinism_test"
    
    # Ejecutar evaluación en ambas máquinas
    eval1 = machine1.evaluate(
        flow_id=flow_id,
        canonical_events=canonical_events,
        correlation_links=correlation_links,
        evaluated_at=evaluated_at,
        evidence_pointer=evidence_pointer
    )
    
    eval2 = machine2.evaluate(
        flow_id=flow_id,
        canonical_events=canonical_events,
        correlation_links=correlation_links,
        evaluated_at=evaluated_at,
        evidence_pointer=evidence_pointer
    )
    
    # Verificar que las evaluaciones son idénticas
    assert eval1.evaluation_id == eval2.evaluation_id
    assert eval1.state == eval2.state
    assert eval1.transition_reason == eval2.transition_reason
    assert eval1.confidence_level == eval2.confidence_level
    assert eval1.flow_id == eval2.flow_id
    assert eval1.event_id == eval2.event_id
    assert eval1.timestamp == eval2.timestamp
    assert eval1.evaluated_at == eval2.evaluated_at
    assert eval1.evidence_pointer == eval2.evidence_pointer


def test_monotonicity_persist_preserves_history():
    """
    Monotonicidad: persist(e1), persist(e2) => store contiene ambas (historia no se borra).
    """
    transitions = list_transitions()
    store = InMemoryAppendOnlyStateStore()
    machine = MoneyStateMachine(transitions, store, "v1", "v1")
    
    # Primera evaluación
    eval1 = machine.evaluate(
        flow_id="flow_001",
        canonical_events=[
            {
                "event_id": "event_001",
                "event_type": "payment_initiated",
                "timestamp": "2026-01-25T10:00:00Z"
            }
        ],
        correlation_links=[],
        evaluated_at="2026-01-25T12:00:00Z",
        evidence_pointer="evidence/step1"
    )
    
    # Segunda evaluación (mismo flujo, más evidencia)
    eval2 = machine.evaluate(
        flow_id="flow_001",
        canonical_events=[
            {
                "event_id": "event_001",
                "event_type": "payment_initiated",
                "timestamp": "2026-01-25T10:00:00Z"
            },
            {
                "event_id": "event_002",
                "event_type": "settlement_confirmed",
                "timestamp": "2026-01-25T10:05:00Z"
            }
        ],
        correlation_links=[],
        evaluated_at="2026-01-25T12:30:00Z",
        evidence_pointer="evidence/step2"
    )
    
    # Persistir primera evaluación
    machine.persist(eval1)
    
    # Contar evaluaciones después de e1
    evaluations_after_e1 = list(store.iter_all())
    e1_count = len(evaluations_after_e1)
    e1_ids = {ev.evaluation_id for ev in evaluations_after_e1}
    
    # Persistir segunda evaluación
    machine.persist(eval2)
    
    # Contar evaluaciones después de e1 + e2
    evaluations_after_e1_e2 = list(store.iter_all())
    total_count = len(evaluations_after_e1_e2)
    
    # Verificar monotonicidad
    assert total_count >= e1_count  # No perdimos evaluaciones
    assert total_count == e1_count + 1  # Agregamos exactamente una
    
    # Verificar que todas las evaluaciones originales siguen ahí
    current_ids = {ev.evaluation_id for ev in evaluations_after_e1_e2}
    assert e1_ids.issubset(current_ids)
    
    # Verificar que ambas evaluaciones están presentes
    assert eval1.evaluation_id in current_ids
    assert eval2.evaluation_id in current_ids


def test_conservatism_contradictory_evidence_yields_ambiguous():
    """
    Conservadurismo: si se construye evidencia que hace plausibles SETTLED y FAILED 
    simultáneamente => AMBIGUOUS.
    """
    transitions = list_transitions()
    store = InMemoryAppendOnlyStateStore()
    machine = MoneyStateMachine(transitions, store, "v1", "v1")
    
    # Evidencia contradictoria: señales de éxito Y falla
    contradictory_events = [
        {
            "event_id": "event_001",
            "event_type": "settlement_confirmed",  # Señal de éxito
            "timestamp": "2026-01-25T10:05:00Z"
        },
        {
            "event_id": "event_002", 
            "event_type": "processing_failed",  # Señal de falla
            "timestamp": "2026-01-25T10:06:00Z"
        }
    ]
    
    evaluation = machine.evaluate(
        flow_id="contradictory_flow",
        canonical_events=contradictory_events,
        correlation_links=[],
        evaluated_at="2026-01-25T12:00:00Z",
        evidence_pointer="evidence/contradictory"
    )
    
    # Debe ser AMBIGUOUS debido a evidencia contradictoria
    assert evaluation.state == "AMBIGUOUS"
    assert "multiple" in evaluation.transition_reason.lower() or "contradictory" in evaluation.transition_reason.lower()
    
    # La confianza debe ser moderada/baja debido a la ambigüedad
    assert evaluation.confidence_level <= 0.7


def test_evaluation_id_determinism():
    """
    Verificar que evaluation_id se genera de manera determinista.
    Mismos inputs => mismo evaluation_id.
    """
    transitions = list_transitions()
    store1 = InMemoryAppendOnlyStateStore()
    store2 = InMemoryAppendOnlyStateStore()
    
    machine1 = MoneyStateMachine(transitions, store1, "v1", "v1")
    machine2 = MoneyStateMachine(transitions, store2, "v1", "v1")
    
    # Inputs idénticos
    common_args = {
        "flow_id": "deterministic_flow",
        "canonical_events": [
            {
                "event_id": "event_det_001",
                "event_type": "payment_initiated",
                "timestamp": "2026-01-25T10:00:00Z"
            }
        ],
        "correlation_links": [],
        "evaluated_at": "2026-01-25T12:00:00Z",
        "evidence_pointer": "evidence/deterministic"
    }
    
    eval1 = machine1.evaluate(**common_args)
    eval2 = machine2.evaluate(**common_args)
    
    # evaluation_id debe ser idéntico
    assert eval1.evaluation_id == eval2.evaluation_id
    
    # Cambiar un input debe cambiar el evaluation_id
    modified_args = common_args.copy()
    modified_args["evaluated_at"] = "2026-01-25T12:01:00Z"
    
    eval3 = machine1.evaluate(**modified_args)
    
    # evaluation_id debe ser diferente
    assert eval1.evaluation_id != eval3.evaluation_id


def test_no_mutation_of_input_events():
    """
    Verificar que evaluate() NO muta canonical_events.
    """
    transitions = list_transitions()
    store = InMemoryAppendOnlyStateStore()
    machine = MoneyStateMachine(transitions, store, "v1", "v1")
    
    # Eventos originales
    original_events = [
        {
            "event_id": "event_immutable_001",
            "event_type": "payment_initiated",
            "amount": 100.0,
            "timestamp": "2026-01-25T10:00:00Z"
        }
    ]
    
    # Hacer copia para comparar después
    events_copy = [event.copy() for event in original_events]
    
    # Ejecutar evaluación
    machine.evaluate(
        flow_id="immutable_test",
        canonical_events=original_events,
        correlation_links=[],
        evaluated_at="2026-01-25T12:00:00Z",
        evidence_pointer="evidence/immutable"
    )
    
    # Verificar que los eventos no fueron mutados
    assert original_events == events_copy
    
    # Verificar que cada campo individual no cambió
    for original, copy in zip(original_events, events_copy):
        for key in original:
            assert original[key] == copy[key]