"""
RFC-10 Systemic Test - Replay from WORM Ledger
Tests deterministic replay of decisions from WORM ledger.
"""

import pytest
from core.idempotency_guardian.v1.guardian import Guardian
from core.idempotency_guardian.v1.key_builder import KeyBuilder
from core.idempotency_guardian.v1.replay import ReplayEngine
from core.idempotency_guardian.v1.types import Scope, Decision
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_store import InMemoryIdempotencyStore
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_worm_ledger import InMemoryWORMLedger


def test_replay_reproduces_decisions():
    """
    Test: Replay from WORM ledger reproduces original decisions.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    
    # Make several decisions
    keys = [
        builder.build("user123", "txn1", {"amount": 100}),
        builder.build("user123", "txn2", {"amount": 200}),
        builder.build("user123", "txn3", {"amount": 300}),
    ]
    
    original_decisions = []
    for key in keys:
        gate = guardian.check(key)
        original_decisions.append(gate.decision)
    
    # Replay from WORM ledger
    replay_engine = ReplayEngine(ledger, store)
    replayed_records = replay_engine.replay_all()
    
    # Verify same number of decisions
    assert len(replayed_records) == len(original_decisions)
    
    # Verify decisions match
    for i, record in enumerate(replayed_records):
        assert record.decision == original_decisions[i]


def test_replay_with_retries():
    """
    Test: Replay captures all attempts including retries.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn1", {"amount": 100})
    
    # First attempt (ACCEPT)
    gate1 = guardian.check(key)
    
    # Retries (REJECT)
    gate2 = guardian.check(key)
    gate3 = guardian.check(key)
    
    # Replay
    replay_engine = ReplayEngine(ledger, store)
    replayed_records = replay_engine.replay_all()
    
    # Should have all 3 attempts in ledger
    assert len(replayed_records) == 3
    assert replayed_records[0].decision == Decision.ACCEPT_FIRST
    assert replayed_records[1].decision == Decision.REJECT_DUPLICATE
    assert replayed_records[2].decision == Decision.REJECT_DUPLICATE


def test_replay_determinism():
    """
    Test: Multiple replays produce identical results.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    
    # Make some decisions
    for i in range(5):
        key = builder.build("user123", f"txn{i}", {"amount": 100 + i})
        guardian.check(key)
    
    # Replay multiple times
    replay_engine = ReplayEngine(ledger, store)
    
    replay1 = replay_engine.replay_all()
    replay2 = replay_engine.replay_all()
    replay3 = replay_engine.replay_all()
    
    # Verify identical results
    assert len(replay1) == len(replay2) == len(replay3)
    
    for i in range(len(replay1)):
        assert replay1[i].idempotency_key == replay2[i].idempotency_key
        assert replay1[i].decision == replay2[i].decision
        assert replay2[i].idempotency_key == replay3[i].idempotency_key
        assert replay2[i].decision == replay3[i].decision


def test_replay_verify_determinism_method():
    """
    Test: ReplayEngine.verify_determinism() validates replay consistency.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    
    # Make decisions
    for i in range(10):
        key = builder.build("user123", f"txn{i}", {"amount": 100 + i})
        guardian.check(key)
    
    # Verify determinism
    replay_engine = ReplayEngine(ledger, store)
    is_deterministic = replay_engine.verify_determinism()
    
    assert is_deterministic is True


def test_replay_empty_ledger():
    """
    Test: Replay from empty ledger returns empty list.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    
    replay_engine = ReplayEngine(ledger, store)
    replayed_records = replay_engine.replay_all()
    
    assert len(replayed_records) == 0


def test_replay_preserves_order():
    """
    Test: Replay preserves original order of decisions.
    """
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    
    # Make decisions in specific order
    expected_keys = []
    for i in range(10):
        key = builder.build("user123", f"txn{i}", {"amount": 100 + i})
        guardian.check(key)
        expected_keys.append(key.key)
    
    # Replay
    replay_engine = ReplayEngine(ledger, store)
    replayed_records = replay_engine.replay_all()
    
    # Verify order
    replayed_keys = [r.idempotency_key for r in replayed_records]
    assert replayed_keys == expected_keys
