"""
RFC-13 Risk Observability - Test: Systemic (Anti-Vanity Metrics)
=================================================================

Test sistémico: Anti-Vanity Metrics (hard fail en métricas técnicas).

OBJETIVO:
- Métricas técnicas puras (CPU, RAM, latency, QPS) NO generan señales
- Validador/contract rechaza payload O SignalComputer lo ignora
- Fundamentación: No-Goals prohíben CPU/latencia/QPS (RFC-13 §2)
"""

import pytest
from datetime import datetime

from core.risk.v1.thresholds import ThresholdEvaluator
from core.risk.v1.signal_computer import SignalComputer


@pytest.fixture
def threshold_set_empty():
    """Fixture: threshold_set vacío (para aislar test de validación)."""
    return {
        "threshold_set_id": "TST_VANITY",
        "threshold_set_version": "1.0.0",
        "approved_change_ref": "CHANGE_VANITY_001",
        "rules": []
    }


def test_anti_vanity_cpu_usage_rejected(threshold_set_empty):
    """
    Test: metric_key 'cpu_usage_pct' → ValueError (hard fail).
    """
    evaluator = ThresholdEvaluator(threshold_set_empty)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "cpu_usage_pct",  # FORBIDDEN
                "metric_value": 85.0,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["INFRA_CPU_001"],
                "risk_mapping": "CPU alto"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    with pytest.raises(ValueError, match="Vanity metric forbidden"):
        computer.compute(observation_bundle, "1.0.0", observed_at)


def test_anti_vanity_ram_usage_rejected(threshold_set_empty):
    """
    Test: metric_key 'ram_used_mb' → ValueError (hard fail).
    """
    evaluator = ThresholdEvaluator(threshold_set_empty)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "ram_used_mb",  # FORBIDDEN
                "metric_value": 8192,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["INFRA_RAM_001"],
                "risk_mapping": "RAM usage"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    with pytest.raises(ValueError, match="Vanity metric forbidden"):
        computer.compute(observation_bundle, "1.0.0", observed_at)


def test_anti_vanity_latency_ms_rejected(threshold_set_empty):
    """
    Test: metric_key 'latency_ms' → ValueError (hard fail).
    """
    evaluator = ThresholdEvaluator(threshold_set_empty)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "latency_ms",  # FORBIDDEN
                "metric_value": 250,
                "scope": "COMPONENT",
                "scope_key": "API_GATEWAY",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["INFRA_LATENCY_001"],
                "risk_mapping": "Latency alta"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    with pytest.raises(ValueError, match="Vanity metric forbidden"):
        computer.compute(observation_bundle, "1.0.0", observed_at)


def test_anti_vanity_qps_rejected(threshold_set_empty):
    """
    Test: metric_key 'qps' → ValueError (hard fail).
    """
    evaluator = ThresholdEvaluator(threshold_set_empty)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "qps",  # FORBIDDEN
                "metric_value": 5000,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["INFRA_QPS_001"],
                "risk_mapping": "QPS alto"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    with pytest.raises(ValueError, match="Vanity metric forbidden"):
        computer.compute(observation_bundle, "1.0.0", observed_at)


def test_anti_vanity_throughput_rejected(threshold_set_empty):
    """
    Test: metric_key 'throughput_mbps' → ValueError (hard fail).
    """
    evaluator = ThresholdEvaluator(threshold_set_empty)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "throughput_mbps",  # FORBIDDEN
                "metric_value": 100,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["INFRA_THROUGHPUT_001"],
                "risk_mapping": "Throughput alto"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    with pytest.raises(ValueError, match="Vanity metric forbidden"):
        computer.compute(observation_bundle, "1.0.0", observed_at)


def test_anti_vanity_memory_rejected(threshold_set_empty):
    """
    Test: metric_key 'memory_percent' → ValueError (hard fail).
    """
    evaluator = ThresholdEvaluator(threshold_set_empty)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "memory_percent",  # FORBIDDEN
                "metric_value": 75,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["INFRA_MEM_001"],
                "risk_mapping": "Memory usage"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    with pytest.raises(ValueError, match="Vanity metric forbidden"):
        computer.compute(observation_bundle, "1.0.0", observed_at)


def test_anti_vanity_load_avg_rejected(threshold_set_empty):
    """
    Test: metric_key 'load_avg_1m' → ValueError (hard fail).
    """
    evaluator = ThresholdEvaluator(threshold_set_empty)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "load_avg_1m",  # FORBIDDEN
                "metric_value": 3.5,
                "scope": "GLOBAL",
                "scope_key": "SYSTEM",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["INFRA_LOAD_001"],
                "risk_mapping": "Load average"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    with pytest.raises(ValueError, match="Vanity metric forbidden"):
        computer.compute(observation_bundle, "1.0.0", observed_at)


def test_anti_vanity_valid_risk_metric_accepted(threshold_set_empty):
    """
    Test: Métrica de riesgo válida (no vanity) → procesamiento OK.
    
    Métrica institucional: 'discrepancy_concentration_pct'
    """
    evaluator = ThresholdEvaluator(threshold_set_empty)
    computer = SignalComputer(evaluator)
    
    observation_bundle = {
        "observations": [
            {
                "metric_key": "discrepancy_concentration_pct",  # VÁLIDO
                "metric_value": 15.0,
                "scope": "SOURCE",
                "scope_key": "SAP_FINANCE",
                "observed_at": "2026-01-25T10:00:00Z",
                "evidence_refs": ["WORM_DISCREP_001"],
                "risk_mapping": "Concentración de discrepancias en SAP"
            }
        ]
    }
    
    observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
    
    # No debe lanzar excepción
    signals = computer.compute(observation_bundle, "1.0.0", observed_at)
    
    # No hay threshold_set rules → 0 señales (silencio), pero validación pasa
    assert len(signals) == 0


def test_anti_vanity_case_insensitive_rejection(threshold_set_empty):
    """
    Test: Validación case-insensitive (CPU vs cpu vs Cpu).
    """
    evaluator = ThresholdEvaluator(threshold_set_empty)
    computer = SignalComputer(evaluator)
    
    # Variantes de case
    vanity_variations = [
        "CPU_usage",
        "cpu_USAGE",
        "Cpu_Usage",
        "RAM_used",
        "Latency_P99",
    ]
    
    for metric_key in vanity_variations:
        observation_bundle = {
            "observations": [
                {
                    "metric_key": metric_key,
                    "metric_value": 100,
                    "scope": "GLOBAL",
                    "scope_key": "SYSTEM",
                    "observed_at": "2026-01-25T10:00:00Z",
                    "evidence_refs": ["INFRA_001"],
                    "risk_mapping": "Test"
                }
            ]
        }
        
        observed_at = datetime.fromisoformat("2026-01-25T10:00:00")
        
        with pytest.raises(ValueError, match="Vanity metric forbidden"):
            computer.compute(observation_bundle, "1.0.0", observed_at)
