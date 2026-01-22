"""
Unit tests: event_type enum closed validation.
RFC-01 implementation.

Tests that event_type is restricted to closed enum.
Invalid event_type → REJECT with evidence.
"""

import pytest
from core.canonical_event.schema_validator import SchemaValidator


class TestEventTypeEnum:
    """Test event_type closed enum enforcement."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SchemaValidator()
        
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
        
        # Valid event types from RFC-01
        self.valid_event_types = [
            "PAYMENT_INITIATED",
            "PAYMENT_AUTHORIZED",
            "PAYMENT_CAPTURED",
            "PAYMENT_SETTLED",
            "PAYOUT_INITIATED",
            "PAYOUT_SETTLED",
            "REFUND_INITIATED",
            "REFUND_SETTLED",
            "CHARGEBACK_OPENED",
            "CHARGEBACK_WON",
            "CHARGEBACK_LOST",
            "FEE_ASSESSED",
            "ADJUSTMENT_POSTED",
            "REVERSAL_POSTED",
            "BALANCE_SNAPSHOT",
            "UNKNOWN"
        ]
    
    @pytest.mark.parametrize("valid_type", [
        "PAYMENT_INITIATED",
        "PAYMENT_AUTHORIZED",
        "PAYMENT_CAPTURED",
        "PAYMENT_SETTLED",
        "PAYOUT_INITIATED",
        "PAYOUT_SETTLED",
        "REFUND_INITIATED",
        "REFUND_SETTLED",
        "CHARGEBACK_OPENED",
        "CHARGEBACK_WON",
        "CHARGEBACK_LOST",
        "FEE_ASSESSED",
        "ADJUSTMENT_POSTED",
        "REVERSAL_POSTED",
        "BALANCE_SNAPSHOT",
        "UNKNOWN"
    ])
    def test_valid_event_type_accepted(self, valid_type):
        """All valid event types from RFC-01 enum should be accepted."""
        event = self.base_event.copy()
        event["event_type"] = valid_type
        
        result = self.validator.validate(event)
        
        assert result.valid is True, f"Event type {valid_type} should be accepted"
    
    @pytest.mark.parametrize("invalid_type", [
        "PAYMENT_RECEIVED",  # Old enum value
        "PAYMENT_SENT",      # Old enum value
        "TRANSACTION",       # Generic term
        "TRANSFER",          # Not in enum
        "payment_captured",  # Wrong case
        "Payment_Captured",  # Wrong case
        "",                  # Empty
        "CUSTOM_TYPE",       # Ad-hoc type
        "INVOICE_CREATED"    # Not in enum
    ])
    def test_invalid_event_type_rejected(self, invalid_type):
        """Event types not in RFC-01 enum should be rejected."""
        event = self.base_event.copy()
        event["event_type"] = invalid_type
        
        result = self.validator.validate(event)
        
        assert result.valid is False
        assert len(result.errors) > 0
        
        # Check error mentions event_type
        error_fields = [e.field for e in result.errors]
        assert any("event_type" in field for field in error_fields)
    
    def test_event_type_null_rejected(self):
        """Null event_type should be rejected."""
        event = self.base_event.copy()
        event["event_type"] = None
        
        result = self.validator.validate(event)
        
        assert result.valid is False
    
    def test_event_type_missing_rejected(self):
        """Missing event_type should be rejected."""
        event = self.base_event.copy()
        del event["event_type"]
        
        result = self.validator.validate(event)
        
        assert result.valid is False
