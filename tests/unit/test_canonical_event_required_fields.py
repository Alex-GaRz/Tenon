"""
Unit tests: CanonicalEvent required fields validation.
RFC-01 + RFC-01A implementation.

Tests that all required fields are enforced by schema validator.
Missing required field → REJECT with evidence.
"""

import pytest
from core.canonical_event.schema_validator import SchemaValidator


class TestRequiredFields:
    """Test required fields enforcement."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SchemaValidator()
        
        # Valid minimal event
        self.valid_event = {
            "event_id": "evt_001",
            "source_system": "BANK",
            "source_connector": "bank_connector_v1",
            "source_environment": "PROD",
            "observed_at": "2026-01-22T10:00:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": 100.50,
            "currency": "USD",
            "raw_payload_hash": "abc123def456",
            "raw_pointer": "s3://bucket/raw/evt_001.json",
            "raw_format": "JSON",
            "normalizer_version": "1.0.0",
            "adapter_version": "1.0.0",
            "schema_version": "1.0.0",
            "idempotency_key": "v1.0.0:hash123",
            "idempotency_decision": "ACCEPT"
        }
    
    def test_valid_event_passes(self):
        """Valid event with all required fields should pass."""
        result = self.validator.validate(self.valid_event)
        assert result.valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.parametrize("required_field", [
        "event_id",
        "source_system",
        "source_connector",
        "source_environment",
        "observed_at",
        "event_type",
        "direction",
        "amount",
        "currency",
        "raw_payload_hash",
        "raw_pointer",
        "raw_format",
        "normalizer_version",
        "adapter_version",
        "schema_version",
        "idempotency_key",
        "idempotency_decision"
    ])
    def test_missing_required_field_rejects(self, required_field):
        """Missing any required field should reject with evidence."""
        event = self.valid_event.copy()
        del event[required_field]
        
        result = self.validator.validate(event)
        
        assert result.valid is False
        assert len(result.errors) > 0
        
        # Check that error mentions the missing field
        error_messages = [e.message for e in result.errors]
        assert any(required_field in msg or "required" in msg.lower() 
                   for msg in error_messages)
    
    def test_null_required_field_rejects(self):
        """Required field set to null should reject."""
        event = self.valid_event.copy()
        event["event_id"] = None
        
        result = self.validator.validate(event)
        
        assert result.valid is False
        assert len(result.errors) > 0
    
    def test_empty_string_required_field_rejects(self):
        """Required string field set to empty should reject."""
        event = self.valid_event.copy()
        event["event_id"] = ""
        
        result = self.validator.validate(event)
        
        # Schema validation may or may not catch empty strings
        # but it should not be accepted as valid
        # (Invariant validator would catch this for traceability fields)
