"""
RFC-13 Risk Observability - Test: Contracts Conformance
========================================================

Validación de conformidad de contratos (schemas).

OBJETIVO:
- Validar que enums coinciden EXACTO con RFC-13
- Validar additionalProperties: false en todos los contratos
- Verificar taxonomía cerrada (25 signal_types)
"""

import json
import pytest
from pathlib import Path

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts" / "risk" / "v1"


def test_risk_signal_schema_has_closed_taxonomy():
    """Validar que risk_signal.schema.json tiene taxonomía CERRADA de 25 signal_types."""
    schema_path = CONTRACTS_DIR / "risk_signal.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # Verificar que signal_type es enum cerrado
    assert "signal_type" in schema["properties"]
    signal_type_enum = schema["properties"]["signal_type"]["enum"]
    
    # Verificar 25 señales exactas (RFC-13 §4.1-4.6)
    expected_count = 25
    assert len(signal_type_enum) == expected_count, (
        f"Expected {expected_count} signal types, got {len(signal_type_enum)}"
    )
    
    # Verificar prefijos por categoría
    discrepancy_signals = [s for s in signal_type_enum if s.startswith("DISCREPANCY_")]
    correlation_signals = [s for s in signal_type_enum if s.startswith("CORRELATION_")]
    state_signals = [s for s in signal_type_enum if s.startswith("STATE_")]
    idempotency_signals = [s for s in signal_type_enum if s.startswith("IDEMPOTENCY_")]
    change_signals = [s for s in signal_type_enum if s.startswith("CHANGE_")]
    human_signals = [s for s in signal_type_enum if s.startswith("HUMAN_")]
    
    assert len(discrepancy_signals) == 5, "RFC-13 §4.1 expects 5 discrepancy signals"
    assert len(correlation_signals) == 3, "RFC-13 §4.2 expects 3 correlation signals"
    assert len(state_signals) == 5, "RFC-13 §4.3 expects 5 state signals"
    assert len(idempotency_signals) == 4, "RFC-13 §4.4 expects 4 idempotency signals"
    assert len(change_signals) == 5, "RFC-13 §4.5 expects 5 change signals"
    assert len(human_signals) == 3, "RFC-13 §4.6 expects 3 human signals"


def test_risk_signal_schema_has_exact_severity_levels():
    """Validar que severity_level tiene EXACTO 4 niveles sin UNKNOWN."""
    schema_path = CONTRACTS_DIR / "risk_signal.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    severity_enum = schema["properties"]["severity_level"]["enum"]
    
    expected_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert severity_enum == expected_levels, (
        f"Expected {expected_levels}, got {severity_enum}"
    )
    
    # Verificar que NO existe UNKNOWN (hard fail)
    assert "UNKNOWN" not in severity_enum


def test_risk_signal_schema_has_exact_scopes():
    """Validar que scope tiene EXACTO 4 valores (GLOBAL, SOURCE, FLOW, COMPONENT)."""
    schema_path = CONTRACTS_DIR / "risk_signal.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    scope_enum = schema["properties"]["scope"]["enum"]
    
    expected_scopes = ["GLOBAL", "SOURCE", "FLOW", "COMPONENT"]
    assert scope_enum == expected_scopes


def test_all_schemas_have_additional_properties_false():
    """Validar que todos los schemas tienen additionalProperties: false."""
    schema_files = [
        "risk_signal.schema.json",
        "risk_aggregate.schema.json",
        "risk_threshold_set.schema.json",
        "risk_observation.schema.json",
        "risk_alert.schema.json",
    ]
    
    for schema_file in schema_files:
        schema_path = CONTRACTS_DIR / schema_file
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        
        assert schema.get("additionalProperties") is False, (
            f"{schema_file} must have 'additionalProperties: false' at root"
        )


def test_risk_signal_schema_requires_evidence_and_explanation():
    """Validar que supporting_evidence y explanation son obligatorios y no vacíos."""
    schema_path = CONTRACTS_DIR / "risk_signal.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # Verificar que son required
    assert "supporting_evidence" in schema["required"]
    assert "explanation" in schema["required"]
    
    # Verificar minItems=1 para supporting_evidence
    assert schema["properties"]["supporting_evidence"]["minItems"] == 1
    
    # Verificar minLength=1 para explanation
    assert schema["properties"]["explanation"]["minLength"] == 1


def test_risk_threshold_set_forbids_auto_adjustment():
    """Validar que risk_threshold_set.schema.json prohíbe auto-ajuste."""
    schema_path = CONTRACTS_DIR / "risk_threshold_set.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # Verificar que existe cláusula "not" que rechaza auto_tune/learning/adaptive
    assert "not" in schema, "Schema must forbid auto-adjustment fields"


def test_risk_observation_forbids_vanity_metrics():
    """Validar que risk_observation.schema.json rechaza métricas de vanity."""
    schema_path = CONTRACTS_DIR / "risk_observation.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # Verificar que metric_key tiene patrón "not" para CPU/RAM/latency/etc
    metric_key_schema = schema["properties"]["observations"]["items"]["properties"]["metric_key"]
    
    assert "not" in metric_key_schema, (
        "metric_key must have 'not' pattern to reject vanity metrics"
    )


def test_risk_alert_schema_has_exact_alert_types():
    """Validar que alert_type tiene EXACTO 3 tipos (RFC-13 §7.2)."""
    schema_path = CONTRACTS_DIR / "risk_alert.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    alert_type_enum = schema["properties"]["alert_type"]["enum"]
    
    expected_types = ["EARLY_WARNING", "RISK_ESCALATION", "INSTITUTIONAL_BREACH"]
    assert alert_type_enum == expected_types


def test_risk_aggregate_drivers_coherence():
    """Validar que el schema de RiskAggregate documenta coherencia drivers/risk_profile."""
    schema_path = CONTRACTS_DIR / "risk_aggregate.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # Verificar que drivers existe
    assert "drivers" in schema["properties"]
    
    # Verificar que description menciona "subconjunto de risk_profile" (oráculo de coherencia)
    drivers_desc = schema["properties"]["drivers"].get("description", "")
    assert "risk_profile" in drivers_desc.lower(), (
        "drivers description must reference risk_profile coherence"
    )
