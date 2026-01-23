"""
RFC-10 Unit Test - Record Fields (rule_version, evidence_refs)
Verifies IdempotencyRecord contains required fields.
"""

import pytest
from core.idempotency_guardian.v1.guardian import Guardian
from core.idempotency_guardian.v1.key_builder import KeyBuilder
from core.idempotency_guardian.v1.types import Scope, Decision
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_store import InMemoryIdempotencyStore
from tests_systemic.rfc10_idempotency_guardian._support.in_memory_worm_ledger import InMemoryWORMLedger


def test_record_contains_rule_version():
    """Record includes rule_version field."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    gate = guardian.check(key)
    record = gate.record
    
    assert record.rule_version is not None
    assert isinstance(record.rule_version, str)
    assert record.rule_version == "1.0.0"


def test_record_contains_evidence_refs():
    """Record includes evidence_refs pointing to WORM ledger."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    gate = guardian.check(key)
    record = gate.record
    
    assert record.evidence_refs is not None
    assert isinstance(record.evidence_refs, list)
    assert len(record.evidence_refs) > 0


def test_evidence_refs_point_to_worm_ledger():
    """Evidence refs can be used to retrieve WORM ledger entries."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    gate = guardian.check(key)
    record = gate.record
    
    # Should be able to retrieve from ledger
    for ref in record.evidence_refs:
        entry = ledger.get_entry(ref)
        assert entry is not None
        assert entry["type"] == "idempotency_check"
        assert entry["key"] == key.key


def test_record_contains_timestamps():
    """Record includes first_seen_at and decided_at timestamps."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    gate = guardian.check(key)
    record = gate.record
    
    assert record.first_seen_at is not None
    assert record.decided_at is not None


def test_record_contains_scope():
    """Record includes scope field."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.CANONICALIZE)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    gate = guardian.check(key)
    record = gate.record
    
    assert record.scope == Scope.CANONICALIZE


def test_record_contains_decision():
    """Record includes decision field."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    key = builder.build("user123", "txn456", {"amount": 100})
    
    gate = guardian.check(key)
    record = gate.record
    
    assert record.decision == Decision.ACCEPT_FIRST


def test_record_has_unique_id():
    """Each record has unique idempotency_record_id."""
    store = InMemoryIdempotencyStore()
    ledger = InMemoryWORMLedger()
    guardian = Guardian(store, ledger)
    
    builder = KeyBuilder(Scope.INGEST)
    
    key1 = builder.build("user123", "txn456", {"amount": 100})
    key2 = builder.build("user123", "txn789", {"amount": 200})
    
    gate1 = guardian.check(key1)
    gate2 = guardian.check(key2)
    
    assert gate1.record.idempotency_record_id != gate2.record.idempotency_record_id
