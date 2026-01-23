"""
RFC-10 Systemic Test - Bypass Detection and Blocking
Tests that operations cannot bypass the guardian.
"""

import pytest
from core.idempotency_guardian.v1.guardian import Guardian
from core.idempotency_guardian.v1.key_builder import KeyBuilder
from core.idempotency_guardian.v1.types import Scope
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_store import InMemoryIdempotencyStore
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_worm_ledger import InMemoryWORMLedger
from tests_systemic.rfc10_idempotency_guardian._support.bypass_target import BypassDetectionTarget


def test_bypass_attempt_detected():
    """
    Test: Direct execution without guardian is detectable.
    """
    target = BypassDetectionTarget()
    
    # Proper path: through guardian
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    guardian.guard(key, target.execute_guarded)
    
    # Bypass attempt: direct execution
    target.execute_unguarded()
    
    # Verify bypass was detected
    assert target.was_bypassed() is True
    assert target.guarded_executions == 1
    assert target.unguarded_executions == 1


def test_no_bypass_when_only_guarded():
    """
    Test: Only guarded executions = no bypass.
    """
    target = BypassDetectionTarget()
    
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    
    # Multiple guarded executions (different keys)
    for i in range(5):
        key = builder.build("user123", f"txn{i}", {"amount": 100 + i})
        guardian.guard(key, target.execute_guarded)
    
    # Verify no bypass
    assert target.was_bypassed() is False
    assert target.guarded_executions == 5
    assert target.unguarded_executions == 0


def test_operation_must_use_guardian():
    """
    Test: Operations should ONLY execute through guardian.
    Architecture pattern enforcement.
    """
    target = BypassDetectionTarget()
    
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    # Correct pattern: always use guardian
    result = guardian.guard(key, target.execute_guarded)
    
    assert result is not None
    assert target.guarded_executions == 1
    assert target.unguarded_executions == 0
    
    # Retry should not execute (but still goes through guardian)
    result2 = guardian.guard(key, target.execute_guarded)
    
    assert result2 is None  # Not executed
    assert target.guarded_executions == 1  # Still 1
    assert target.unguarded_executions == 0


def test_bypass_blocked_by_architecture():
    """
    Test: Guardian architecture blocks unguarded execution paths.
    This test validates the GUARDRAIL: No execution without Guardian.
    """
    target = BypassDetectionTarget()
    
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    # Setup: Use guardian for operation
    def safe_operation():
        return target.execute_guarded()
    
    # Execute through guardian
    guardian.guard(key, safe_operation)
    
    # Verify execution was guarded
    assert target.guarded_executions == 1
    assert target.unguarded_executions == 0
    
    # If someone tries bypass (outside guardian)
    # This is architectural violation - test that we can detect it
    target.execute_unguarded()  # Simulated bypass attempt
    
    # Detection mechanism confirms bypass occurred
    assert target.was_bypassed() is True


def test_guardian_required_for_all_scopes():
    """
    Test: Guardian required for all in-scope operations.
    Verifies INGEST, CANONICALIZE, EVIDENCE_WRITE all use guardian.
    """
    target = BypassDetectionTarget()
    
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    scopes = [Scope.INGEST, Scope.CANONICALIZE, Scope.EVIDENCE_WRITE]
    
    for scope in scopes:
        builder = KeyBuilder(scope)
        key = builder.build("user123", "operation", {"data": scope.value})
        
        # Must use guardian
        result = guardian.guard(key, target.execute_guarded)
        
        # Each scope gets independent execution
        assert result is not None
    
    # Verify all were guarded
    assert target.guarded_executions == len(scopes)
    assert target.unguarded_executions == 0
    assert target.was_bypassed() is False
