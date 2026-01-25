import pytest
import json
from pathlib import Path
from core.money_state.v1.transitions import list_transitions
from core.money_state.v1.state_store import InMemoryAppendOnlyStateStore
from core.money_state.v1.machine import MoneyStateMachine


def load_fixture(filename: str):
    """Carga un fixture JSON desde el directorio de fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "rfc05_money_state_machine" / filename
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_test_machine():
    """Crea una máquina de estados de prueba."""
    transitions = list_transitions()
    store = InMemoryAppendOnlyStateStore()
    return MoneyStateMachine(transitions, store, "v1", "v1")


def test_incomplete_evidence_then_settlement():
    """
    Evaluación inicial con evidencia incompleta => IN_TRANSIT o AMBIGUOUS (según reglas definidas) 
    pero nunca SETTLED sin evidencia.
    Llega nueva evidencia (nuevo evento o link) => nueva evaluación con nuevo evaluation_id, 
    sin borrar la previa.
    """
    machine = create_test_machine()
    
    # Cargar fixture con escenario de evidencia tardía
    scenario = load_fixture("scenario_incomplete_then_settled.json")
    
    step1_data = scenario["step1"]
    step2_data = scenario["step2"]
    
    # Paso 1: Evidencia incompleta
    eval1 = machine.evaluate(
        flow_id="incomplete_to_settled_flow",
        canonical_events=step1_data["events"],
        correlation_links=step1_data["links"],
        evaluated_at="2026-01-25T12:00:00Z",
        evidence_pointer="evidence/step1"
    )
    
    # Con evidencia incompleta, NO debe ser SETTLED
    assert eval1.state != "SETTLED", f"Should not be SETTLED with incomplete evidence, got: {eval1.state}"
    
    # Debe ser un estado intermedio válido
    valid_intermediate_states = ["IN_TRANSIT", "AMBIGUOUS", "UNKNOWN", "INITIATED", "AUTHORIZED"]
    assert eval1.state in valid_intermediate_states, f"Unexpected state with incomplete evidence: {eval1.state}"
    
    # Persistir primera evaluación
    machine.persist(eval1)
    
    # Paso 2: Llega evidencia de settlement
    eval2 = machine.evaluate(
        flow_id="incomplete_to_settled_flow",
        canonical_events=step2_data["events"],
        correlation_links=step2_data["links"],
        evaluated_at="2026-01-25T12:30:00Z",
        evidence_pointer="evidence/step2"
    )
    
    # Con evidencia completa, puede ser SETTLED
    # (dependiendo de la evidencia en el fixture, podría ser SETTLED o otro estado final)
    
    # Persistir segunda evaluación
    machine.persist(eval2)
    
    # Verificar que ambas evaluaciones existen (historia no se borra)
    all_evaluations = list(machine.store.iter_all())
    evaluation_ids = {ev.evaluation_id for ev in all_evaluations}
    
    assert len(all_evaluations) == 2, "Should have both evaluations preserved"
    assert eval1.evaluation_id in evaluation_ids
    assert eval2.evaluation_id in evaluation_ids
    
    # Las evaluaciones deben tener evaluation_id diferentes
    assert eval1.evaluation_id != eval2.evaluation_id


def test_contradictory_evidence_yields_ambiguous():
    """
    Contradicción explícita => AMBIGUOUS.
    Events+links donde existan señales plausibles de SETTLED y FAILED 
    para forzar AMBIGUOUS.
    """
    machine = create_test_machine()
    
    # Cargar fixture con evidencia contradictoria
    scenario = load_fixture("scenario_contradictory.json")
    
    evaluation = machine.evaluate(
        flow_id="contradictory_flow",
        canonical_events=scenario["events"],
        correlation_links=scenario["links"],
        evaluated_at="2026-01-25T12:00:00Z",
        evidence_pointer="evidence/contradictory"
    )
    
    # Con evidencia contradictoria, debe ser AMBIGUOUS
    assert evaluation.state == "AMBIGUOUS", f"Expected AMBIGUOUS with contradictory evidence, got: {evaluation.state}"
    
    # El reason debe indicar la naturaleza de la ambigüedad
    reason_lower = evaluation.transition_reason.lower()
    ambiguity_keywords = ["multiple", "contradictory", "conflict", "ambiguous"]
    has_ambiguity_keyword = any(keyword in reason_lower for keyword in ambiguity_keywords)
    assert has_ambiguity_keyword, f"Transition reason should indicate ambiguity: {evaluation.transition_reason}"
    
    # La confianza debe ser moderada/baja debido a la contradicción
    assert evaluation.confidence_level <= 0.7, f"Confidence should be low/moderate for ambiguous state, got: {evaluation.confidence_level}"


def test_replay_complete_sequence_identical_evaluations():
    """
    Replay completo => misma secuencia de evaluaciones (mismos outputs por paso).
    """
    machine1 = create_test_machine()
    machine2 = create_test_machine()
    
    # Usar fixture de evidencia tardía para tener secuencia de pasos
    scenario = load_fixture("scenario_incomplete_then_settled.json")
    
    # Secuencia de evaluaciones en machine1
    eval1_step1 = machine1.evaluate(
        flow_id="replay_test_flow",
        canonical_events=scenario["step1"]["events"],
        correlation_links=scenario["step1"]["links"],
        evaluated_at="2026-01-25T12:00:00Z",
        evidence_pointer="evidence/replay_step1"
    )
    machine1.persist(eval1_step1)
    
    eval1_step2 = machine1.evaluate(
        flow_id="replay_test_flow",
        canonical_events=scenario["step2"]["events"],
        correlation_links=scenario["step2"]["links"],
        evaluated_at="2026-01-25T12:30:00Z",
        evidence_pointer="evidence/replay_step2"
    )
    machine1.persist(eval1_step2)
    
    # Replay de la misma secuencia en machine2
    eval2_step1 = machine2.evaluate(
        flow_id="replay_test_flow",
        canonical_events=scenario["step1"]["events"],
        correlation_links=scenario["step1"]["links"],
        evaluated_at="2026-01-25T12:00:00Z",
        evidence_pointer="evidence/replay_step1"
    )
    machine2.persist(eval2_step1)
    
    eval2_step2 = machine2.evaluate(
        flow_id="replay_test_flow",
        canonical_events=scenario["step2"]["events"],
        correlation_links=scenario["step2"]["links"],
        evaluated_at="2026-01-25T12:30:00Z",
        evidence_pointer="evidence/replay_step2"
    )
    machine2.persist(eval2_step2)
    
    # Verificar que las evaluaciones son idénticas paso a paso
    assert eval1_step1.evaluation_id == eval2_step1.evaluation_id
    assert eval1_step1.state == eval2_step1.state
    assert eval1_step1.transition_reason == eval2_step1.transition_reason
    assert eval1_step1.confidence_level == eval2_step1.confidence_level
    
    assert eval1_step2.evaluation_id == eval2_step2.evaluation_id
    assert eval1_step2.state == eval2_step2.state
    assert eval1_step2.transition_reason == eval2_step2.transition_reason
    assert eval1_step2.confidence_level == eval2_step2.confidence_level
    
    # Verificar que ambos stores tienen el mismo contenido
    evals1 = list(machine1.store.iter_all())
    evals2 = list(machine2.store.iter_all())
    
    assert len(evals1) == len(evals2)
    
    # Ordenar por evaluation_id para comparar
    evals1_sorted = sorted(evals1, key=lambda e: e.evaluation_id)
    evals2_sorted = sorted(evals2, key=lambda e: e.evaluation_id)
    
    for e1, e2 in zip(evals1_sorted, evals2_sorted):
        assert e1.evaluation_id == e2.evaluation_id
        assert e1.state == e2.state
        assert e1.confidence_level == e2.confidence_level


def test_historical_immutability():
    """
    Verificar que las evaluaciones históricas no se modifican al agregar nueva evidencia.
    """
    machine = create_test_machine()
    
    scenario = load_fixture("scenario_incomplete_then_settled.json")
    
    # Evaluación inicial
    initial_eval = machine.evaluate(
        flow_id="immutability_test",
        canonical_events=scenario["step1"]["events"],
        correlation_links=scenario["step1"]["links"],
        evaluated_at="2026-01-25T12:00:00Z",
        evidence_pointer="evidence/initial"
    )
    machine.persist(initial_eval)
    
    # Capturar estado inicial completo
    initial_state = initial_eval.state
    initial_reason = initial_eval.transition_reason
    initial_confidence = initial_eval.confidence_level
    initial_id = initial_eval.evaluation_id
    
    # Agregar nueva evidencia
    updated_eval = machine.evaluate(
        flow_id="immutability_test",
        canonical_events=scenario["step2"]["events"],
        correlation_links=scenario["step2"]["links"],
        evaluated_at="2026-01-25T13:00:00Z",
        evidence_pointer="evidence/updated"
    )
    machine.persist(updated_eval)
    
    # Verificar que la evaluación inicial no cambió
    all_evals = list(machine.store.iter_all())
    initial_eval_persisted = next(e for e in all_evals if e.evaluation_id == initial_id)
    
    assert initial_eval_persisted.state == initial_state
    assert initial_eval_persisted.transition_reason == initial_reason
    assert initial_eval_persisted.confidence_level == initial_confidence
    assert initial_eval_persisted.evaluation_id == initial_id
    
    # Debe haber exactamente dos evaluaciones
    assert len(all_evals) == 2
    
    # Las evaluaciones deben tener IDs diferentes
    eval_ids = [e.evaluation_id for e in all_evals]
    assert len(set(eval_ids)) == 2, "Evaluations should have unique IDs"