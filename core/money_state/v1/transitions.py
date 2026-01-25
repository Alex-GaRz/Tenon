from typing import List
from .types import TransitionRule, MONEY_STATES

TRANSITION_RULESET_VERSION = "v1"


def list_transitions() -> List[TransitionRule]:
    """
    Retorna lista de transiciones en orden estable (from_state, to_state).
    Incluye transición hacia AMBIGUOUS cuando exista evidencia conflictiva.
    """
    transitions = []
    
    # Transiciones principales del flujo normal
    transitions.extend([
        # Flujo inicial
        TransitionRule(
            from_state="EXPECTED",
            to_state="INITIATED",
            required_evidence=["INITIATION_SIGNAL"],
            forbidden_evidence=[],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        TransitionRule(
            from_state="INITIATED",
            to_state="AUTHORIZED",
            required_evidence=["AUTHORIZATION_CONFIRMATION"],
            forbidden_evidence=["AUTHORIZATION_DENIAL"],
            timeout_policy={"timeout_minutes": 30},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        TransitionRule(
            from_state="AUTHORIZED",
            to_state="IN_TRANSIT",
            required_evidence=["PROCESSING_START"],
            forbidden_evidence=[],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        TransitionRule(
            from_state="IN_TRANSIT",
            to_state="SETTLED",
            required_evidence=["SETTLEMENT_CONFIRMATION"],
            forbidden_evidence=["PROCESSING_FAILURE", "SETTLEMENT_REJECTION"],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        # Flujos de falla
        TransitionRule(
            from_state="INITIATED",
            to_state="FAILED",
            required_evidence=["AUTHORIZATION_DENIAL", "INITIATION_FAILURE"],
            forbidden_evidence=[],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        TransitionRule(
            from_state="AUTHORIZED",
            to_state="FAILED",
            required_evidence=["PROCESSING_FAILURE"],
            forbidden_evidence=[],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        TransitionRule(
            from_state="IN_TRANSIT",
            to_state="FAILED",
            required_evidence=["PROCESSING_FAILURE", "SETTLEMENT_REJECTION"],
            forbidden_evidence=["SETTLEMENT_CONFIRMATION"],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        # Flujos de reversal y refund
        TransitionRule(
            from_state="SETTLED",
            to_state="REFUNDED",
            required_evidence=["REFUND_REQUEST", "REFUND_CONFIRMATION"],
            forbidden_evidence=[],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        TransitionRule(
            from_state="SETTLED",
            to_state="REVERSED",
            required_evidence=["REVERSAL_REQUEST", "REVERSAL_CONFIRMATION"],
            forbidden_evidence=[],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        # Timeouts
        TransitionRule(
            from_state="AUTHORIZED",
            to_state="EXPIRED",
            required_evidence=["TIMEOUT_EXCEEDED"],
            forbidden_evidence=["PROCESSING_START"],
            timeout_policy={"timeout_minutes": 1440},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        # Transiciones hacia AMBIGUOUS (evidencia conflictiva)
        TransitionRule(
            from_state="IN_TRANSIT",
            to_state="AMBIGUOUS",
            required_evidence=[],  # Se activa cuando hay evidencia conflictiva
            forbidden_evidence=[],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        TransitionRule(
            from_state="AUTHORIZED",
            to_state="AMBIGUOUS",
            required_evidence=[],  # Se activa cuando hay evidencia conflictiva
            forbidden_evidence=[],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        ),
        
        # Transiciones hacia UNKNOWN (evidencia insuficiente)
        TransitionRule(
            from_state="EXPECTED",
            to_state="UNKNOWN",
            required_evidence=[],
            forbidden_evidence=[],
            timeout_policy={},
            transition_rule_version=TRANSITION_RULESET_VERSION
        )
    ])
    
    # Validar que todas las transiciones usan estados válidos
    for transition in transitions:
        if transition.from_state not in MONEY_STATES:
            raise ValueError(f"Invalid from_state: {transition.from_state}")
        if transition.to_state not in MONEY_STATES:
            raise ValueError(f"Invalid to_state: {transition.to_state}")
    
    # Retornar en orden estable (from_state, to_state)
    return sorted(transitions, key=lambda t: (t.from_state, t.to_state))