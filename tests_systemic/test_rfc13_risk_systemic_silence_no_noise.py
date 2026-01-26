"""
RFC-13 Risk Observability - Test: Systemic (Silence / Anti-Ruido)
==================================================================

Test sistémico: Política anti-ruido (silencio).

OBJETIVO:
- Si el sistema opera normal (sin breaches), compute() produce 0 señales
- Fundamentación: ruido excesivo es amenaza explícita (RFC-13 §9.1)
"""

import pytest
from datetime import datetime

from core.risk.v1.thresholds import ThresholdEvaluator
from core.risk.v1.signal_computer import SignalComputer
from core.risk.v1.risk_assessor import RiskAssessor
from core.risk.v1.alert_builder import AlertBuilder


@pytest.fixture
def threshold_set_silence():
    """Fixture: threshold_set con umbrales realistas."""
    return {
        "threshold_set_id": "TST_SILENCE",
        "threshold_set_version": "1.0.0",
        "approved_change_ref": "CHANGE_SILENCE_001",
        "rules": [
            {
                "signal_type": "DISCREPANCY_CONCENTRATION_HIGH_BY_SOURCE",
                "scope": "SOURCE",
                "metric_key": "discrepancy_concentration_pct",
                "severity_mapping": [
                    {"threshold_value": 5.0, "severity_level": "LOW", "operator": "GTE"},
                    {"threshold_value": 10.0, "severity_level": "MEDIUM", "operator": "GTE"},
                    {"threshold_value": 20.0, "severity_level": "HIGH", "operator": "GTE"},
                ]
            },
            {
                "signal_type": "CORRELATION_CONFIDENCE_SCORE_DEGRADATION",
                "scope": "GLOBAL",
                "metric_key": "avg_confidence_score",
                "severity_mapping": [
                    {"threshold_value": 0.8, "severity_level": "LOW", "operator": "LT"},
                    {"threshold_value": 0.7, "severity_level": "MEDIUM", "operator": "LT"},
                ]
            },
            {
                "signal_type": "STATE_AMBIGUOUS_ACCUMULATION_OUTSIDE_SLA",
                "scope": "GLOBAL",
                "metric_key": "ambiguous_state_count",
                "severity_mapping": [
                    {"threshold_value": 10, "severity_level": "MEDIUM", "operator": "GTE"},
                    {"threshold_value": 50, "severity_level": "CRITICAL", "operator": "GTE"},
                ]
            }
        ]
    }


def test_silence_normal_operation_produces_zero_signals(threshold_set_silence):
    """
    Test: Operación normal (valores por debajo de umbrales) → 0 señales.
    
    Escenario:
    - discrepancy_concentration_pct = 2% (< 5% threshold)
    - avg_confidence_score = 0.95 (> 0.8 threshold)
    - ambiguous_state_count = 3 (< 10 threshold)
    
    Esperado: 0 señales (silencio operativo)
    """
    evaluator = ThresholdEvaluator(threshold_set_silence)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",
                "metric_value": 2.0,  # < 5.0 → NO señal
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_NORMAL_001"],
                "risk_mapping": "Concentración normal de discrepancias"
            },
            {
                "metric_key": "avg_confidence_score",
                "metric_value": 0.95,  # > 0.8 → NO señal
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_NORMAL_002"],
                "risk_mapping": "Confianza alta en correlación"
            },
            {
                "metric_key": "ambiguous_state_count",
                "metric_value": 3,  # < 10 → NO señal
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_NORMAL_003"],
                "risk_mapping": "Pocos estados ambiguos"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    # Verificar silencio: 0 señales
    assert len(signals) == 0, (
        "Normal operation should produce 0 signals (anti-noise policy)"
    )


def test_silence_normal_operation_produces_low_risk_aggregate(threshold_set_silence):
    """
    Test: Sin señales → RiskAggregate con overall_risk_level=LOW.
    
    Política: Ausencia de señales indica riesgo LOW (operación normal).
    """
    evaluator = ThresholdEvaluator(threshold_set_silence)
    computer = SignalComputer(evaluator)
    assessor = RiskAssessor()
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",
                "metric_value": 1.0,
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_001"],
                "risk_mapping": "Normal"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    # Sin señales
    assert len(signals) == 0
    
    # Assess aggregate con 0 señales
    time_window = {
        "start_at": "2026-01-25T10:00:00",
        "end_at": "2026-01-25T11:00:00"
    }
    aggregate = assessor.assess(time_window, signals, "1.0.0")
    
    # Verificar riesgo LOW
    assert aggregate["overall_risk_level"] == "LOW"
    assert len(aggregate["risk_profile"]) == 0
    assert len(aggregate["drivers"]) == 0


def test_silence_low_risk_produces_zero_alerts(threshold_set_silence):
    """
    Test: Riesgo LOW → 0 alertas (anti-ruido en alerting).
    
    Política: Solo alertar cuando riesgo >= MEDIUM.
    """
    builder = AlertBuilder()
    
    # Aggregate con overall_risk_level=LOW
    aggregate = {
        "aggregate_id": "AGG_LOW",
        "overall_risk_level": "LOW",
        "drivers": [],
        "risk_profile": [],
        "time_window": {
            "start_at": "2026-01-25T10:00:00Z",
            "end_at": "2026-01-25T11:00:00Z"
        },
        "computed_at": "2026-01-25T11:00:00Z",
        "model_version": "1.0.0"
    }
    
    raised_at = datetime.fromisoformat("2026-01-25T11:00:00")
    alerts = builder.build(aggregate, "1.0.0", raised_at)
    
    # Verificar 0 alertas (anti-ruido)
    assert len(alerts) == 0, (
        "LOW risk should produce 0 alerts (anti-noise policy)"
    )


def test_silence_boundary_exactly_at_threshold_produces_signal(threshold_set_silence):
    """
    Test: Valor exactamente en umbral → ACTIVA señal (boundary condition).
    
    Escenario:
    - discrepancy_concentration_pct = 5.0 (exacto threshold LOW con GTE)
    
    Esperado: 1 señal con severity=LOW
    """
    evaluator = ThresholdEvaluator(threshold_set_silence)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",
                "metric_value": 5.0,  # Exacto threshold (GTE)
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_BOUNDARY"],
                "risk_mapping": "Boundary test"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    # Verificar que se activa señal
    assert len(signals) == 1
    assert signals[0]["severity_level"] == "LOW"


def test_silence_below_threshold_by_epsilon_produces_zero_signals(threshold_set_silence):
    """
    Test: Valor justo por debajo de umbral → 0 señales (boundary condition).
    
    Escenario:
    - discrepancy_concentration_pct = 4.99 (< 5.0 threshold)
    
    Esperado: 0 señales (no ruido)
    """
    evaluator = ThresholdEvaluator(threshold_set_silence)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",
                "metric_value": 4.99,  # < 5.0
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_EPSILON"],
                "risk_mapping": "Epsilon below threshold"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    # Verificar silencio
    assert len(signals) == 0


def test_silence_no_matching_rule_produces_zero_signals(threshold_set_silence):
    """
    Test: Métrica sin regla definida → 0 señales (silencio por diseño).
    
    Escenario:
    - metric_key sin regla matching en threshold_set
    
    Esperado: 0 señales (no inventar señales sin gobernanza)
    """
    evaluator = ThresholdEvaluator(threshold_set_silence)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "unknown_metric",  # No existe en threshold_set
                "metric_value": 999.0,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_UNKNOWN"],
                "risk_mapping": "Métrica sin regla"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    # Verificar silencio (no inventar señales)
    assert len(signals) == 0
