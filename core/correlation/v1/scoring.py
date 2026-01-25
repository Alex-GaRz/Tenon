from typing import List
from .types import CorrelationEvidence


def clamp_score(score: float) -> float:
    """Garantiza que el score esté en el rango [0.0, 1.0]"""
    if score < 0.0:
        return 0.0
    elif score > 1.0:
        return 1.0
    else:
        return score


def score_from_evidence(evidence: List[CorrelationEvidence]) -> float:
    """
    Calcula el score basado únicamente en evidence_type + details (determinista).
    """
    if not evidence:
        return 0.0
    
    total_score = 0.0
    
    for ev in evidence:
        # Score determinista basado solo en evidence_type y details
        if ev.evidence_type == "FIELD_MATCH":
            # Base score para match de campo
            base_score = 0.3
            # Si hay detalles sobre exactitud, ajustar
            if isinstance(ev.details, dict):
                if ev.details.get("exact_match", False):
                    base_score = 0.5
                elif ev.details.get("partial_match", False):
                    base_score = 0.2
            total_score += base_score
            
        elif ev.evidence_type == "AMOUNT_TOLERANCE":
            # Score basado en tolerancia de monto
            base_score = 0.4
            if isinstance(ev.details, dict):
                tolerance = ev.details.get("tolerance_percentage", 0.0)
                if tolerance <= 0.01:  # 1% o menos
                    base_score = 0.6
                elif tolerance <= 0.05:  # 5% o menos
                    base_score = 0.4
                else:
                    base_score = 0.2
            total_score += base_score
            
        elif ev.evidence_type == "TIME_WINDOW":
            # Score basado en ventana de tiempo
            base_score = 0.2
            if isinstance(ev.details, dict):
                window_minutes = ev.details.get("window_minutes", float('inf'))
                if window_minutes <= 60:  # 1 hora o menos
                    base_score = 0.3
                elif window_minutes <= 1440:  # 24 horas o menos
                    base_score = 0.2
                else:
                    base_score = 0.1
            total_score += base_score
            
        elif ev.evidence_type == "SEQUENCE_OBSERVED":
            total_score += 0.35
            
        elif ev.evidence_type == "REFERENCE_MATCH":
            total_score += 0.5
            
        elif ev.evidence_type == "CONTRADICTION_FLAG":
            # Resta del score por contradicción
            total_score -= 0.3
    
    # Normalizar por número de evidencias para evitar scores muy altos
    normalized_score = total_score / len(evidence)
    
    return clamp_score(normalized_score)