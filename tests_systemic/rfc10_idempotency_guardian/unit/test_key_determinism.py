"""
RFC-10 Unit Test - Key Determinism
Verifies that identical inputs always produce identical keys.
"""

import pytest
from core.idempotency_guardian.v1.key_builder import KeyBuilder
from core.idempotency_guardian.v1.types import Scope


def test_key_determinism_identical_inputs():
    """Same inputs produce same key."""
    builder = KeyBuilder(Scope.INGEST)
    
    payload = {"amount": 100, "currency": "USD"}
    
    key1 = builder.build("user123", "txn456", payload)
    key2 = builder.build("user123", "txn456", payload)
    
    assert key1.key == key2.key
    assert key1.scope == key2.scope
    assert key1.principal == key2.principal
    assert key1.subject == key2.subject
    assert key1.payload_hash == key2.payload_hash


def test_key_determinism_different_principal():
    """Different principal produces different key."""
    builder = KeyBuilder(Scope.INGEST)
    
    payload = {"amount": 100, "currency": "USD"}
    
    key1 = builder.build("user123", "txn456", payload)
    key2 = builder.build("user999", "txn456", payload)
    
    assert key1.key != key2.key


def test_key_determinism_different_subject():
    """Different subject produces different key."""
    builder = KeyBuilder(Scope.INGEST)
    
    payload = {"amount": 100, "currency": "USD"}
    
    key1 = builder.build("user123", "txn456", payload)
    key2 = builder.build("user123", "txn789", payload)
    
    assert key1.key != key2.key


def test_key_determinism_different_payload():
    """Different payload produces different key."""
    builder = KeyBuilder(Scope.INGEST)
    
    key1 = builder.build("user123", "txn456", {"amount": 100})
    key2 = builder.build("user123", "txn456", {"amount": 200})
    
    assert key1.key != key2.key


def test_key_determinism_different_scope():
    """Different scope produces different key."""
    builder1 = KeyBuilder(Scope.INGEST)
    builder2 = KeyBuilder(Scope.CANONICALIZE)
    
    payload = {"amount": 100, "currency": "USD"}
    
    key1 = builder1.build("user123", "txn456", payload)
    key2 = builder2.build("user123", "txn456", payload)
    
    assert key1.key != key2.key


def test_key_determinism_payload_order_irrelevant():
    """Payload with different key order produces same key."""
    builder = KeyBuilder(Scope.INGEST)
    
    payload1 = {"amount": 100, "currency": "USD", "memo": "test"}
    payload2 = {"memo": "test", "currency": "USD", "amount": 100}
    
    key1 = builder.build("user123", "txn456", payload1)
    key2 = builder.build("user123", "txn456", payload2)
    
    assert key1.key == key2.key


def test_key_determinism_across_builder_instances():
    """Different builder instances produce same key."""
    builder1 = KeyBuilder(Scope.INGEST)
    builder2 = KeyBuilder(Scope.INGEST)
    
    payload = {"amount": 100, "currency": "USD"}
    
    key1 = builder1.build("user123", "txn456", payload)
    key2 = builder2.build("user123", "txn456", payload)
    
    assert key1.key == key2.key
