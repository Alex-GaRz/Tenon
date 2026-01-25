from typing import List
from .types import CorrelationRule, CorrelationEvidence, CorrelationLink


def link_events(
    source_event_id: str,
    target_event_id: str,
    link_type: str,
    rule: CorrelationRule,
    evidence: List[CorrelationEvidence],
    score: float,
    engine_version: str,
    created_at: str,
    *,
    link_id: str
) -> CorrelationLink:
    """
    Construye un CorrelationLink (arista) sin fusionar eventos.
    Aplica validaciones obligatorias.
    """
    # Validación: evidence no puede estar vacío
    if not evidence:
        raise ValueError("Evidence cannot be empty")
    
    # Validación: score debe estar en [0,1]
    if score < 0.0 or score > 1.0:
        raise ValueError(f"Score must be between 0.0 and 1.0, got: {score}")
    
    # Validación: source y target no pueden ser iguales
    if source_event_id == target_event_id:
        raise ValueError("Source and target event IDs cannot be the same")
    
    return CorrelationLink(
        link_id=link_id,
        source_event_id=source_event_id,
        target_event_id=target_event_id,
        link_type=link_type,
        rule_id=rule.rule_id,
        rule_version=rule.rule_version,
        version="v1",  # Version del schema/contrato del link
        score=score,
        evidence=evidence,
        engine_version=engine_version,
        created_at=created_at
    )