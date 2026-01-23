"""
RFC-03 Property Tests: Normalization determinism invariants.

Property-based tests for:
- Determinism: N executions → same canonical_event
- Stable diff content (though diff_reference may vary if UUID-based)
- No side effects on raw payload
"""

import json

from core.ingest.v1.raw_payload_store import RawPayloadStore
from core.normalization.v1.rule_registry import RuleRegistry
from core.normalization.v1.diff_store import DiffStore
from core.normalization.v1.normalization_engine import normalize_ingest_record


def test_property_normalization_deterministic():
    """Property: Same input → same canonical_event (deterministic)."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    
    raw_payload = json.dumps({"amount": 1000, "currency": "EUR"}).encode("utf-8")
    hash_val, ptr, size = raw_store.append(raw_payload, raw_format="json")
    
    rule = {
        "rule_id": "rule_det",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "bank_det",
            "raw_format": "json",
            "schema_hint": "default"
        },
        "mapping": [
            {"raw_path": "amount", "canonical_path": "amount"},
            {"raw_path": "currency", "canonical_path": "currency"}
        ],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule)
    
    ingest_record = {
        "raw_pointer": ptr,
        "source_system": "bank_det",
        "raw_format": "json",
        "event_id": "evt_det"
    }
    
    # Run normalization N times
    results = []
    for _ in range(10):
        diff_store = DiffStore()  # Fresh store each time (diff_reference may vary)
        canonical, result = normalize_ingest_record(ingest_record, raw_store, registry, diff_store)
        results.append(canonical)
    
    # All canonical events identical
    for i in range(1, len(results)):
        assert results[i] == results[0]


def test_property_raw_payload_immutable():
    """Property: Normalization does not modify raw payload."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    diff_store = DiffStore()
    
    raw_payload = json.dumps({"immutable": "test"}).encode("utf-8")
    hash_before = raw_payload
    
    hash_val, ptr, size = raw_store.append(raw_payload, raw_format="json")
    
    rule = {
        "rule_id": "rule_immut",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "bank_immut",
            "raw_format": "json",
            "schema_hint": "default"
        },
        "mapping": [{"raw_path": "immutable", "canonical_path": "field"}],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule)
    
    ingest_record = {
        "raw_pointer": ptr,
        "source_system": "bank_immut",
        "raw_format": "json",
        "event_id": "evt_immut"
    }
    
    # Normalize
    canonical, result = normalize_ingest_record(ingest_record, raw_store, registry, diff_store)
    
    # Raw payload unchanged
    raw_after = raw_store.get(ptr)
    assert raw_after == hash_before


def test_property_diff_content_stable():
    """Property: Same normalization → same diff content (structure)."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()
    
    raw_payload = json.dumps({"stable": "diff"}).encode("utf-8")
    hash_val, ptr, size = raw_store.append(raw_payload, raw_format="json")
    
    rule = {
        "rule_id": "rule_stable",
        "rule_version": "1.0.0",
        "normalizer_version": "1.0.0",
        "input_signature": {
            "source_system": "bank_stable",
            "raw_format": "json",
            "schema_hint": "default"
        },
        "mapping": [{"raw_path": "stable", "canonical_path": "stable_field"}],
        "lossy_fields": [],
        "warnings": []
    }
    
    registry.register(rule)
    
    ingest_record = {
        "raw_pointer": ptr,
        "source_system": "bank_stable",
        "raw_format": "json",
        "event_id": "evt_stable"
    }
    
    # Run normalization multiple times
    diff_contents = []
    for _ in range(5):
        diff_store = DiffStore()
        canonical, result = normalize_ingest_record(ingest_record, raw_store, registry, diff_store)
        
        # Retrieve diff content
        diff_doc = diff_store.get(result["diff_reference"])
        
        # Exclude diff_reference (may vary due to UUID), compare structure
        diff_contents.append({
            "raw_pointer": diff_doc["raw_pointer"],
            "applied_rule": diff_doc["applied_rule"],
            "mappings_applied": diff_doc["mappings_applied"]
        })
    
    # All diff contents identical
    for i in range(1, len(diff_contents)):
        assert diff_contents[i] == diff_contents[0]


def test_property_no_rule_always_fails_consistently():
    """Property: No rule → always fails with same warnings."""
    raw_store = RawPayloadStore()
    registry = RuleRegistry()  # Empty registry
    
    raw_payload = json.dumps({"orphan": "data"}).encode("utf-8")
    hash_val, ptr, size = raw_store.append(raw_payload, raw_format="json")
    
    ingest_record = {
        "raw_pointer": ptr,
        "source_system": "no_rule",
        "raw_format": "json",
        "event_id": None
    }
    
    # Run multiple times
    results = []
    for _ in range(5):
        diff_store = DiffStore()
        canonical, result = normalize_ingest_record(ingest_record, raw_store, registry, diff_store)
        results.append((canonical, result["warnings"]))
    
    # All fail consistently
    for canonical, warnings in results:
        assert canonical is None
        assert len(warnings) > 0
        assert any("No normalization rule" in w for w in warnings)
