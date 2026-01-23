"""
RFC-03 Unit Tests: Normalization Rules guarantees.

Tests:
- Mapping only declared fields (rest not populated)
- normalizer_version always present
- Exact rule matching (no fallback)
- UNKNOWN for non-inferible fields
"""

import json

from core.ingest.v1.raw_payload_store import RawPayloadStore
from core.normalization.v1.rule_registry import RuleRegistry
from core.normalization.v1.diff_store import DiffStore
from core.normalization.v1.normalization_engine import normalize_ingest_record


def test_rule_registry_exact_match():
    """Rule registry requires exact match on all 3 fields."""
    registry = RuleRegistry()
    
    rule = {
        "rule_id": "rule_001",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "bank_a",
            "raw_format": "json",
            "schema_hint": "v1"
        },
        "mapping": [],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule)
    
    # Exact match
    found = registry.get_rule("bank_a", "json", "v1")
    assert found is not None
    assert found["rule_id"] == "rule_001"
    
    # No partial match
    assert registry.get_rule("bank_a", "json", "v2") is None
    assert registry.get_rule("bank_a", "csv", "v1") is None
    assert registry.get_rule("bank_b", "json", "v1") is None


def test_normalization_mapping_only_declared_fields():
    """Normalization only populates fields declared in mapping."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    diff_store = DiffStore()
    
    raw_payload = json.dumps({
        "amount": 100,
        "currency": "USD",
        "extra_field": "should_be_ignored"
    }).encode("utf-8")
    
    hash_val, ptr, size = raw_store.append(raw_payload, raw_format="json")
    
    rule = {
        "rule_id": "rule_002",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "bank_b",
            "raw_format": "json",
            "schema_hint": "default"
        },
        "mapping": [
            {"raw_path": "amount", "canonical_path": "amount"},
            {"raw_path": "currency", "canonical_path": "currency"}
        ],
        "lossy_fields": ["extra_field"],
        "warnings": []
    }
    
    registry.register(rule)
    
    ingest_record = {
        "raw_pointer": ptr,
        "source_system": "bank_b",
        "raw_format": "json",
        "event_id": "evt_001"
    }
    
    canonical, result = normalize_ingest_record(ingest_record, raw_store, registry, diff_store)
    
    # Only mapped fields populated
    assert canonical is not None
    assert canonical["amount"] == 100
    assert canonical["currency"] == "USD"
    assert "extra_field" not in canonical


def test_normalization_unknown_for_missing_fields():
    """Fields not in raw payload → UNKNOWN in canonical."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    diff_store = DiffStore()
    
    raw_payload = json.dumps({"amount": 50}).encode("utf-8")
    hash_val, ptr, size = raw_store.append(raw_payload, raw_format="json")
    
    rule = {
        "rule_id": "rule_003",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "bank_c",
            "raw_format": "json",
            "schema_hint": "default"
        },
        "mapping": [
            {"raw_path": "amount", "canonical_path": "amount"},
            {"raw_path": "missing_field", "canonical_path": "direction"}
        ],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule)
    
    ingest_record = {
        "raw_pointer": ptr,
        "source_system": "bank_c",
        "raw_format": "json",
        "event_id": "evt_002"
    }
    
    canonical, result = normalize_ingest_record(ingest_record, raw_store, registry, diff_store)
    
    # Missing field → UNKNOWN
    assert canonical is not None
    assert canonical["amount"] == 50
    assert canonical["direction"] == "UNKNOWN"
    
    # Warning generated
    assert any("missing_field" in w for w in result["warnings"])


def test_normalizer_version_always_present():
    """normalizer_version is mandatory in result and applied_rules."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    diff_store = DiffStore()
    
    raw_payload = json.dumps({"test": "data"}).encode("utf-8")
    hash_val, ptr, size = raw_store.append(raw_payload, raw_format="json")
    
    rule = {
        "rule_id": "rule_004",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "sys",
            "raw_format": "json",
            "schema_hint": "default"
        },
        "mapping": [{"raw_path": "test", "canonical_path": "test"}],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule)
    
    ingest_record = {
        "raw_pointer": ptr,
        "source_system": "sys",
        "raw_format": "json",
        "event_id": "evt_003"
    }
    
    canonical, result = normalize_ingest_record(ingest_record, raw_store, registry, diff_store)
    
    # normalizer_version in result
    assert "normalizer_version" in result
    assert result["normalizer_version"] == "1.0.0"
    
    # normalizer_version in applied_rules
    assert len(result["applied_rules"]) == 1
    assert result["applied_rules"][0]["normalizer_version"] == "1.0.0"


def test_diff_always_created():
    """Diff document always created, even for failed normalization."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    diff_store = DiffStore()
    
    raw_payload = json.dumps({"data": "test"}).encode("utf-8")
    hash_val, ptr, size = raw_store.append(raw_payload, raw_format="json")
    
    # No rule registered (normalization will fail)
    ingest_record = {
        "raw_pointer": ptr,
        "source_system": "no_rule_sys",
        "raw_format": "json",
        "event_id": None
    }
    
    canonical, result = normalize_ingest_record(ingest_record, raw_store, registry, diff_store)
    
    # Normalization failed
    assert canonical is None
    
    # But diff_reference still present
    assert "diff_reference" in result
    assert result["diff_reference"].startswith("diff:")
    
    # Diff store has entry
    assert diff_store.count() == 1
