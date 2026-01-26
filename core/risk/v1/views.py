"""
RFC-13 Risk Observability - Views (Ejecutivas y Operativas)
============================================================

Proyecciones puras para vistas institucionales.

PROHIBIDO:
- Incluir métricas técnicas (CPU, RAM, latencia, QPS, throughput)
- Side effects (solo lectura/agregación)
"""

from typing import List, Dict, Any
from collections import defaultdict


def build_executive_view(aggregates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Construye vista ejecutiva de riesgo (RFC-13 §8.1).
    
    Contenido:
    - Riesgo agregado del sistema (último período)
    - Top drivers de riesgo
    - Tendencias temporales
    - Comparativas pre/post cambio (si hay datos)
    
    Args:
        aggregates: Lista de RiskAggregates (ordenados por computed_at desc)
    
    Returns:
        Dict con vista ejecutiva (proyección pura)
    """
    if not aggregates:
        return {
            "system_risk_level": "LOW",
            "top_drivers": [],
            "trend": "STABLE",
            "summary": "Sin datos de riesgo disponibles.",
        }
    
    # Riesgo agregado del sistema (último período)
    latest_aggregate = aggregates[0]
    system_risk_level = latest_aggregate["overall_risk_level"]
    
    # Top drivers de riesgo (desde último agregado)
    top_drivers = _extract_top_drivers(latest_aggregate)
    
    # Tendencia temporal (comparar últimos N agregados)
    trend = _compute_trend(aggregates[:10])  # Últimos 10 períodos
    
    # Comparativas pre/post cambio (placeholder: requiere metadata de cambios)
    change_comparison = _compute_change_comparison(aggregates)
    
    return {
        "system_risk_level": system_risk_level,
        "top_drivers": top_drivers,
        "trend": trend,
        "change_comparison": change_comparison,
        "summary": _generate_executive_summary(system_risk_level, trend),
    }


def build_operational_view(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Construye vista operativa de riesgo (RFC-13 §8.2).
    
    Contenido:
    - Vistas por fuente/flujo
    - Backlog de discrepancias críticas
    - Estados stale y ambigüedades
    - Evidencia navegable
    
    Args:
        signals: Lista de RiskSignals (activas)
    
    Returns:
        Dict con vista operativa (proyección pura)
    """
    if not signals:
        return {
            "by_source": {},
            "by_flow": {},
            "critical_backlog": [],
            "stale_states": [],
            "summary": "Sin señales de riesgo activas.",
        }
    
    # Agrupación por fuente (scope=SOURCE)
    by_source = _group_signals_by_scope(signals, "SOURCE")
    
    # Agrupación por flujo (scope=FLOW)
    by_flow = _group_signals_by_scope(signals, "FLOW")
    
    # Backlog de discrepancias críticas
    critical_backlog = _extract_critical_discrepancies(signals)
    
    # Estados stale y ambigüedades
    stale_states = _extract_stale_states(signals)
    
    return {
        "by_source": by_source,
        "by_flow": by_flow,
        "critical_backlog": critical_backlog,
        "stale_states": stale_states,
        "summary": _generate_operational_summary(signals),
    }


# --- Helpers (funciones puras internas) ---

def _extract_top_drivers(aggregate: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrae top drivers desde RiskAggregate."""
    drivers = aggregate.get("drivers", [])
    risk_profile = aggregate.get("risk_profile", [])
    
    # Mapear driver IDs a señales completas
    driver_signals = [
        sig for sig in risk_profile
        if sig["risk_signal_id"] in drivers
    ]
    
    # Ordenar por severidad descendente
    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    sorted_drivers = sorted(
        driver_signals,
        key=lambda s: severity_order.get(s["severity_level"], 0),
        reverse=True
    )
    
    return sorted_drivers[:5]  # Top 5


def _compute_trend(aggregates: List[Dict[str, Any]]) -> str:
    """
    Computa tendencia temporal de riesgo.
    
    Returns:
        "ESCALATING" | "STABLE" | "IMPROVING"
    """
    if len(aggregates) < 2:
        return "STABLE"
    
    severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    
    # Comparar primeros 3 vs últimos 3 agregados
    recent = [severity_order[a["overall_risk_level"]] for a in aggregates[:3]]
    older = [severity_order[a["overall_risk_level"]] for a in aggregates[3:6]]
    
    if not older:
        return "STABLE"
    
    avg_recent = sum(recent) / len(recent)
    avg_older = sum(older) / len(older)
    
    if avg_recent > avg_older * 1.1:
        return "ESCALATING"
    elif avg_recent < avg_older * 0.9:
        return "IMPROVING"
    else:
        return "STABLE"


def _compute_change_comparison(aggregates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computa comparativa pre/post cambio (placeholder).
    
    En implementación real: cruzar con change_control metadata.
    """
    return {
        "available": False,
        "message": "Requiere metadata de change control para comparativas",
    }


def _generate_executive_summary(risk_level: str, trend: str) -> str:
    """Genera resumen ejecutivo human-readable."""
    trend_text = {
        "ESCALATING": "en escalamiento",
        "STABLE": "estable",
        "IMPROVING": "en mejora",
    }.get(trend, "sin tendencia clara")
    
    return f"Riesgo del sistema: {risk_level} ({trend_text})"


def _group_signals_by_scope(
    signals: List[Dict[str, Any]],
    scope: str
) -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa señales por scope_key (fuente/flujo)."""
    grouped = defaultdict(list)
    
    for sig in signals:
        if sig["scope"] == scope:
            # Extraer scope_key desde supporting_metrics o usar signal_type
            scope_key = sig.get("scope_key", "UNKNOWN")
            grouped[scope_key].append({
                "risk_signal_id": sig["risk_signal_id"],
                "signal_type": sig["signal_type"],
                "severity_level": sig["severity_level"],
                "explanation": sig.get("explanation", ""),
            })
    
    return dict(grouped)


def _extract_critical_discrepancies(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extrae señales de discrepancias críticas (CRITICAL severity)."""
    critical = [
        {
            "risk_signal_id": sig["risk_signal_id"],
            "signal_type": sig["signal_type"],
            "explanation": sig.get("explanation", ""),
        }
        for sig in signals
        if sig["severity_level"] == "CRITICAL"
        and sig["signal_type"].startswith("DISCREPANCY_")
    ]
    
    return critical


def _extract_stale_states(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extrae señales de estados stale/ambiguous."""
    stale = [
        {
            "risk_signal_id": sig["risk_signal_id"],
            "signal_type": sig["signal_type"],
            "severity_level": sig["severity_level"],
        }
        for sig in signals
        if sig["signal_type"] in [
            "STATE_STALE_FLOWS_NO_EVOLUTION",
            "STATE_AMBIGUOUS_ACCUMULATION_OUTSIDE_SLA",
            "STATE_UNKNOWN_ACCUMULATION_OUTSIDE_SLA",
        ]
    ]
    
    return stale


def _generate_operational_summary(signals: List[Dict[str, Any]]) -> str:
    """Genera resumen operativo."""
    total_signals = len(signals)
    critical_count = sum(1 for s in signals if s["severity_level"] == "CRITICAL")
    high_count = sum(1 for s in signals if s["severity_level"] == "HIGH")
    
    return (
        f"{total_signals} señales activas: "
        f"{critical_count} CRITICAL, {high_count} HIGH"
    )
