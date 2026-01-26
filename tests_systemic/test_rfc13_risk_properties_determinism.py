"""
RFC-13 Risk Observability - Test: Properties (Determinism)
===========================================================

Tests de propiedades: determinismo, no side-effects, replay estable.

OBJETIVO:
- Mismo input → mismas señales/agregados/alertas byte-for-byte
- Verificar que core no usa reloj del sistema
- Replay reproduce resultados históricos
"""

import pytest
from datetime import datetime, timedelta
import copy

from core.risk.v1.enums import RiskSignalType, RiskScope, RiskSeverityLevel
from core.risk.v1.thresholds import ThresholdEvaluator
from core.risk.v1.signal_computer import SignalComputer
from core.risk.v1.risk_assessor import RiskAssessor
from core.risk.v1.alert_builder import AlertBuilder


@pytest.fixture
def threshold_set_determinism():
    """Fixture: threshold_set para tests de determinismo."""
    return {
        "threshold_set_id": "TST_DETERM",
        "threshold_set_version": "1.0.0",
        "approved_change_ref": "CHANGE_DET_001",
        "rules": [
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


def test_signal_computer_is_deterministic(threshold_set_determinism):
    """
    Propiedad: Mismo input → mismas señales byte-for-byte.
    
    Algoritmo:
    - Ejecutar compute() dos veces con mismo input
    - Verificar que señales son idénticas (deep equality)
    """
    evaluator = ThresholdEvaluator(threshold_set_determinism)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "ambiguous_state_count",
                "metric_value": 60,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_001", "WORM_002"],
                "risk_mapping": "Acumulación de estados ambiguos fuera de SLA"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    # Run 1
    signals_run1 = computer.compute(
        copy.deepcopy(observation_bundle),
        "1.0.0",
        observed_at
    )
    
    # Run 2 (mismo input)
    signals_run2 = computer.compute(
        copy.deepcopy(observation_bundle),
        "1.0.0",
        observed_at
    )
    
    # Verificar determinismo (misma cantidad de señales)
    assert len(signals_run1) == len(signals_run2)
    
    # Verificar deep equality (excluyendo UUIDs que pueden variar)
    for sig1, sig2 in zip(signals_run1, signals_run2):
        # Comparar campos deterministas
        assert sig1["signal_type"] == sig2["signal_type"]
        assert sig1["severity_level"] == sig2["severity_level"]
        assert sig1["scope"] == sig2["scope"]
        assert sig1["observed_at"] == sig2["observed_at"]
        assert sig1["supporting_metrics"] == sig2["supporting_metrics"]
        assert sig1["supporting_evidence"] == sig2["supporting_evidence"]
        assert sig1["explanation"] == sig2["explanation"]


def test_risk_assessor_is_deterministic():
    """
    Propiedad: Mismo input (señales + ventana) → mismo agregado.
    
    Algoritmo:
    - Ejecutar assess() dos veces con mismo input
    - Verificar que agregado es idéntico
    """
    assessor = RiskAssessor()
    
    time_window = {
        "start_at": "2026-01-25T10:00:00Z",
        "end_at": "2026-01-25T11:00:00Z"
    }
    
    signals = [
        {
            "risk_signal_id": "SIG_001",
            "signal_type": "STATE_AMBIGUOUS_ACCUMULATION_OUTSIDE_SLA",
            "severity_level": "CRITICAL",
            "scope": "GLOBAL",
        },
        {
            "risk_signal_id": "SIG_002",
            "signal_type": "CORRELATION_CONFIDENCE_SCORE_DEGRADATION",
            "severity_level": "HIGH",
            "scope": "GLOBAL",
        }
    ]
    
    # Run 1
    aggregate_run1 = assessor.assess(
        copy.deepcopy(time_window),
        copy.deepcopy(signals),
        "1.0.0"
    )
    
    # Run 2
    aggregate_run2 = assessor.assess(
        copy.deepcopy(time_window),
        copy.deepcopy(signals),
        "1.0.0"
    )
    
    # Verificar determinismo
    assert aggregate_run1["overall_risk_level"] == aggregate_run2["overall_risk_level"]
    assert aggregate_run1["drivers"] == aggregate_run2["drivers"]
    assert aggregate_run1["computed_at"] == aggregate_run2["computed_at"]
    assert aggregate_run1["time_window"] == aggregate_run2["time_window"]


def test_alert_builder_is_deterministic():
    """
    Propiedad: Mismo input (aggregate) → misma alerta.
    """
    builder = AlertBuilder()
    
    aggregate = {
        "aggregate_id": "AGG_001",
        "overall_risk_level": "CRITICAL",
        "drivers": ["SIG_001"],
        "risk_profile": [
            {
                "risk_signal_id": "SIG_001",
                "signal_type": "STATE_AMBIGUOUS_ACCUMULATION_OUTSIDE_SLA",
                "severity_level": "CRITICAL"
            }
        ],
        "time_window": {
            "start_at": "2026-01-25T10:00:00Z",
            "end_at": "2026-01-25T11:00:00Z"
        },
        "computed_at": "2026-01-25T11:00:00Z",
        "model_version": "1.0.0"
    }
    
    raised_at = datetime.fromisoformat("2026-01-25T11:00:00")
    
    # Run 1
    alerts_run1 = builder.build(copy.deepcopy(aggregate), "1.0.0", raised_at)
    
    # Run 2
    alerts_run2 = builder.build(copy.deepcopy(aggregate), "1.0.0", raised_at)
    
    assert len(alerts_run1) == len(alerts_run2)
    
    for alert1, alert2 in zip(alerts_run1, alerts_run2):
        assert alert1["alert_type"] == alert2["alert_type"]
        assert alert1["aggregate_id"] == alert2["aggregate_id"]
        assert alert1["signal_ids"] == alert2["signal_ids"]
        assert alert1["potential_impact"] == alert2["potential_impact"]
        assert alert1["operational_recommendation"] == alert2["operational_recommendation"]


def test_core_does_not_use_system_clock(threshold_set_determinism):
    """
    Propiedad: Core no usa reloj del sistema (timestamps inyectados).
    
    Algoritmo:
    - Congelar tiempo conceptualmente (usar timestamps fijos)
    - Verificar que computed_at/observed_at son los inyectados, no datetime.now()
    """
    evaluator = ThresholdEvaluator(threshold_set_determinism)
    computer = SignalComputer(evaluator)
    assessor = RiskAssessor()
    
    # Timestamp fijo inyectado
    fixed_time = datetime(2026, 1, 25, 10, 0, 0)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "ambiguous_state_count",
                "metric_value": 60,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": fixed_time.isoformat() + "Z",
                "evidence_refs": ["WORM_001"],
                "risk_mapping": "Test"
            }
        ]
    }
    
    # Compute signal
    signals = computer.compute(observation_bundle, "1.0.0", fixed_time)
    
    # Verificar que observed_at es el inyectado
    assert signals[0]["observed_at"] == fixed_time.isoformat()
    
    # Assess aggregate
    time_window = {
        "start_at": fixed_time.isoformat(),
        "end_at": (fixed_time + timedelta(hours=1)).isoformat()
    }
    
    aggregate = assessor.assess(time_window, signals, "1.0.0")
    
    # Verificar que computed_at es time_window.end_at (no reloj del sistema)
    assert aggregate["computed_at"] == time_window["end_at"]


