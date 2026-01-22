"""
Property-based test: Strong idempotency (N retries).
RFC-01A implementation.

Oracle: N attempts of same event → 1 ACCEPT + (N-1) REJECT_DUPLICATE.

Tests that idempotency guarantees:
- First occurrence: ACCEPT
- Subsequent identical occurrences: REJECT_DUPLICATE
- Conservative: ambiguous cases → FLAG_AMBIGUOUS (not ACCEPT)
"""

import pytest
from core.canonical_ids.idempotency_key import IdempotencyKeyGenerator
from core.canonical_ids.identity_decider import IdentityDecider, IdentityDecision


class TestStrongIdempotency:
    """Test strong idempotency property for retries."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.key_generator = IdempotencyKeyGenerator(version="1.0.0")
        self.decider = IdentityDecider(version="1.0.0")
        
        # Base event
        self.event = {
            "event_id": "evt_001",
            "source_event_id": "txn_12345",
            "source_system": "BANK",
            "source_connector": "bank_connector",
            "source_environment": "PROD",
            "observed_at": "2026-01-22T10:00:00Z",
            "source_timestamp": "2026-01-22T10:00:00Z",
            "event_type": "PAYMENT_CAPTURED",
            "direction": "IN",
            "amount": 100.50,
            "currency": "USD",
            "raw_payload_hash": "abc123",
            "raw_pointer": "s3://bucket/raw/evt_001.json",
            "raw_format": "JSON"
        }
    
    def test_single_event_accepted(self):
        """Property: First occurrence → ACCEPT."""
        idempotency_key = self.key_generator.generate(self.event)
        existing_events = {}
        
        match = self.decider.decide(idempotency_key, self.event, existing_events)
        
        assert match.decision == IdentityDecision.ACCEPT
        assert match.match_score == 0.0
    
    def test_exact_duplicate_rejected(self):
        """Property: Exact duplicate → REJECT_DUPLICATE."""
        idempotency_key = self.key_generator.generate(self.event)
        
        # First event accepted
        existing_events = {idempotency_key: self.event}
        
        # Second identical event rejected
        match = self.decider.decide(idempotency_key, self.event, existing_events)
        
        assert match.decision == IdentityDecision.REJECT_DUPLICATE
        assert match.match_score == 1.0
        assert match.matched_event_id == self.event["event_id"]
    
    def test_n_retries_one_accept_n_minus_one_reject(self):
        """
        Property: N retries → 1 ACCEPT + (N-1) REJECT_DUPLICATE.
        """
        N = 10
        idempotency_key = self.key_generator.generate(self.event)
        
        decisions = []
        existing_events = {}
        
        for i in range(N):
            match = self.decider.decide(idempotency_key, self.event, existing_events)
            decisions.append(match.decision)
            
            # After first ACCEPT, add to existing
            if match.decision == IdentityDecision.ACCEPT:
                existing_events[idempotency_key] = self.event.copy()
        
        # Count decisions
        accepts = sum(1 for d in decisions if d == IdentityDecision.ACCEPT)
        rejects = sum(1 for d in decisions if d == IdentityDecision.REJECT_DUPLICATE)
        
        assert accepts == 1, f"Expected 1 ACCEPT, got {accepts}"
        assert rejects == N - 1, f"Expected {N-1} REJECT_DUPLICATE, got {rejects}"
    
    def test_partial_match_flagged_ambiguous(self):
        """
        Property: Partial match (same key, different fields) → FLAG_AMBIGUOUS.
        """
        idempotency_key = self.key_generator.generate(self.event)
        
        # Existing event
        existing_events = {idempotency_key: self.event.copy()}
        
        # New event with same key but different amount
        conflicting_event = self.event.copy()
        conflicting_event["event_id"] = "evt_002"
        conflicting_event["amount"] = 200.00  # Different
        
        match = self.decider.decide(idempotency_key, conflicting_event, existing_events)
        
        assert match.decision == IdentityDecision.FLAG_AMBIGUOUS
        assert match.matched_event_id == self.event["event_id"]
        assert "amount" in match.conflicting_fields
    
    def test_conservative_ambiguity_no_silent_accept(self):
        """
        Property: Conservative strategy - ambiguity → FLAG_AMBIGUOUS (never silent ACCEPT).
        """
        idempotency_key = self.key_generator.generate(self.event)
        existing_events = {idempotency_key: self.event.copy()}
        
        # Multiple conflicting fields
        conflicting_event = self.event.copy()
        conflicting_event["event_id"] = "evt_003"
        conflicting_event["amount"] = 999.99
        conflicting_event["currency"] = "EUR"
        conflicting_event["direction"] = "OUT"
        
        match = self.decider.decide(idempotency_key, conflicting_event, existing_events)
        
        # Conservative: conflicts → FLAG_AMBIGUOUS (not ACCEPT)
        assert match.decision == IdentityDecision.FLAG_AMBIGUOUS
        assert len(match.conflicting_fields) > 0
    
    def test_different_key_both_accepted(self):
        """Property: Different idempotency keys → both ACCEPT."""
        event1 = self.event.copy()
        event1["source_event_id"] = "txn_001"
        
        event2 = self.event.copy()
        event2["source_event_id"] = "txn_002"
        event2["event_id"] = "evt_002"
        
        key1 = self.key_generator.generate(event1)
        key2 = self.key_generator.generate(event2)
        
        assert key1 != key2
        
        existing_events = {}
        
        match1 = self.decider.decide(key1, event1, existing_events)
        assert match1.decision == IdentityDecision.ACCEPT
        
        existing_events[key1] = event1
        
        match2 = self.decider.decide(key2, event2, existing_events)
        assert match2.decision == IdentityDecision.ACCEPT
    
    def test_idempotency_across_restarts(self):
        """
        Property: Idempotency persists across "restarts" (existing_events map).
        """
        idempotency_key = self.key_generator.generate(self.event)
        
        # First "session" - accept event
        existing_events_session1 = {}
        match1 = self.decider.decide(idempotency_key, self.event, existing_events_session1)
        assert match1.decision == IdentityDecision.ACCEPT
        
        # Persist to "storage"
        persisted_events = {idempotency_key: self.event.copy()}
        
        # Second "session" - load from storage and retry
        existing_events_session2 = persisted_events.copy()
        match2 = self.decider.decide(idempotency_key, self.event, existing_events_session2)
        
        assert match2.decision == IdentityDecision.REJECT_DUPLICATE
    
    def test_retry_with_different_event_id_still_duplicate(self):
        """
        Property: Retry with different event_id but same business fields → REJECT_DUPLICATE.
        
        event_id is not part of idempotency key calculation.
        """
        event1 = self.event.copy()
        event1["event_id"] = "evt_001"
        
        event2 = self.event.copy()
        event2["event_id"] = "evt_999"  # Different event_id
        
        key1 = self.key_generator.generate(event1)
        key2 = self.key_generator.generate(event2)
        
        # Keys should be same (event_id not in key fields)
        assert key1 == key2
        
        existing_events = {key1: event1}
        match = self.decider.decide(key2, event2, existing_events)
        
        assert match.decision == IdentityDecision.REJECT_DUPLICATE
