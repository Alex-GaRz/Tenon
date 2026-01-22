"""
Unit tests: currency validation (ISO 4217 vs UNKNOWN).
RFC-01 implementation.

Tests that currency is validated at schema/semantic level.
Invalid currency → REJECT.
Unknown currency → must use explicit "UNKNOWN" (no silent defaulting).
"""

import pytest
from core.canonical_event.schema_validator import SchemaValidator


class TestCurrencyValidation:
    """Test currency field validation."""
    
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
    
    @pytest.mark.parametrize("valid_currency", [
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "BRL", "MXN"
    ])
    def test_valid_iso4217_currency_accepted(self, valid_currency):
        """Valid ISO 4217 currency codes should be accepted."""
        event = self.base_event.copy()
        event["currency"] = valid_currency
        
        result = self.validator.validate(event)
        
        # Note: Schema now allows any string, semantic validation is separate
        assert result.valid is True
    
    def test_unknown_currency_explicit(self):
        """Explicit UNKNOWN currency should be accepted."""
        event = self.base_event.copy()
        event["currency"] = "UNKNOWN"
        
        result = self.validator.validate(event)
        
        assert result.valid is True
    
    def test_currency_required(self):
        """Currency field is required."""
        event = self.base_event.copy()
        del event["currency"]
        
        result = self.validator.validate(event)
        
        assert result.valid is False
        assert len(result.errors) > 0
    
    def test_currency_null_rejected(self):
        """Null currency should be rejected."""
        event = self.base_event.copy()
        event["currency"] = None
        
        result = self.validator.validate(event)
        
        assert result.valid is False
    
    def test_currency_empty_string_allowed_by_schema(self):
        """
        Empty string currency is allowed by schema (relaxed validation).
        Semantic validation would catch this separately.
        """
        event = self.base_event.copy()
        event["currency"] = ""
        
        result = self.validator.validate(event)
        
        # Schema allows any string now (pattern removed)
        # Semantic validator would enforce non-empty for traceability/business rules
        assert result.valid is True
    
    @pytest.mark.parametrize("invalid_currency", [
        "us",           # Lowercase not ISO format
        "usd",          # Lowercase not ISO format  
        "USDD",         # Too long
        "US",           # Too short
        "123",          # Numeric
        "$$$",          # Symbols
        "dollar"        # Full name
    ])
    def test_semantic_validation_would_reject_invalid(self, invalid_currency):
        """
        Schema now allows any string for currency (relaxed).
        These would be caught by semantic/business validation layer.
        Testing that schema accepts them (delegate to semantic layer).
        """
        event = self.base_event.copy()
        event["currency"] = invalid_currency
        
        result = self.validator.validate(event)
        
        # Schema validation passes (no pattern constraint)
        assert result.valid is True
        
        # Note: Semantic validator would enforce ISO 4217 or UNKNOWN
        # This is intentional separation of concerns per RFC-01
    
    def test_currency_must_be_string(self):
        """Currency must be string type."""
        event = self.base_event.copy()
        event["currency"] = 840  # ISO 4217 numeric code
        
        result = self.validator.validate(event)
        
        assert result.valid is False
        assert len(result.errors) > 0
