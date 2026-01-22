"""
Unit tests: Event immutability.
RFC-01 implementation.

Tests that:
1. Events cannot be mutated once created
2. event_id cannot be reused
3. No mutation hint fields allowed

Immutability is enforced via:
- Append-only storage (external)
- Invariant validator rejecting mutation hints
- Uniqueness enforcement of event_id
"""

import pytest
from core.canonical_event.invariant_validator import InvariantValidator


class TestEventImmutability:
    """Test event immutability constraints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Event store to track uniqueness
        self.event_store = set()
        self.validator = InvariantValidator(event_store=self.event_store)
        
        # Valid base event
        self.base_event = {
            "event_id": "evt_001",
            "source_system": "BANK",
            "source_connector": "bank_connector_v1",
            "source_environment": "PROD",
            "observed_at": "2026-01-22T10:00:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": 100.50,
            "currency": "USD",
            "raw_payload_hash": "abc123",
            "raw_pointer": "s3://bucket/raw/evt_001.json",
            "raw_format": "JSON",
            "normalizer_version": "1.0.0",
            "adapter_version": "1.0.0",
            "schema_version": "1.0.0",
            "idempotency_key": "v1.0.0:hash123",
            "idempotency_decision": "ACCEPT"
        }
    
    def test_new_event_id_accepted(self):
        """New unique event_id should be accepted."""
        event = self.base_event.copy()
        
        result = self.validator.validate(event)
        
        assert result.valid is True
        assert len(result.violations) == 0
    
    def test_duplicate_event_id_rejected(self):
        """Reusing an event_id should be rejected (uniqueness violation)."""
        event = self.base_event.copy()
        
        # First event accepted
        result1 = self.validator.validate(event)
        assert result1.valid is True
        
        # Add to store
        self.event_store.add(event["event_id"])
        
        # Same event_id rejected
        result2 = self.validator.validate(event)
        
        assert result2.valid is False
        assert len(result2.violations) > 0
        
        # Check violation is UNIQUENESS
        assert any(v.invariant == "UNIQUENESS" for v in result2.violations)
    
    def test_event_id_immutable_simulation(self):
        """
        Simulate immutability: once event_id is used, cannot be reused.
        This is the append-only guarantee.
        """
        event1 = self.base_event.copy()
        event1["event_id"] = "evt_001"
        
        # Create event
        result1 = self.validator.validate(event1)
        assert result1.valid is True
        self.event_store.add(event1["event_id"])
        
        # Try to "update" by reusing same event_id
        event2 = self.base_event.copy()
        event2["event_id"] = "evt_001"
        event2["amount"] = 200.00  # Different amount
        
        result2 = self.validator.validate(event2)
        
        # Should be rejected (event_id already exists)
        assert result2.valid is False
        assert any(v.invariant == "UNIQUENESS" for v in result2.violations)
    
    def test_different_event_ids_accepted(self):
        """Different event_ids should both be accepted."""
        event1 = self.base_event.copy()
        event1["event_id"] = "evt_001"
        
        event2 = self.base_event.copy()
        event2["event_id"] = "evt_002"
        
        result1 = self.validator.validate(event1)
        assert result1.valid is True
        self.event_store.add(event1["event_id"])
        
        result2 = self.validator.validate(event2)
        assert result2.valid is True
    
    def test_no_mutation_without_store(self):
        """
        Without event_store, uniqueness cannot be enforced.
        This tests the validator gracefully handles missing store.
        """
        validator_no_store = InvariantValidator(event_store=None)
        event = self.base_event.copy()
        
        result = validator_no_store.validate(event)
        
        # Should pass (uniqueness check skipped)
        assert result.valid is True
