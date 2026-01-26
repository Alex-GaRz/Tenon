"""
RFC-13 Risk Observability - Test: Systemic (Degradación Progresiva)
====================================================================

Test sistémico: Degradación progresiva de riesgo (oráculo institucional).

OBJETIVO:
- Simular escalamiento LOW → MEDIUM → HIGH → CRITICAL
- Verificar que overall_risk_level sigue la severidad máxima
- Validar determinismo de drivers
"""

import pytest
from datetime import datetime, timedelta

from core.risk.v1.thresholds import ThresholdEvaluator
from core.risk.v1.signal_computer import SignalComputer
from core.risk.v1.risk_assessor import RiskAssessor


@pytest.fixture
def threshold_set_progressive():
    """Fixture: threshold_set para degradación progresiva."""
    return {
        "threshold_set_id": "TST_PROG",
        "threshold_set_version": "1.0.0",
        "approved_change_ref": "CHANGE_PROG_001",
        "rules": [
            {
                "signal_type": "IDEMPOTENCY_REJECT_DUPLICATE_INCREASE",
                "scope": "GLOBAL",
                "metric_key": "reject_duplicate_rate_pct",
                "severity_mapping": [
                    {"threshold_value": 1.0, "severity_level": "LOW", "operator": "GTE"},
                    {"threshold_value": 5.0, "severity_level": "MEDIUM", "operator": "GTE"},
                    {"threshold_value": 15.0, "severity_level": "HIGH", "operator": "GTE"},
                    {"threshold_value": 30.0, "severity_level": "CRITICAL", "operator": "GTE"},
                ]
            },
            {
                "signal_type": "IDEMPOTENCY_FLAG_AMBIGUOUS_INCREASE",
                "scope": "GLOBAL",
                "metric_key": "flag_ambiguous_rate_pct",
                "severity_mapping": [
                    {"threshold_value": 2.0, "severity_level": "LOW", "operator": "GTE"},
                    {"threshold_value": 8.0, "severity_level": "MEDIUM", "operator": "GTE"},
                    {"threshold_value": 20.0, "severity_level": "HIGH", "operator": "GTE"},
                    {"threshold_value": 40.0, "severity_level": "CRITICAL", "operator": "GTE"},
                ]
            }
        ]
    }


