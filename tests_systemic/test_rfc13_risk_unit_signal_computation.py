"""
RFC-13 Risk Observability - Test: Unit Signal Computation
==========================================================

Tests unitarios: cálculo correcto de señales.

OBJETIVO:
- Validar que umbral dispara señal correcta
- Validar severity_level conforme a threshold_set
- Validar supporting_evidence y explanation no vacíos
"""

import pytest
from datetime import datetime
from pathlib import Path

from core.risk.v1.enums import RiskSignalType, RiskScope, RiskSeverityLevel
from core.risk.v1.thresholds import ThresholdEvaluator
from core.risk.v1.signal_computer import SignalComputer


@pytest.fixture
def threshold_set_minimal():
    """Fixture: threshold_set mínimo para tests."""
    return {
        "threshold_set_id": "TST_001",
        "threshold_set_version": "1.0.0",
        "approved_change_ref": "CHANGE_CONTROL_2026_001",
        "rules": [
            {
                "signal_type": "DISCREPANCY_CONCENTRATION_HIGH_BY_SOURCE",
                "scope": "SOURCE",
                "metric_key": "discrepancy_concentration_pct",
                "severity_mapping": [
                    {"threshold_value": 5.0, "severity_level": "LOW", "operator": "GTE"},
                    {"threshold_value": 10.0, "severity_level": "MEDIUM", "operator": "GTE"},
                    {"threshold_value": 20.0, "severity_level": "HIGH", "operator": "GTE"},
                    {"threshold_value": 40.0, "severity_level": "CRITICAL", "operator": "GTE"},
                ]
            },
            {
                "signal_type": "CORRELATION_CONFIDENCE_SCORE_DEGRADATION",
                "scope": "GLOBAL",
                "metric_key": "avg_confidence_score",
                "severity_mapping": [
                    {"threshold_value": 0.8, "severity_level": "LOW", "operator": "LT"},
                    {"threshold_value": 0.7, "severity_level": "MEDIUM", "operator": "LT"},
                    {"threshold_value": 0.6, "severity_level": "HIGH", "operator": "LT"},
                    {"threshold_value": 0.5, "severity_level": "CRITICAL", "operator": "LT"},
                ]
            },
        ]
    }


def test_signal_computer_triggers_correct_signal_type(threshold_set_minimal):
    """Validar que umbral dispara signal_type correcto."""
    evaluator = ThresholdEvaluator(threshold_set_minimal)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",
                "metric_value": 25.0,  # Activa HIGH
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_ENTRY_12345"],
                "risk_mapping": "Concentración alta de discrepancias en fuente SAP"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    assert len(signals) == 1
    signal = signals[0]
    
    assert signal["signal_type"] == "DISCREPANCY_CONCENTRATION_HIGH_BY_SOURCE"
    assert signal["severity_level"] == "HIGH"


def test_signal_computer_respects_severity_thresholds(threshold_set_minimal):
    """Validar que severity_level es conforme a threshold_set."""
    evaluator = ThresholdEvaluator(threshold_set_minimal)
    computer = SignalComputer(evaluator)
    
    # Test CRITICAL threshold
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",
                "metric_value": 45.0,  # >= 40.0 → CRITICAL
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_ENTRY_12345"],
                "risk_mapping": "Concentración crítica"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    assert signals[0]["severity_level"] == "CRITICAL"


def test_signal_always_has_supporting_evidence(threshold_set_minimal):
    """Validar que señal siempre incluye supporting_evidence no vacío."""
    evaluator = ThresholdEvaluator(threshold_set_minimal)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",
                "metric_value": 15.0,
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_001", "WORM_002"],
                "risk_mapping": "Evidencia múltiple"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    signal = signals[0]
    assert "supporting_evidence" in signal
    assert len(signal["supporting_evidence"]) >= 1
    
    # Verificar estructura de evidencia
    for evidence in signal["supporting_evidence"]:
        assert "evidence_type" in evidence
        assert "evidence_ref" in evidence


def test_signal_always_has_explanation(threshold_set_minimal):
    """Validar que señal siempre incluye explanation no vacío."""
    evaluator = ThresholdEvaluator(threshold_set_minimal)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",
                "metric_value": 15.0,
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_001"],
                "risk_mapping": "Concentración detectada"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    signal = signals[0]
    assert "explanation" in signal
    assert len(signal["explanation"]) > 0
    
    # Verificar que explanation incluye contexto institucional
    explanation = signal["explanation"]
    assert "Riesgo" in explanation
    assert signal["signal_type"] in explanation


def test_signal_computer_anti_noise_no_signal_below_threshold(threshold_set_minimal):
    """Validar política anti-ruido: no generar señal si no hay umbral activado."""
    evaluator = ThresholdEvaluator(threshold_set_minimal)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",
                "metric_value": 2.0,  # < 5.0 (threshold mínimo) → NO señal
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_001"],
                "risk_mapping": "Valor bajo"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    # Anti-ruido: no generar señales innecesarias
    assert len(signals) == 0


def test_signal_computer_rejects_vanity_metrics():
    """Validar que SignalComputer rechaza métricas de vanity (hard fail)."""
    threshold_set = {
        "threshold_set_id": "TST_VANITY",
        "threshold_set_version": "1.0.0",
        "approved_change_ref": "CHANGE_001",
        "rules": []
    }
    
    evaluator = ThresholdEvaluator(threshold_set)
    computer = SignalComputer(evaluator)
    
    vanity_observation = {
        "observations": [
            {
                "metric_key": "cpu_usage_pct",  # FORBIDDEN
                "metric_value": 80.0,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["INFRA_001"],
                "risk_mapping": "CPU alto"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    with pytest.raises(ValueError, match="Vanity metric forbidden"):
        computer.compute(vanity_observation, "1.0.0", observed_at)


def test_signal_supports_all_signal_type_families():
    """Validar que SignalComputer soporta todas las familias de señales (§4.1-4.6)."""
    # Verificar que RiskSignalType tiene 25 valores exactos
    signal_types = list(RiskSignalType)
    assert len(signal_types) == 25
    
    # Verificar familias
    discrepancy_count = sum(1 for st in signal_types if st.value.startswith("DISCREPANCY_"))
    correlation_count = sum(1 for st in signal_types if st.value.startswith("CORRELATION_"))
    state_count = sum(1 for st in signal_types if st.value.startswith("STATE_"))
    idempotency_count = sum(1 for st in signal_types if st.value.startswith("IDEMPOTENCY_"))
    change_count = sum(1 for st in signal_types if st.value.startswith("CHANGE_"))
    human_count = sum(1 for st in signal_types if st.value.startswith("HUMAN_"))
    
    assert discrepancy_count == 5
    assert correlation_count == 3
    assert state_count == 5
    assert idempotency_count == 4
    assert change_count == 5
    assert human_count == 3
