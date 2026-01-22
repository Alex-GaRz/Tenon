"""
Adversarial test: external_reference collision does NOT merge events.
RFC-01A implementation.

Oracle: Same external_reference from different sources → separate events.

Tests that:
1. external_reference alone does NOT determine identity
2. Collisions from different sources → both persisted separately
3. Partial match with same external_reference → FLAG_AMBIGUOUS
4. NO silent merging/fusion of distinct events
"""

import pytest
from core.canonical_ids.idempotency_key import IdempotencyKeyGenerator
from core.canonical_ids.identity_decider import IdentityDecider, IdentityDecision


class TestExternalReferenceCollision:
    """Test that external_reference collisions don't merge events."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.key_generator = IdempotencyKeyGenerator(version="1.0.0")
        self.decider = IdentityDecider(version="1.0.0")
    
    def test_same_external_ref_different_sources_separate_events(self):
        """
        Adversarial: Same external_reference from different sources → separate events.
        """
        # Event from BANK
        event_bank = {
            "event_id": "evt_001",
            "external_reference": "REF12345",  # Same reference
            "source_system": "BANK",
            "source_event_id": "bank_txn_001",
            "source_connector": "bank_connector",
            "source_environment": "PROD",
            "observed_at": "2026-01-22T10:00:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": 100.00,
            "currency": "USD"
        }
        
        # Event from PSP (different source, same external_reference)
        event_psp = {
            "event_id": "evt_002",
            "external_reference": "REF12345",  # Same reference!
            "source_system": "PSP",
            "source_event_id": "psp_txn_002",
            "source_connector": "psp_connector",
            "source_environment": "PROD",
            "observed_at": "2026-01-22T10:05:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": 100.00,
            "currency": "USD"
        }
        
        # Generate keys
        key_bank = self.key_generator.generate(event_bank)
        key_psp = self.key_generator.generate(event_psp)
        
        # Keys MUST be different (different source_system, source_event_id)
        assert key_bank != key_psp, "Different sources should produce different idempotency keys"
        
        # Both should be ACCEPT (different events)
        existing_events = {}
        
        match_bank = self.decider.decide(key_bank, event_bank, existing_events)
        assert match_bank.decision == IdentityDecision.ACCEPT
        
        existing_events[key_bank] = event_bank
        
        match_psp = self.decider.decide(key_psp, event_psp, existing_events)
        assert match_psp.decision == IdentityDecision.ACCEPT
    
    def test_same_external_ref_same_source_different_amount_ambiguous(self):
        """
        Adversarial: Same external_reference + source but different amount → FLAG_AMBIGUOUS.
        """
        event1 = {
            "event_id": "evt_001",
            "external_reference": "INV9999",
            "source_system": "ERP",
            "source_event_id": "erp_001",
            "source_connector": "erp_connector",
            "source_environment": "PROD",
            "observed_at": "2026-01-22T10:00:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": 500.00,
            "currency": "USD"
        }
        
        event2 = {
            "event_id": "evt_002",
            "external_reference": "INV9999",  # Same
            "source_system": "ERP",           # Same
            "source_event_id": "erp_001",     # Same
            "source_connector": "erp_connector",
            "source_environment": "PROD",
            "observed_at": "2026-01-22T10:01:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": 1000.00,                # DIFFERENT
            "currency": "USD"
        }
        
        key1 = self.key_generator.generate(event1)
        key2 = self.key_generator.generate(event2)
        
        # Keys might be same (same source_event_id) or different (different amount)
        # Depending on key derivation priority
        
        # If keys are same → ambiguous match
        if key1 == key2:
            existing_events = {key1: event1}
            match = self.decider.decide(key2, event2, existing_events)
            
            assert match.decision == IdentityDecision.FLAG_AMBIGUOUS
            assert "amount" in match.conflicting_fields
        else:
            # Different keys → both accepted (different events)
            existing_events = {}
            match1 = self.decider.decide(key1, event1, existing_events)
            assert match1.decision == IdentityDecision.ACCEPT
            
            existing_events[key1] = event1
            match2 = self.decider.decide(key2, event2, existing_events)
            assert match2.decision == IdentityDecision.ACCEPT
    
    def test_collision_does_not_overwrite_first_event(self):
        """
        Adversarial: Collision should NOT overwrite/merge with first event.
        """
        event1 = {
            "event_id": "evt_001",
            "external_reference": "COLLISION_REF",
            "source_system": "BANK",
            "source_event_id": "txn_001",
            "observed_at": "2026-01-22T10:00:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": 100.00,
            "currency": "USD"
        }
        
        event2 = {
            "event_id": "evt_002",
            "external_reference": "COLLISION_REF",  # Same
            "source_system": "BANK",                # Same
            "source_event_id": "txn_002",           # Different
            "observed_at": "2026-01-22T11:00:00Z",
            "event_type": "REFUND_SETTLED",         # Different type
            "direction": "OUT",                     # Different direction
            "amount": 50.00,                        # Different amount
            "currency": "USD"
        }
        
        key1 = self.key_generator.generate(event1)
        key2 = self.key_generator.generate(event2)
        
        # Different source_event_id → different keys
        assert key1 != key2
        
        existing_events = {key1: event1}
        original_event = existing_events[key1].copy()
        
        # Process second event
        match = self.decider.decide(key2, event2, existing_events)
        
        # First event should remain unchanged
        assert existing_events[key1] == original_event
        assert existing_events[key1]["event_id"] == "evt_001"
        assert existing_events[key1]["amount"] == 100.00
    
    def test_external_ref_not_primary_identity_field(self):
        """
        Adversarial: external_reference alone does NOT determine identity.
        
        source_event_id has higher priority in idempotency key.
        """
        # Two events: same external_ref, different source_event_id
        event1 = {
            "external_reference": "SAME_REF",
            "source_event_id": "SOURCE_A",  # Different
            "source_system": "BANK",
            "amount": 100.00,
            "currency": "USD"
        }
        
        event2 = {
            "external_reference": "SAME_REF",
            "source_event_id": "SOURCE_B",  # Different
            "source_system": "BANK",
            "amount": 100.00,
            "currency": "USD"
        }
        
        key1 = self.key_generator.generate(event1)
        key2 = self.key_generator.generate(event2)
        
        # Keys must be different (source_event_id is primary)
        assert key1 != key2
    
    def test_no_silent_merge_on_ambiguous_external_ref(self):
        """
        Adversarial: Ambiguous external_reference → FLAG_AMBIGUOUS, not silent merge.
        """
        # Scenario: Same external_ref + partial match
        base_event = {
            "event_id": "evt_001",
            "external_reference": "AMB_REF",
            "source_event_id": "txn_base",
            "source_system": "MARKETPLACE",
            "observed_at": "2026-01-22T10:00:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": 75.00,
            "currency": "USD"
        }
        
        ambiguous_event = {
            "event_id": "evt_002",
            "external_reference": "AMB_REF",     # Same
            "source_event_id": "txn_base",       # Same (same key)
            "source_system": "MARKETPLACE",      # Same
            "observed_at": "2026-01-22T10:00:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "OUT",                  # DIFFERENT
            "amount": 75.00,
            "currency": "EUR"                    # DIFFERENT
        }
        
        key_base = self.key_generator.generate(base_event)
        key_amb = self.key_generator.generate(ambiguous_event)
        
        existing_events = {key_base: base_event}
        
        match = self.decider.decide(key_amb, ambiguous_event, existing_events)
        
        # Should flag as ambiguous (not merge, not accept)
        assert match.decision == IdentityDecision.FLAG_AMBIGUOUS
        assert len(match.conflicting_fields) > 0
    
    def test_out_of_order_with_external_ref_no_merge(self):
        """
        Adversarial: Out-of-order events with same external_ref → no merge.
        """
        # Event arrives later but refers to earlier external_reference
        early_event = {
            "event_id": "evt_early",
            "external_reference": "ORDER_123",
            "source_event_id": "early_txn",
            "source_timestamp": "2026-01-22T09:00:00Z",
            "observed_at": "2026-01-22T10:00:00Z",
            "amount": 200.00
        }
        
        late_event = {
            "event_id": "evt_late",
            "external_reference": "ORDER_123",  # Same reference
            "source_event_id": "late_txn",      # Different source event
            "source_timestamp": "2026-01-22T11:00:00Z",
            "observed_at": "2026-01-22T09:30:00Z",  # Observed earlier
            "amount": 200.00
        }
        
        key_early = self.key_generator.generate(early_event)
        key_late = self.key_generator.generate(late_event)
        
        # Different source_event_id → different keys
        assert key_early != key_late
        
        # Both should be accepted as separate events
        existing_events = {}
        
        match_early = self.decider.decide(key_early, early_event, existing_events)
        assert match_early.decision == IdentityDecision.ACCEPT
        
        existing_events[key_early] = early_event
        
        match_late = self.decider.decide(key_late, late_event, existing_events)
        assert match_late.decision == IdentityDecision.ACCEPT
