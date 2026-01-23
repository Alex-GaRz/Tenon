"""
RFC-03 Systemic Tests: End-to-end normalization scenarios with fixtures.

Scenarios:
- Version change: new events use new rule, old events unchanged
- Corrupt raw payload: graceful failure
- Mixed formats: json/csv/pdf (format-specific rules)
"""

import json

from core.ingest.v1.raw_payload_store import RawPayloadStore
from core.normalization.v1.rule_registry import RuleRegistry
from core.normalization.v1.diff_store import DiffStore
from core.normalization.v1.normalization_engine import normalize_ingest_record


def test_systemic_version_change_new_events_use_new_rule(tmp_path):
    """Systemic: Rule version change → new events use new rule, old events unchanged."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    diff_store = DiffStore()
    
    # Fixture: version change scenario
    fixture = {
        "scenario": "version_change_new_events_use_new_rule",
        "old_rule": {
            "rule_id": "rule_v1",
            "rule_version": "1.0.0",
            "normalizer_version": "1.0.0",
            "input_signature": {
                "source_system": "bank_versioned",
                "raw_format": "json",
                "schema_hint": "v1"
            },
            "mapping": [
                {"raw_path": "amount", "canonical_path": "amount"}
            ],
            "lossy_fields": [],
            "warnings": []
        },
        "new_rule": {
            "rule_id": "rule_v2",
            "rule_version": "2.0.0",
            "normalizer_version": "1.0.0",
            "input_signature": {
                "source_system": "bank_versioned",
                "raw_format": "json",
                "schema_hint": "v2"
            },
            "mapping": [
                {"raw_path": "amount", "canonical_path": "amount"},
                {"raw_path": "currency", "canonical_path": "currency"}
            ],
            "lossy_fields": [],
            "warnings": []
        }
    }
    
    # Register old rule
    registry.register(fixture["old_rule"])
    
    # Normalize with old rule
    old_payload = json.dumps({"amount": 100}).encode("utf-8")
    hash_old, ptr_old, size_old = raw_store.append(old_payload, raw_format="json")
    
    ingest_old = {
        "raw_pointer": ptr_old,
        "source_system": "bank_versioned",
        "raw_format": "json",
        "schema_hint": "v1",
        "event_id": "evt_old"
    }
    
    canonical_old, result_old = normalize_ingest_record(ingest_old, raw_store, registry, diff_store)
    
    assert canonical_old is not None
    assert canonical_old["amount"] == 100
    assert "currency" not in canonical_old  # Not in v1 mapping
    
    # Register new rule
    registry.register(fixture["new_rule"])
    
    # Normalize with new rule
    new_payload = json.dumps({"amount": 200, "currency": "GBP"}).encode("utf-8")
    hash_new, ptr_new, size_new = raw_store.append(new_payload, raw_format="json")
    
    ingest_new = {
        "raw_pointer": ptr_new,
        "source_system": "bank_versioned",
        "raw_format": "json",
        "schema_hint": "v2",
        "event_id": "evt_new"
    }
    
    canonical_new, result_new = normalize_ingest_record(ingest_new, raw_store, registry, diff_store)
    
    assert canonical_new is not None
    assert canonical_new["amount"] == 200
    assert canonical_new["currency"] == "GBP"  # New field in v2
    
    # Old event unchanged (re-normalize with v1)
    canonical_old_again, _ = normalize_ingest_record(ingest_old, raw_store, registry, diff_store)
    assert canonical_old_again == canonical_old


def test_systemic_old_events_unchanged(tmp_path):
    """Systemic: After rule update, re-normalizing old events with old schema_hint → unchanged."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    diff_store = DiffStore()
    
    # Register v1 rule
    rule_v1 = {
        "rule_id": "rule_stability",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "bank_stable",
            "raw_format": "json",
            "schema_hint": "v1"
        },
        "mapping": [{"raw_path": "field_a", "canonical_path": "field_a"}],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule_v1)
    
    # Normalize event with v1
    payload_v1 = json.dumps({"field_a": "value_a"}).encode("utf-8")
    hash_v1, ptr_v1, size_v1 = raw_store.append(payload_v1, raw_format="json")
    
    ingest_v1 = {
        "raw_pointer": ptr_v1,
        "source_system": "bank_stable",
        "raw_format": "json",
        "schema_hint": "v1",
        "event_id": "evt_v1"
    }
    
    canonical_before, _ = normalize_ingest_record(ingest_v1, raw_store, registry, diff_store)
    
    # Register v2 rule (different mapping)
    rule_v2 = {
        "rule_id": "rule_stability",
        "rule_version": "2.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "bank_stable",
            "raw_format": "json",
            "schema_hint": "v2"
        },
        "mapping": [{"raw_path": "field_b", "canonical_path": "field_b"}],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule_v2)
    
    # Re-normalize old event (still using v1 schema_hint)
    canonical_after, _ = normalize_ingest_record(ingest_v1, raw_store, registry, diff_store)
    
    # Old event unchanged
    assert canonical_after == canonical_before


