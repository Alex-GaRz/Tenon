"""
RFC-13 Risk Observability - Taxonomía Cerrada (Enums)
======================================================

Enums canónicos derivados estrictamente de RFC-13:
- RiskSeverityLevel: Niveles de severidad (§5.1)
- RiskScope: Alcances de señal (§5.1)
- RiskSignalType: Taxonomía CERRADA de señales (§4.1-4.6) - 25 valores exactos
- RiskAlertType: Tipos de alerta institucional (§7.2)

PROHIBIDO:
- Añadir valores tipo UNKNOWN (no existe en RFC-13)
- Modificar RiskSignalType sin actualizar RFC-13 §4
"""

from enum import Enum


class RiskSeverityLevel(str, Enum):
    """
    Niveles de severidad institucional - RFC-13 §5.1
    Orden: LOW < MEDIUM < HIGH < CRITICAL
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def max(cls, *levels: "RiskSeverityLevel") -> "RiskSeverityLevel":
        """Retorna el máximo nivel de severidad (CRITICAL > HIGH > MEDIUM > LOW)."""
        order = {cls.LOW: 1, cls.MEDIUM: 2, cls.HIGH: 3, cls.CRITICAL: 4}
        return max(levels, key=lambda lvl: order[lvl])


class RiskScope(str, Enum):
    """
    Alcances de señal de riesgo - RFC-13 §5.1
    """
    GLOBAL = "GLOBAL"           # Riesgo global del sistema
    SOURCE = "SOURCE"           # Riesgo por fuente de datos
    FLOW = "FLOW"               # Riesgo por flujo financiero
    COMPONENT = "COMPONENT"     # Riesgo por componente específico


class RiskSignalType(str, Enum):
    """
    Taxonomía CERRADA de señales de riesgo - RFC-13 §4.1-4.6
    
    Derivación mecánica (OBLIGATORIA):
    - Cada bullet de §4.1-4.6 → 1 entrada UPPER_SNAKE + prefijo de categoría
    - Total: 25 señales (sin añadir ni omitir)
    
    Categorías:
    - DISCREPANCY_ (§4.1): 5 señales
    - CORRELATION_ (§4.2): 3 señales
    - STATE_ (§4.3): 5 señales
    - IDEMPOTENCY_ (§4.4): 4 señales
    - CHANGE_ (§4.5): 5 señales
    - HUMAN_ (§4.6): 3 señales
    """
    
    # §4.1 Riesgo de discrepancias (5 señales)
    DISCREPANCY_CONCENTRATION_HIGH_BY_SOURCE = "DISCREPANCY_CONCENTRATION_HIGH_BY_SOURCE"
    DISCREPANCY_CONCENTRATION_HIGH_BY_TYPE = "DISCREPANCY_CONCENTRATION_HIGH_BY_TYPE"
    DISCREPANCY_CONCENTRATION_HIGH_BY_FLOW = "DISCREPANCY_CONCENTRATION_HIGH_BY_FLOW"
    DISCREPANCY_TEMPORAL_TREND_CRITICAL = "DISCREPANCY_TEMPORAL_TREND_CRITICAL"
    DISCREPANCY_AVERAGE_AGE_UNRESOLVED = "DISCREPANCY_AVERAGE_AGE_UNRESOLVED"
    
    # §4.2 Riesgo de correlación (3 señales)
    CORRELATION_CONFIDENCE_SCORE_DEGRADATION = "CORRELATION_CONFIDENCE_SCORE_DEGRADATION"
    CORRELATION_AMBIGUOUS_INCREASE_BY_FLOW = "CORRELATION_AMBIGUOUS_INCREASE_BY_FLOW"
    CORRELATION_ORPHAN_EVENT_GROWTH = "CORRELATION_ORPHAN_EVENT_GROWTH"
    
    # §4.3 Riesgo de estados (5 señales)
    STATE_AMBIGUOUS_ACCUMULATION_OUTSIDE_SLA = "STATE_AMBIGUOUS_ACCUMULATION_OUTSIDE_SLA"
    STATE_UNKNOWN_ACCUMULATION_OUTSIDE_SLA = "STATE_UNKNOWN_ACCUMULATION_OUTSIDE_SLA"
    STATE_IN_TRANSIT_ACCUMULATION_OUTSIDE_SLA = "STATE_IN_TRANSIT_ACCUMULATION_OUTSIDE_SLA"
    STATE_STALE_FLOWS_NO_EVOLUTION = "STATE_STALE_FLOWS_NO_EVOLUTION"
    STATE_DIVERGENCE_EXPECTED_VS_OBSERVED = "STATE_DIVERGENCE_EXPECTED_VS_OBSERVED"
    
    # §4.4 Riesgo de idempotencia (4 señales)
    IDEMPOTENCY_REJECT_DUPLICATE_INCREASE = "IDEMPOTENCY_REJECT_DUPLICATE_INCREASE"
    IDEMPOTENCY_FLAG_AMBIGUOUS_INCREASE = "IDEMPOTENCY_FLAG_AMBIGUOUS_INCREASE"
    IDEMPOTENCY_KEY_COLLISION_RECURRENT = "IDEMPOTENCY_KEY_COLLISION_RECURRENT"
    IDEMPOTENCY_GUARDIAN_BYPASS_OR_FAILURE = "IDEMPOTENCY_GUARDIAN_BYPASS_OR_FAILURE"
    
    # §4.5 Riesgo de cambio (5 señales)
    CHANGE_IMPACT_ON_CORRELATION = "CHANGE_IMPACT_ON_CORRELATION"
    CHANGE_IMPACT_ON_STATES = "CHANGE_IMPACT_ON_STATES"
    CHANGE_IMPACT_ON_DISCREPANCIES = "CHANGE_IMPACT_ON_DISCREPANCIES"
    CHANGE_VERSION_COEXISTENCE_DIVERGENT_RESULTS = "CHANGE_VERSION_COEXISTENCE_DIVERGENT_RESULTS"
    CHANGE_DISCREPANCY_INCREASE_POST_CHANGE = "CHANGE_DISCREPANCY_INCREASE_POST_CHANGE"
    
    # §4.6 Riesgo humano-operativo (3 señales)
    HUMAN_INTERVENTION_OVERUSE = "HUMAN_INTERVENTION_OVERUSE"
    HUMAN_DISCREPANCY_REOPENING_RECURRENT = "HUMAN_DISCREPANCY_REOPENING_RECURRENT"
    HUMAN_OVERRIDE_DEPENDENCY = "HUMAN_OVERRIDE_DEPENDENCY"


class RiskAlertType(str, Enum):
    """
    Tipos de alerta institucional - RFC-13 §7.2
    """
    EARLY_WARNING = "EARLY_WARNING"                 # Degradación incipiente
    RISK_ESCALATION = "RISK_ESCALATION"             # Riesgo material
    INSTITUTIONAL_BREACH = "INSTITUTIONAL_BREACH"   # Violación de umbral crítico