def test_progressive_degradation_low_to_critical(threshold_set_progressive):
    """
    Test sistémico: Degradación progresiva LOW → MEDIUM → HIGH → CRITICAL.
    
    Escenario:
    - W1: reject_duplicate_rate = 2% → LOW
    - W2: reject_duplicate_rate = 7% → MEDIUM
    - W3: reject_duplicate_rate = 18% → HIGH
    - W4: reject_duplicate_rate = 35% → CRITICAL
    
    Verificaciones:
    - overall_risk_level escala determinísticamente
    - drivers se actualizan correctamente
    """
    evaluator = ThresholdEvaluator(threshold_set_progressive)
    computer = SignalComputer(evaluator)
    assessor = RiskAssessor()
    
    base_time = datetime(2026, 1, 25, 10, 0, 0)
    
    # Definir 4 ventanas con valores progresivos
    windows_data = [
        {"value": 2.0, "expected_severity": "LOW", "label": "W1"},
        {"value": 7.0, "expected_severity": "MEDIUM", "label": "W2"},
        {"value": 18.0, "expected_severity": "HIGH", "label": "W3"},
        {"value": 35.0, "expected_severity": "CRITICAL", "label": "W4"},
    ]
    
    aggregates = []
    
    for i, window_data in enumerate(windows_data):
        window_time = base_time + timedelta(hours=i)
        
        observation_bundle = {
            "observations": [
                {
                    "metric_key": "reject_duplicate_rate_pct",
                    "metric_value": window_data["value"],
                    "scope": "GLOBAL",
                    "scope_key": "SYSTEM",
                    "observed_at": window_time.isoformat() + "Z",
                    "evidence_refs": [f"WORM_{window_data['label']}"],
                    "risk_mapping": f"Incremento de REJECT_DUPLICATE en {window_data['label']}"
                }
            ]
        }
        
        # Compute signals
        signals = computer.compute(observation_bundle, "1.0.0", window_time)
        
        # Assert: verificar severidad esperada
        assert len(signals) == 1, f"Expected 1 signal in {window_data['label']}"
        assert signals[0]["severity_level"] == window_data["expected_severity"], (
            f"{window_data['label']}: Expected {window_data['expected_severity']}, "
            f"got {signals[0]['severity_level']}"
        )
        
        # Assess aggregate
        time_window = {
            "start_at": window_time.isoformat(),
            "end_at": (window_time + timedelta(hours=1)).isoformat()
        }
        aggregate = assessor.assess(time_window, signals, "1.0.0")
        
        # Verificar overall_risk_level
        assert aggregate["overall_risk_level"] == window_data["expected_severity"], (
            f"{window_data['label']}: Aggregate overall_risk_level mismatch"
        )
        
        # Verificar drivers
        assert len(aggregate["drivers"]) == 1, f"{window_data['label']}: Expected 1 driver"
        assert signals[0]["risk_signal_id"] in aggregate["drivers"], (
            f"{window_data['label']}: Driver mismatch"
        )
        
        aggregates.append(aggregate)
    
    # Verificar escalamiento global
    severity_progression = [agg["overall_risk_level"] for agg in aggregates]
    assert severity_progression == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_progressive_degradation_with_multiple_signals(threshold_set_progressive):
    """
    Test sistémico: Degradación con múltiples señales concurrentes.
    
    Escenario:
    - W1: REJECT_DUPLICATE=2% (LOW) + FLAG_AMBIGUOUS=3% (LOW) → overall=LOW
    - W2: REJECT_DUPLICATE=7% (MEDIUM) + FLAG_AMBIGUOUS=10% (MEDIUM) → overall=MEDIUM
    - W3: REJECT_DUPLICATE=18% (HIGH) + FLAG_AMBIGUOUS=25% (HIGH) → overall=HIGH
    - W4: REJECT_DUPLICATE=35% (CRITICAL) + FLAG_AMBIGUOUS=45% (CRITICAL) → overall=CRITICAL
    """
    evaluator = ThresholdEvaluator(threshold_set_progressive)
    computer = SignalComputer(evaluator)
    assessor = RiskAssessor()
    
    base_time = datetime(2026, 1, 25, 10, 0, 0)
    
    windows_data = [
        {"reject": 2.0, "flag": 3.0, "expected": "LOW"},
        {"reject": 7.0, "flag": 10.0, "expected": "MEDIUM"},
        {"reject": 18.0, "flag": 25.0, "expected": "HIGH"},
        {"reject": 35.0, "flag": 45.0, "expected": "CRITICAL"},
    ]
    
    for i, window_data in enumerate(windows_data):
        window_time = base_time + timedelta(hours=i)
        
        observation_bundle = {
            "observations": [
                {
                    "metric_key": "reject_duplicate_rate_pct",
                    "metric_value": window_data["reject"],
                    "scope": "GLOBAL",
                    "scope_key": "SYSTEM",
                    "observed_at": window_time.isoformat() + "Z",
                    "evidence_refs": [f"WORM_REJECT_W{i+1}"],
                    "risk_mapping": "REJECT_DUPLICATE increase"
                },
                {
                    "metric_key": "flag_ambiguous_rate_pct",
                    "metric_value": window_data["flag"],
                    "scope": "GLOBAL",
                    "scope_key": "SYSTEM",
                    "observed_at": window_time.isoformat() + "Z",
                    "evidence_refs": [f"WORM_FLAG_W{i+1}"],
                    "risk_mapping": "FLAG_AMBIGUOUS increase"
                }
            ]
        }
        
        signals = computer.compute(observation_bundle, "1.0.0", window_time)
        
        # Verificar que se generaron 2 señales
        assert len(signals) == 2
        
        # Verificar que ambas tienen la severidad esperada
        for signal in signals:
            assert signal["severity_level"] == window_data["expected"]
        
        # Assess aggregate
        time_window = {
            "start_at": window_time.isoformat(),
            "end_at": (window_time + timedelta(hours=1)).isoformat()
        }
        aggregate = assessor.assess(time_window, signals, "1.0.0")
        
        # Verificar overall_risk_level (max de ambas señales)
        assert aggregate["overall_risk_level"] == window_data["expected"]
        
        # Verificar drivers (ambas señales deben ser drivers si igualan overall)
        assert len(aggregate["drivers"]) == 2


def test_aggregate_drivers_are_only_max_severity_signals(threshold_set_progressive):
    """
    Test sistémico: Drivers solo incluyen señales que igualan overall_risk_level.
    
    Escenario:
    - Señal A: HIGH
    - Señal B: CRITICAL
    - overall_risk_level = CRITICAL (max)
    - drivers = [Señal B] (solo la CRITICAL)
    """
    evaluator = ThresholdEvaluator(threshold_set_progressive)
    computer = SignalComputer(evaluator)
    assessor = RiskAssessor()
    
    window_time = datetime(2026, 1, 25, 10, 0, 0)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "reject_duplicate_rate_pct",
                "metric_value": 18.0,  # HIGH
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": window_time.isoformat() + "Z",
                "evidence_refs": ["WORM_A"],
                "risk_mapping": "HIGH signal"
            },
            {
                "metric_key": "flag_ambiguous_rate_pct",
                "metric_value": 45.0,  # CRITICAL
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": window_time.isoformat() + "Z",
                "evidence_refs": ["WORM_B"],
                "risk_mapping": "CRITICAL signal"
            }
        ]
    }
    
    signals = computer.compute(observation_bundle, "1.0.0", window_time)
    assert len(signals) == 2
    
    # Identificar señales por severidad
    high_signal = next(s for s in signals if s["severity_level"] == "HIGH")
    critical_signal = next(s for s in signals if s["severity_level"] == "CRITICAL")
    
    # Assess aggregate
    time_window = {
        "start_at": window_time.isoformat(),
        "end_at": (window_time + timedelta(hours=1)).isoformat()
    }
    aggregate = assessor.assess(time_window, signals, "1.0.0")
    
    # Verificar overall = CRITICAL
    assert aggregate["overall_risk_level"] == "CRITICAL"
    
    # Verificar drivers = [CRITICAL signal only]
    assert len(aggregate["drivers"]) == 1
    assert critical_signal["risk_signal_id"] in aggregate["drivers"]
    assert high_signal["risk_signal_id"] not in aggregate["drivers"]