def test_systemic_corrupt_raw_payload(tmp_path):
    """Systemic: Corrupt raw payload → normalization fails gracefully."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    diff_store = DiffStore()
    
    # Register rule
    rule = {
        "rule_id": "rule_corrupt",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "bank_corrupt",
            "raw_format": "json",
            "schema_hint": "default"
        },
        "mapping": [{"raw_path": "data", "canonical_path": "data"}],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule)
    
    # Corrupt payload (invalid JSON)
    corrupt_payload = b"{ not valid json }"
    hash_corrupt, ptr_corrupt, size_corrupt = raw_store.append(corrupt_payload, raw_format="json")
    
    ingest_corrupt = {
        "raw_pointer": ptr_corrupt,
        "source_system": "bank_corrupt",
        "raw_format": "json",
        "schema_hint": "default",
        "event_id": None
    }
    
    # Normalize
    canonical, result = normalize_ingest_record(ingest_corrupt, raw_store, registry, diff_store)
    
    # Normalization failed
    assert canonical is None
    
    # Warnings present
    assert len(result["warnings"]) > 0
    assert any("parse" in w.lower() for w in result["warnings"])
    
    # Diff still created
    assert result["diff_reference"].startswith("diff:")


def test_systemic_mixed_formats_json_csv_pdf(tmp_path):
    """Systemic: Mixed formats (json/csv/pdf) → format-specific rules."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    diff_store = DiffStore()
    
    # JSON rule
    rule_json = {
        "rule_id": "rule_json",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "multi_format",
            "raw_format": "json",
            "schema_hint": "default"
        },
        "mapping": [{"raw_path": "json_field", "canonical_path": "data"}],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule_json)
    
    # JSON payload
    json_payload = json.dumps({"json_field": "json_value"}).encode("utf-8")
    hash_json, ptr_json, size_json = raw_store.append(json_payload, raw_format="json")
    
    ingest_json = {
        "raw_pointer": ptr_json,
        "source_system": "multi_format",
        "raw_format": "json",
        "schema_hint": "default",
        "event_id": "evt_json"
    }
    
    canonical_json, result_json = normalize_ingest_record(ingest_json, raw_store, registry, diff_store)
    
    assert canonical_json is not None
    assert canonical_json["data"] == "json_value"
    
    # CSV/PDF not implemented (should fail gracefully)
    csv_payload = b"csv,data,here"
    hash_csv, ptr_csv, size_csv = raw_store.append(csv_payload, raw_format="csv")
    
    ingest_csv = {
        "raw_pointer": ptr_csv,
        "source_system": "multi_format",
        "raw_format": "csv",
        "schema_hint": "default",
        "event_id": None
    }
    
    canonical_csv, result_csv = normalize_ingest_record(ingest_csv, raw_store, registry, diff_store)
    
    # No rule for CSV → fails
    assert canonical_csv is None
    assert any("No normalization rule" in w for w in result_csv["warnings"])
