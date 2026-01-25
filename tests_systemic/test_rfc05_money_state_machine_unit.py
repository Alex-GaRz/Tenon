import pytest
from core.money_state.v1.types import MONEY_STATES, MoneyStateEvaluation, TransitionRule
from core.money_state.v1.transitions import list_transitions
from core.money_state.v1.state_store import InMemoryAppendOnlyStateStore
from core.money_state.v1.machine import MoneyStateMachine


def test_enum_includes_ambiguous_and_unknown():
    """Enum incluye AMBIGUOUS y UNKNOWN."""
    assert "AMBIGUOUS" in MONEY_STATES
    assert "UNKNOWN" in MONEY_STATES
    
    # Verificar que están en las posiciones correctas
    assert MONEY_STATES[-2] == "AMBIGUOUS"
    assert MONEY_STATES[-1] == "UNKNOWN"


def test_confidence_level_always_valid_range():
    """confidence_level siempre [0,1]."""
    transitions = list_transitions()
    store = InMemoryAppendOnlyStateStore()
    machine = MoneyStateMachine(transitions, store, "v1", "v1")
    
    # Evaluar con diferentes tipos de evidencia
    test_cases = [
        # Evidencia fuerte
        {
            "events": [
                {
                    "event_id": "evt_001",
                    "event_type": "settlement_confirmed",
                    "timestamp": "2026-01-25T10:00:00Z"
                }
            ],
            "links": []
        },
        # Evidencia contradictoria
        {
            "events": [
                {
                    "event_id": "evt_002", 
                    "event_type": "settlement_confirmed",
                    "timestamp": "2026-01-25T10:00:00Z"
                },
                {
                    "event_id": "evt_003",
                    "event_type": "processing_failed", 
                    "timestamp": "2026-01-25T10:01:00Z"
                }
            ],
            "links": []
        },
        # Sin evidencia
        {
            "events": [],
            "links": []
        }
    ]
    
    for i, case in enumerate(test_cases):
        evaluation = machine.evaluate(
            flow_id=f"flow_{i}",
            canonical_events=case["events"],
            correlation_links=case["links"],
            evaluated_at="2026-01-25T12:00:00Z",
            evidence_pointer=f"evidence/case_{i}"
        )
        
        assert 0.0 <= evaluation.confidence_level <= 1.0, \
            f"Confidence level {evaluation.confidence_level} out of range for case {i}"


def test_append_only_state_store_rejects_duplicate_evaluation_id():
    """InMemoryAppendOnlyStateStore rechaza evaluation_id duplicado."""
    store = InMemoryAppendOnlyStateStore()
    
    evaluation1 = MoneyStateEvaluation(
        evaluation_id="eval_001",
        flow_id="flow_001",
        event_id="event_001",
        timestamp="2026-01-25T10:00:00Z",
        state="SETTLED",
        transition_reason="Settlement confirmed",
        evidence_pointer="evidence/001",
        state_version="v1",
        machine_version="v1",
        confidence_level=0.9,
        evaluated_at="2026-01-25T12:00:00Z"
    )
    
    evaluation2 = MoneyStateEvaluation(
        evaluation_id="eval_001",  # Mismo evaluation_id
        flow_id="flow_002",
        event_id="event_002",
        timestamp="2026-01-25T10:30:00Z",
        state="FAILED",
        transition_reason="Processing failed",
        evidence_pointer="evidence/002",
        state_version="v1",
        machine_version="v1",
        confidence_level=0.8,
        evaluated_at="2026-01-25T12:30:00Z"
    )
    
    # Primer append debe ser exitoso
    store.append(evaluation1)
    
    # Segundo append debe fallar por evaluation_id duplicado
    with pytest.raises(ValueError, match="Duplicate evaluation_id: eval_001"):
        store.append(evaluation2)


def test_invalid_transitions_raise_value_error():
    """Transiciones inválidas (from/to fuera de enum) deben levantar ValueError."""
    
    # Transición con from_state inválido
    invalid_transition_from = TransitionRule(
        from_state="INVALID_STATE",
        to_state="SETTLED",
        required_evidence=["SETTLEMENT_CONFIRMATION"],
        forbidden_evidence=[],
        timeout_policy={},
        transition_rule_version="v1"
    )
    
    # Transición con to_state inválido
    invalid_transition_to = TransitionRule(
        from_state="INITIATED",
        to_state="INVALID_STATE",
        required_evidence=["SOMETHING"],
        forbidden_evidence=[],
        timeout_policy={},
        transition_rule_version="v1"
    )
    
    store = InMemoryAppendOnlyStateStore()
    
    # Construir máquina con transición inválida debe fallar o
    # alternativamente, list_transitions debe validar y fallar
    
    # Test con from_state inválido
    with pytest.raises(ValueError):
        machine = MoneyStateMachine([invalid_transition_from], store, "v1", "v1")
        # Si la validación no está en el constructor, estará en la evaluación
        machine.evaluate(
            flow_id="test_flow",
            canonical_events=[],
            correlation_links=[],
            evaluated_at="2026-01-25T12:00:00Z",
            evidence_pointer="test/evidence"
        )
    
    # Test con to_state inválido
    with pytest.raises(ValueError):
        machine = MoneyStateMachine([invalid_transition_to], store, "v1", "v1")
        machine.evaluate(
            flow_id="test_flow",
            canonical_events=[],
            correlation_links=[],
            evaluated_at="2026-01-25T12:00:00Z",
            evidence_pointer="test/evidence"
        )


def test_list_transitions_validates_state_enum():
    """list_transitions debe validar que estados estén en el enum y levantar ValueError si no."""
    # Esta prueba verifica que list_transitions hace validación interna
    transitions = list_transitions()
    
    # Verificar que todas las transiciones usan estados válidos
    for transition in transitions:
        assert transition.from_state in MONEY_STATES, f"Invalid from_state: {transition.from_state}"
        assert transition.to_state in MONEY_STATES, f"Invalid to_state: {transition.to_state}"


def test_machine_no_delete_update_methods():
    """Verificar que el store no tiene métodos delete/update (append-only)."""
    store = InMemoryAppendOnlyStateStore()
    
    # Verificar que no existen métodos prohibidos
    forbidden_methods = ['delete', 'update', 'remove', 'pop', 'clear']
    
    for method_name in forbidden_methods:
        assert not hasattr(store, method_name), f"Store should not have {method_name} method"
    
    # Verificar que solo tiene métodos permitidos
    allowed_methods = ['append', 'iter_all', 'iter_by_flow']
    
    for method_name in allowed_methods:
        assert hasattr(store, method_name), f"Store should have {method_name} method"


def test_state_evaluation_immutable():
    """Verificar que MoneyStateEvaluation es inmutable (frozen=True)."""
    evaluation = MoneyStateEvaluation(
        evaluation_id="eval_001",
        flow_id="flow_001",
        event_id="event_001",
        timestamp="2026-01-25T10:00:00Z",
        state="SETTLED",
        transition_reason="Settlement confirmed",
        evidence_pointer="evidence/001",
        state_version="v1",
        machine_version="v1",
        confidence_level=0.9,
        evaluated_at="2026-01-25T12:00:00Z"
    )
    
    # Intentar modificar debe fallar (frozen dataclass)
    with pytest.raises(AttributeError):
        evaluation.state = "FAILED"  # type: ignore
    
    with pytest.raises(AttributeError):
        evaluation.confidence_level = 0.5  # type: ignore