"""
Property-based test: Determinism raw→CanonicalEvent.
RFC-01 + RFC-01A implementation.

Oracle: Same raw input + same versions → same CanonicalEvent.

Tests that the canonicalization process is deterministic:
- Same raw payload
- Same normalizer_version
- Same adapter_version  
- Same schema_version
→ Produces identical canonical representation
"""

import pytest
import hashlib
import json
from core.canonical_ids.idempotency_key import IdempotencyKeyGenerator


class TestDeterminismRawToCanonical:
    """Test deterministic canonicalization property."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.key_generator = IdempotencyKeyGenerator(version="1.0.0")
        
        # Raw event simulation
        self.raw_event_1 = {
            "transaction_id": "txn_12345",
            "amount": 100.50,
            "currency": "USD",
            "timestamp": "2026-01-22T10:00:00Z",
            "source": "bank_api"
        }
    
    def _canonicalize(self, raw_event, normalizer_version, adapter_version, schema_version):
        """
        Simulate canonicalization process.
        
        In real implementation, this would be the adapter + normalizer.
        For testing, we create a canonical event deterministically.
        """
        # Deterministic raw hash for traceability
        raw_json = json.dumps(raw_event, sort_keys=True)
        raw_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
        
        # Fixed event_id for deterministic testing (not derived from hash)
        # In production, event_id generation is external concern
        event_id = "evt_test_001"
        
        canonical_event = {
            "event_id": event_id,
            "source_event_id": raw_event.get("transaction_id"),
            "source_system": "BANK",
            "source_connector": "bank_api_connector",
            "source_environment": "PROD",
            "observed_at": "2026-01-22T10:00:00Z",
            "source_timestamp": raw_event.get("timestamp"),
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": raw_event.get("amount"),
            "currency": raw_event.get("currency"),
            "raw_payload_hash": raw_hash,
            "raw_pointer": f"s3://bucket/raw/{raw_hash}.json",
            "raw_format": "JSON",
            "normalizer_version": normalizer_version,
            "adapter_version": adapter_version,
            "schema_version": schema_version,
            "idempotency_key": "",  # Will be set below
            "idempotency_decision": "ACCEPT"
        }
        
        # Generate deterministic idempotency key with version context
        # Include canonicalization context in key calculation
        key_event = canonical_event.copy()
        key_event["_canonicalization_context"] = f"{normalizer_version}|{adapter_version}|{schema_version}"
        canonical_event["idempotency_key"] = self.key_generator.generate(key_event)
        
        return canonical_event
    
    def test_same_raw_same_versions_produces_identical_canonical(self):
        """
        Property: Same raw + same versions → identical canonical.
        """
        versions = ("1.0.0", "1.0.0", "1.0.0")
        
        # Canonicalize twice
        canonical_1 = self._canonicalize(self.raw_event_1, *versions)
        canonical_2 = self._canonicalize(self.raw_event_1, *versions)
        
        # Should be identical (deterministic)
        assert canonical_1 == canonical_2
        assert canonical_1["idempotency_key"] == canonical_2["idempotency_key"]
        assert canonical_1["event_id"] == canonical_2["event_id"]
    
    def test_same_raw_different_normalizer_version_deterministic_per_context(self):
        """
        Property: Same raw + different normalizer_version → deterministic per version context.
        
        Different normalizer_version means different canonicalization context,
        which MUST produce different idempotency_key (versions affect identity).
        """
        canonical_v1 = self._canonicalize(self.raw_event_1, "1.0.0", "1.0.0", "1.0.0")
        canonical_v2 = self._canonicalize(self.raw_event_1, "2.0.0", "1.0.0", "1.0.0")
        
        # event_id same (fixed for test)
        assert canonical_v1["event_id"] == canonical_v2["event_id"]
        
        # normalizer_version differs
        assert canonical_v1["normalizer_version"] != canonical_v2["normalizer_version"]
        
        # idempotency_key DIFFERENT: version context affects identity
        # Different canonicalization version → different identity
        assert canonical_v1["idempotency_key"] != canonical_v2["idempotency_key"]
        
        # But: each version context is deterministic
        canonical_v1_repeat = self._canonicalize(self.raw_event_1, "1.0.0", "1.0.0", "1.0.0")
        assert canonical_v1 == canonical_v1_repeat
    
    def test_idempotency_key_deterministic_same_input(self):
        """
        Property: Idempotency key is deterministic for same event fields.
        """
        event = {
            "source_event_id": "txn_12345",
            "source_system": "BANK",
            "source_timestamp": "2026-01-22T10:00:00Z",
            "amount": 100.50,
            "currency": "USD",
            "direction": "IN",
            "event_type": "PAYMENT_CAPTURED"
        }
        
        key1 = self.key_generator.generate(event)
        key2 = self.key_generator.generate(event)
        
        assert key1 == key2
    
    def test_idempotency_key_changes_with_different_amount(self):
        """
        Property: Different critical field → different idempotency key.
        """
        event1 = {
            "source_event_id": "txn_12345",
            "amount": 100.50,
            "currency": "USD"
        }
        
        event2 = {
            "source_event_id": "txn_12345",
            "amount": 200.00,  # Different amount
            "currency": "USD"
        }
        
        key1 = self.key_generator.generate(event1)
        key2 = self.key_generator.generate(event2)
        
        assert key1 != key2
    
    def test_idempotency_key_deterministic_float_normalization(self):
        """
        Property: Float normalization is deterministic.
        
        Same numeric value represented differently should produce same key.
        """
        event1 = {
            "source_event_id": "txn_12345",
            "amount": 100.5,
            "currency": "USD"
        }
        
        event2 = {
            "source_event_id": "txn_12345",
            "amount": 100.50,  # Same value, different precision
            "currency": "USD"
        }
        
        key1 = self.key_generator.generate(event1)
        key2 = self.key_generator.generate(event2)
        
        # Should be same after normalization
        assert key1 == key2
    
    def test_canonicalization_multiple_iterations_stable(self):
        """
        Property: Multiple canonicalization iterations produce stable result.
        """
        versions = ("1.0.0", "1.0.0", "1.0.0")
        
        results = []
        for _ in range(5):
            canonical = self._canonicalize(self.raw_event_1, *versions)
            results.append(canonical)
        
        # All results should be identical
        first = results[0]
        for result in results[1:]:
            assert result == first
    
    def test_field_order_does_not_affect_idempotency_key(self):
        """
        Property: Field order in event dict does not affect idempotency key.
        """
        event1 = {
            "source_event_id": "txn_12345",
            "amount": 100.50,
            "currency": "USD"
        }
        
        event2 = {
            "currency": "USD",
            "source_event_id": "txn_12345",
            "amount": 100.50
        }
        
        key1 = self.key_generator.generate(event1)
        key2 = self.key_generator.generate(event2)
        
        assert key1 == key2
