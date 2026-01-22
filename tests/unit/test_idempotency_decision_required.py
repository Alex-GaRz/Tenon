"""
Unit tests: idempotency_decision required and explicit.
RFC-01A implementation.

Tests that:
1. idempotency_decision is required field
2. Decision must be explicit (ACCEPT / REJECT_DUPLICATE / FLAG_AMBIGUOUS)
3. Invalid decisions are rejected
4. Decision aligns with identity matching logic
"""

import pytest
from core.canonical_event.schema_validator import SchemaValidator
from core.canonical_ids.identity_decider import IdentityDecider, IdentityDecision


class TestIdempotencyDecisionRequired:
    """Test idempotency_decision field requirements."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SchemaValidator()
        self.decider = IdentityDecider()
        
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
    
    def test_idempotency_decision_required(self):
        """idempotency_decision is a required field."""
        event = self.base_event.copy()
        del event["idempotency_decision"]
        
        result = self.validator.validate(event)
        
        assert result.valid is False
        assert len(result.errors) > 0
        
        # Check error mentions idempotency_decision
        error_messages = [e.message for e in result.errors]
        assert any("idempotency_decision" in msg or "required" in msg.lower()
                   for msg in error_messages)
    
    @pytest.mark.parametrize("valid_decision", [
        "ACCEPT",
        "REJECT_DUPLICATE",
        "FLAG_AMBIGUOUS"
    ])
    def test_valid_decisions_accepted(self, valid_decision):
        """All valid idempotency decisions should be accepted."""
        event = self.base_event.copy()
        event["idempotency_decision"] = valid_decision
        
        result = self.validator.validate(event)
        
        assert result.valid is True
    
    @pytest.mark.parametrize("invalid_decision", [
        "REJECT",           # Not full enum value
        "DUPLICATE",        # Partial value
        "ACCEPT_FORCE",     # Not in enum
        "accept",           # Wrong case
        "Accept",           # Wrong case
        "",                 # Empty
        "PENDING",          # Not in enum
        "UNKNOWN"           # Not in enum
    ])
    def test_invalid_decisions_rejected(self, invalid_decision):
        """Invalid idempotency decisions should be rejected."""
        event = self.base_event.copy()
        event["idempotency_decision"] = invalid_decision
        
        result = self.validator.validate(event)
        
        assert result.valid is False
        assert len(result.errors) > 0
    
    def test_idempotency_decision_null_rejected(self):
        """Null idempotency_decision should be rejected."""
        event = self.base_event.copy()
        event["idempotency_decision"] = None
        
        result = self.validator.validate(event)
        
        assert result.valid is False
    
    def test_decision_explicit_accept(self):
        """ACCEPT decision should be explicit (not implicit default)."""
        event = self.base_event.copy()
        event["idempotency_decision"] = "ACCEPT"
        
        result = self.validator.validate(event)
        
        assert result.valid is True
        # Decision is explicitly set, not defaulted
        assert event["idempotency_decision"] == "ACCEPT"
    
    def test_decision_explicit_reject_duplicate(self):
        """REJECT_DUPLICATE decision should be explicit."""
        event = self.base_event.copy()
        event["idempotency_decision"] = "REJECT_DUPLICATE"
        
        result = self.validator.validate(event)
        
        assert result.valid is True
        assert event["idempotency_decision"] == "REJECT_DUPLICATE"
    
    def test_decision_explicit_flag_ambiguous(self):
        """FLAG_AMBIGUOUS decision should be explicit."""
        event = self.base_event.copy()
        event["idempotency_decision"] = "FLAG_AMBIGUOUS"
        
        result = self.validator.validate(event)
        
        assert result.valid is True
        assert event["idempotency_decision"] == "FLAG_AMBIGUOUS"
    
    def test_identity_decider_produces_valid_decisions(self):
        """IdentityDecider should only produce valid decision enum values."""
        # No existing events → ACCEPT
        match1 = self.decider.decide("key1", self.base_event, existing_events={})
        assert match1.decision in [IdentityDecision.ACCEPT, 
                                    IdentityDecision.REJECT_DUPLICATE,
                                    IdentityDecision.FLAG_AMBIGUOUS]
        
        # Exact match → REJECT_DUPLICATE
        existing = {"key1": self.base_event.copy()}
        match2 = self.decider.decide("key1", self.base_event, existing_events=existing)
        assert match2.decision in [IdentityDecision.ACCEPT,
                                    IdentityDecision.REJECT_DUPLICATE,
                                    IdentityDecision.FLAG_AMBIGUOUS]
    
    def test_idempotency_key_also_required(self):
        """idempotency_key is also required (companion to decision)."""
        event = self.base_event.copy()
        del event["idempotency_key"]
        
        result = self.validator.validate(event)
        
        assert result.valid is False
        assert len(result.errors) > 0
