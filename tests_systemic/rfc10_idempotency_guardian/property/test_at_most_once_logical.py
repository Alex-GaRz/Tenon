"""
RFC-10 Property-Based Test - At-Most-Once Logical Guarantee
Deterministic property testing without external dependencies.
"""

import pytest
import hashlib
from core.idempotency_guardian.v1.guardian import Guardian
from core.idempotency_guardian.v1.key_builder import KeyBuilder
from core.idempotency_guardian.v1.types import Scope, Decision
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_store import InMemoryIdempotencyStore
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_worm_ledger import InMemoryWORMLedger


def _generate_test_inputs(seed):
    """Generate deterministic test inputs from seed."""
    h = hashlib.sha256(str(seed).encode()).hexdigest()
    principal = f"user_{h[:8]}"
    subject = f"txn_{h[8:16]}"
    amount = int(h[16:20], 16) % 1000000 + 1
    return principal, subject, amount


def test_at_most_once_execution_property():
    """
    Property: For any input, execution happens at most once.
    Multiple attempts with same inputs result in exactly one ACCEPT_FIRST.
    """
    # Test across 50 deterministic seeds
    for seed in range(50):
        store = InMemoryIdempotencyStore()
        ledger = InMemoryWORMLedger()
        guardian = Guardian(store, ledger)
        
        builder = KeyBuilder(Scope.INGEST)
        principal, subject, amount = _generate_test_inputs(seed)
        key = builder.build(principal, subject, {"amount": amount})
        
        # Make multiple attempts (arbitrary number)
        attempts = 5
        accept_count = 0
        reject_count = 0
        
        for _ in range(attempts):
            gate = guardian.check(key)
            if gate.decision == Decision.ACCEPT_FIRST:
                accept_count += 1
            elif gate.decision == Decision.REJECT_DUPLICATE:
                reject_count += 1
        
        # Property: Exactly one ACCEPT, rest are REJECT
        assert accept_count == 1, f"Seed {seed}: expected 1 ACCEPT, got {accept_count}"
        assert reject_count == attempts - 1, f"Seed {seed}: expected {attempts-1} REJECT, got {reject_count}"


def test_retry_storm_at_most_once():
    """
    Property: Even with many retries, operation accepted at most once.
    """
    # Test with varying retry counts (1 to 20)
    for num_retries in range(1, 21):
        store = InMemoryIdempotencyStore()
        ledger = InMemoryWORMLedger()
        guardian = Guardian(store, ledger)
        
        builder = KeyBuilder(Scope.INGEST)
        key = builder.build("user123", "txn456", {"amount": 100})
        
        execution_count = 0
        
        def operation():
            nonlocal execution_count
            execution_count += 1
            return execution_count
        
        # Execute multiple times
        for _ in range(num_retries):
            guardian.guard(key, operation)
        
        # Property: Operation executed exactly once
        assert execution_count == 1, f"Retries {num_retries}: expected 1 execution, got {execution_count}"


def test_different_keys_independent():
    """
    Property: Different keys result in independent decisions.
    Each unique operation gets exactly one ACCEPT.
    """
    # Test with varying number of operations (1 to 10)
    for num_different_operations in range(1, 11):
        store = InMemoryIdempotencyStore()
        ledger = InMemoryWORMLedger()
        guardian = Guardian(store, ledger)
        
        builder = KeyBuilder(Scope.INGEST)
        
        accept_count = 0
        
        for i in range(num_different_operations):
            key = builder.build("user123", f"txn{i}", {"amount": 100 + i})
            gate = guardian.check(key)
            if gate.decision == Decision.ACCEPT_FIRST:
                accept_count += 1
        
        # Property: Each different key gets ACCEPT_FIRST
        assert accept_count == num_different_operations, f"Expected {num_different_operations} ACCEPTs, got {accept_count}"


def test_deterministic_decision_across_instances():
    """
    Property: Same key always produces same decision sequence.
    Even with different Guardian instances (same store).
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    # First guardian instance
    guardian1 = Guardian(store, ledger)
    gate1 = guardian1.check(key)
    
    # Second guardian instance (same store)
    guardian2 = Guardian(store, ledger)
    gate2 = guardian2.check(key)
    
    # Property: First is ACCEPT, second is REJECT
    assert gate1.decision == Decision.ACCEPT_FIRST
    assert gate2.decision == Decision.REJECT_DUPLICATE
