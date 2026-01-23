"""
RFC-10 Unit Test - Decisions (ACCEPT/REJECT/FLAG)
Verifies correct decision logic.
"""

import pytest
from core.idempotency_guardian.v1.guardian import Guardian
from core.idempotency_guardian.v1.key_builder import KeyBuilder
from core.idempotency_guardian.v1.types import Scope, Decision
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_store import InMemoryIdempotencyStore
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_worm_ledger import InMemoryWORMLedger


def test_first_attempt_returns_accept_first():
    """First attempt gets ACCEPT_FIRST decision."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    gate = guardian.check(key)
    
    assert gate.decision == Decision.ACCEPT_FIRST
    assert gate.should_execute() is True


def test_duplicate_attempt_returns_reject_duplicate():
    """Duplicate attempt gets REJECT_DUPLICATE decision."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    # First attempt
    gate1 = guardian.check(key)
    assert gate1.decision == Decision.ACCEPT_FIRST
    
    # Second attempt (duplicate)
    gate2 = guardian.check(key)
    assert gate2.decision == Decision.REJECT_DUPLICATE
    assert gate2.should_execute() is False


def test_multiple_duplicates_all_rejected():
    """Multiple duplicate attempts all get REJECT_DUPLICATE."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    # First attempt
    gate1 = guardian.check(key)
    assert gate1.decision == Decision.ACCEPT_FIRST
    
    # Multiple duplicates
    for i in range(5):
        gate = guardian.check(key)
        assert gate.decision == Decision.REJECT_DUPLICATE
        assert gate.should_execute() is False


def test_different_keys_independent_decisions():
    """Different keys get independent ACCEPT_FIRST decisions."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    
    key1 = builder.build("user123", "txn456", {"amount": 100})
    key2 = builder.build("user123", "txn789", {"amount": 200})
    
    gate1 = guardian.check(key1)
    gate2 = guardian.check(key2)
    
    assert gate1.decision == Decision.ACCEPT_FIRST
    assert gate2.decision == Decision.ACCEPT_FIRST


def test_execution_gate_only_accept_first():
    """Only ACCEPT_FIRST allows execution."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    # First attempt - should execute
    gate1 = guardian.check(key)
    assert gate1.should_execute() is True
    
    # Duplicate - should not execute
    gate2 = guardian.check(key)
    assert gate2.should_execute() is False


def test_ambiguous_key_returns_flag_ambiguous():
    """
    Ambiguous attempt (same key, different fingerprint) gets FLAG_AMBIGUOUS.
    Tests collision detection when key hash matches but components differ.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    # Controlled hash function that returns same hash for different inputs
    def collision_hash(value: str) -> str:
        # Always return same hash to force collision
        return "COLLISION_HASH_FIXED"
    
    # First attempt with collision hash
    builder1 = KeyBuilder(Scope.INGEST, hash_fn=collision_hash)
    key1 = builder1.build("user123", "txn456", {"amount": 100})
    
    gate1 = guardian.check(key1)
    assert gate1.decision == Decision.ACCEPT_FIRST
    assert gate1.should_execute() is True
    
    # Second attempt: same hash but different fingerprint (different principal)
    builder2 = KeyBuilder(Scope.INGEST, hash_fn=collision_hash)
    key2 = builder2.build("user999", "txn456", {"amount": 100})
    
    # Keys should be the same (collision)
    assert key1.key == key2.key
    # But fingerprints should differ
    assert key1.principal != key2.principal
    
    gate2 = guardian.check(key2)
    assert gate2.decision == Decision.FLAG_AMBIGUOUS
    assert gate2.should_execute() is False
    
    # Verify evidence was recorded
    assert len(gate2.record.evidence_refs) > 0
    evidence = ledger.get_entry(gate2.record.evidence_refs[0])
    assert evidence["decision"] == "FLAG_AMBIGUOUS"


def test_guard_method_executes_only_on_accept():
    """Guard method executes operation only on ACCEPT_FIRST."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    execution_count = 0
    
    def operation():
        nonlocal execution_count
        execution_count += 1
        return "executed"
    
    # First attempt - executes
    result1 = guardian.guard(key, operation)
    assert result1 == "executed"
    assert execution_count == 1
    
    # Duplicate - does not execute
    result2 = guardian.guard(key, operation)
    assert result2 is None
    assert execution_count == 1  # Still 1, not incremented
