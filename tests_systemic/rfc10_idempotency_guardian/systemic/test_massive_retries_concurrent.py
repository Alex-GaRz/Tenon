"""
RFC-10 Systemic Test - Massive Retries with Concurrency
Tests at-most-once guarantee under concurrent retry storm.
"""

import pytest
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.idempotency_guardian.v1.guardian import Guardian
from core.idempotency_guardian.v1.key_builder import KeyBuilder
from core.idempotency_guardian.v1.types import Scope, Decision
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_store import InMemoryIdempotencyStore
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_worm_ledger import InMemoryWORMLedger


def test_concurrent_retries_single_key():
    """
    Test: 100 concurrent retries of same operation.
    Expect: Exactly 1 ACCEPT_FIRST, 99 REJECT_DUPLICATE.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    num_threads = 100
    decisions = []
    lock = threading.Lock()
    
    def check_idempotency():
        gate = guardian.check(key)
        with lock:
            decisions.append(gate.decision)
        return gate.decision
    
    # Execute concurrently
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_idempotency) for _ in range(num_threads)]
        for future in as_completed(futures):
            future.result()
    
    # Verify exactly one ACCEPT
    accept_count = sum(1 for d in decisions if d == Decision.ACCEPT_FIRST)
    reject_count = sum(1 for d in decisions if d == Decision.REJECT_DUPLICATE)
    
    assert accept_count == 1
    assert reject_count == num_threads - 1
    assert len(decisions) == num_threads


def test_concurrent_executions_single_key():
    """
    Test: 100 concurrent guarded executions of same operation.
    Expect: Operation executes exactly once.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    num_threads = 100
    execution_count = 0
    lock = threading.Lock()
    
    def guarded_operation():
        def operation():
            nonlocal execution_count
            with lock:
                execution_count += 1
            return "executed"
        
        return guardian.guard(key, operation)
    
    # Execute concurrently
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(guarded_operation) for _ in range(num_threads)]
        results = [future.result() for future in as_completed(futures)]
    
    # Verify operation executed exactly once
    assert execution_count == 1
    
    # Verify results: one "executed", rest None
    executed_count = sum(1 for r in results if r == "executed")
    none_count = sum(1 for r in results if r is None)
    
    assert executed_count == 1
    assert none_count == num_threads - 1


def test_concurrent_different_keys():
    """
    Test: 50 concurrent operations with different keys.
    Expect: All 50 get ACCEPT_FIRST (independent).
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    
    num_operations = 50
    decisions = []
    lock = threading.Lock()
    
    def check_unique_operation(index):
        key = builder.build("user123", f"txn{index}", {"amount": 100 + index})
        gate = guardian.check(key)
        with lock:
            decisions.append(gate.decision)
        return gate.decision
    
    # Execute concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_unique_operation, i) for i in range(num_operations)]
        for future in as_completed(futures):
            future.result()
    
    # Verify all ACCEPT_FIRST
    accept_count = sum(1 for d in decisions if d == Decision.ACCEPT_FIRST)
    assert accept_count == num_operations


def test_concurrent_mixed_retries():
    """
    Test: 10 different keys, each retried 10 times concurrently.
    Expect: 10 ACCEPT_FIRST total, 90 REJECT_DUPLICATE.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    
    num_keys = 10
    retries_per_key = 10
    decisions = []
    lock = threading.Lock()
    
    def check_with_retry(key_index, retry_index):
        key = builder.build("user123", f"txn{key_index}", {"amount": 100 + key_index})
        gate = guardian.check(key)
        with lock:
            decisions.append((key_index, gate.decision))
        return gate.decision
    
    # Execute concurrently
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for key_idx in range(num_keys):
            for retry_idx in range(retries_per_key):
                futures.append(executor.submit(check_with_retry, key_idx, retry_idx))
        
        for future in as_completed(futures):
            future.result()
    
    # Verify totals
    accept_count = sum(1 for _, d in decisions if d == Decision.ACCEPT_FIRST)
    reject_count = sum(1 for _, d in decisions if d == Decision.REJECT_DUPLICATE)
    
    assert accept_count == num_keys
    assert reject_count == num_keys * (retries_per_key - 1)
    assert len(decisions) == num_keys * retries_per_key