def test_replay_produces_stable_results(threshold_set_determinism):
    """
    Propiedad: Replay de histórico → resultados estables.
    
    Algoritmo:
    - Simular 3 ventanas temporales consecutivas
    - Replay: procesar mismo histórico dos veces
    - Verificar que resultados son idénticos
    """
    evaluator = ThresholdEvaluator(threshold_set_determinism)
    computer = SignalComputer(evaluator)
    assessor = RiskAssessor()
    
    # Histórico: 3 ventanas
    windows = [
        datetime(2026, 1, 25, 10, 0, 0),
        datetime(2026, 1, 25, 11, 0, 0),
        datetime(2026, 1, 25, 12, 0, 0),
    ]
    
    historical_observations = [
        {
            "observations": [
                {
                    "metric_key": "ambiguous_state_count",
                    "metric_value": 15,
                    "scope": "GLOBAL",
                    "scope_key": "SYSTEM",
                    "observed_at": windows[0].isoformat() + "Z",
                    "evidence_refs": ["WORM_W1"],
                    "risk_mapping": "Ventana 1"
                }
            ]
        },
        {
            "observations": [
                {
                    "metric_key": "ambiguous_state_count",
                    "metric_value": 30,
                    "scope": "GLOBAL",
                    "scope_key": "SYSTEM",
                    "observed_at": windows[1].isoformat() + "Z",
                    "evidence_refs": ["WORM_W2"],
                    "risk_mapping": "Ventana 2"
                }
            ]
        },
        {
            "observations": [
                {
                    "metric_key": "ambiguous_state_count",
                    "metric_value": 55,
                    "scope": "GLOBAL",
                    "scope_key": "SYSTEM",
                    "observed_at": windows[2].isoformat() + "Z",
                    "evidence_refs": ["WORM_W3"],
                    "risk_mapping": "Ventana 3"
                }
            ]
        }
    ]
    
    def replay_history(observations_list):
        """Procesa histórico y retorna señales + agregados."""
        all_signals = []
        all_aggregates = []
        
        for i, obs_bundle in enumerate(observations_list):
            signals = computer.compute(obs_bundle, "1.0.0", windows[i])
            all_signals.extend(signals)
            
            time_window = {
                "start_at": windows[i].isoformat(),
                "end_at": (windows[i] + timedelta(hours=1)).isoformat()
            }
            aggregate = assessor.assess(time_window, signals, "1.0.0")
            all_aggregates.append(aggregate)
        
        return all_signals, all_aggregates
    
    # Replay 1
    signals_replay1, aggregates_replay1 = replay_history(copy.deepcopy(historical_observations))
    
    # Replay 2
    signals_replay2, aggregates_replay2 = replay_history(copy.deepcopy(historical_observations))
    
    # Verificar estabilidad
    assert len(signals_replay1) == len(signals_replay2)
    assert len(aggregates_replay1) == len(aggregates_replay2)
    
    # Verificar que agregados tienen mismo overall_risk_level
    for agg1, agg2 in zip(aggregates_replay1, aggregates_replay2):
        assert agg1["overall_risk_level"] == agg2["overall_risk_level"]
        assert agg1["drivers"] == agg2["drivers"]


def test_no_side_effects_in_signal_computation(threshold_set_determinism):
    """
    Propiedad: Computación de señales no tiene side effects.
    
    Algoritmo:
    - Ejecutar compute() con observation_bundle
    - Verificar que observation_bundle no se mutó
    """
    evaluator = ThresholdEvaluator(threshold_set_determinism)
    computer = SignalComputer(evaluator)
    
    observation_bundle_original = {
        "observations": [
            {
                "metric_key": "ambiguous_state_count",
                "metric_value": 60,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_001"],
                "risk_mapping": "Test"
            }
        ]
    }
    
    observation_bundle = copy.deepcopy(observation_bundle_original)
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    # Verificar que input no se mutó
    assert observation_bundle == observation_bundle_original
