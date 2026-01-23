"""
RFC-02 Property Tests: Ingest Append-Only invariants.

Property-based tests for:
- Determinism: same input → same hash
- Monotonicity: count never decreases
- Idempotency: duplicate append → no duplicates in raw store
"""

import json
from datetime import datetime, timezone

from core.ingest.v1.raw_payload_store import RawPayloadStore
from core.ingest.v1.ingest_record_store import IngestRecordStore
from core.ingest.v1.entrypoint import ingest_raw_observation


def test_property_raw_store_deterministic_hash():
    """Property: Same bytes → same hash (deterministic)."""
    store = RawPayloadStore()
    
    payload = b'{"determinism": "test"}'
    
    results = []
    for _ in range(10):
        hash_val, ptr, size = store.append(payload, raw_format="json")
        results.append((hash_val, ptr, size))
    
    # All hashes identical
    hashes = [r[0] for r in results]
    assert len(set(hashes)) == 1
    
    # All pointers identical
    pointers = [r[1] for r in results]
    assert len(set(pointers)) == 1
    
    # No duplication in store
    assert store.count() == 1


def test_property_ingest_store_monotonic_growth():
    """Property: Ingest record count is monotonically increasing."""
    store = IngestRecordStore()
    
    counts = [store.count()]
    
    for i in range(20):
        record = {
            "ingest_id": f"id_{i}",
            "raw_payload_hash": f"hash_{i}",
            "event_id": None,
            "idempotency_decision": "ACCEPT",
            "source_system": "test",
            "source_connector": "test",
            "source_environment": "test",
            "observed_at": "2026-01-01T00:00:00Z",
            "ingested_at": "2026-01-01T00:00:01Z",
            "source_timestamp": None,
            "raw_pointer": f"raw:hash_{i}",
            "raw_format": "json",
            "raw_size_bytes": 10,
            "ingest_protocol_version": "1.0.0",
            "adapter_version": "1.0.0",
            "status": "RECORDED",
            "warnings": []
        }
        store.append(record)
        counts.append(store.count())
    
    # Monotonicity: each count >= previous count
    for i in range(1, len(counts)):
        assert counts[i] >= counts[i-1]
    
    # Strict growth: final count == initial + 20
    assert counts[-1] == counts[0] + 20


def test_property_duplicate_ingest_always_recorded():
    """Property: Duplicate payloads → multiple IngestRecords (append-only)."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    payload = json.dumps({"source_event_id": "dup_test"}).encode("utf-8")
    
    clock = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # Ingest same payload N times
    N = 5
    for i in range(N):
        ingest_raw_observation(
            payload,
            source_system="bank",
            source_connector="api",
            source_environment="prod",
            observed_at="2026-01-01T00:00:00Z",
            source_timestamp=None,
            raw_format="json",
            adapter_version="1.0.0",
            raw_payload_store=raw_store,
            ingest_record_store=ingest_store,
            _clock=clock
        )
    
    # Property: N IngestRecords created (one per call)
    assert ingest_store.count() == N
    
    # Property: Only 1 raw payload (deduplicated)
    assert raw_store.count() == 1


def test_property_idempotency_decision_stable():
    """Property: Same payload → consistent idempotency decision."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    payload = json.dumps({"source_event_id": "stable_test", "amount": 999}).encode("utf-8")
    
    clock = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    decisions = []
    event_ids = []
    
    for _ in range(3):
        record = ingest_raw_observation(
            payload,
            source_system="bank",
            source_connector="api",
            source_environment="prod",
            observed_at="2026-01-01T00:00:00Z",
            source_timestamp=None,
            raw_format="json",
            adapter_version="1.0.0",
            raw_payload_store=raw_store,
            ingest_record_store=ingest_store,
            _clock=clock
        )
        decisions.append(record["idempotency_decision"])
        event_ids.append(record["event_id"])
    
    # First: ACCEPT, rest: REJECT_DUPLICATE
    assert decisions[0] == "ACCEPT"
    assert all(d == "REJECT_DUPLICATE" for d in decisions[1:])
    
    # Same event_id for all
    assert len(set(event_ids)) == 1


def test_property_hash_consistency():
    """Property: raw_payload_hash matches actual hash of raw_bytes."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    payload = json.dumps({"consistency": "check"}).encode("utf-8")
    
    record = ingest_raw_observation(
        payload,
        source_system="sys",
        source_connector="conn",
        source_environment="prod",
        observed_at="2026-01-01T00:00:00Z",
        source_timestamp=None,
        raw_format="json",
        adapter_version="1.0.0",
        raw_payload_store=raw_store,
        ingest_record_store=ingest_store
    )
    
    # Verify hash consistency
    import hashlib
    expected_hash = hashlib.sha256(payload).hexdigest()
    assert record["raw_payload_hash"] == expected_hash
    
    # Retrieve and verify
    retrieved = raw_store.get(record["raw_pointer"])
    assert retrieved == payload
