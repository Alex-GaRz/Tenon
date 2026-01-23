"""
RFC-02 Unit Tests: Ingest Append-Only guarantees.

Tests:
- Append-only semantics (no update/delete)
- Idempotency decision always present
- Timestamps never collapsed
- Hash consistency
"""

import json
from datetime import datetime, timezone

from core.ingest.v1.raw_payload_store import RawPayloadStore
from core.ingest.v1.ingest_record_store import IngestRecordStore
from core.ingest.v1.entrypoint import ingest_raw_observation


def test_raw_payload_store_append_only():
    """Raw payload store is append-only and idempotent."""
    store = RawPayloadStore()
    
    payload = b'{"amount": 100}'
    hash1, ptr1, size1 = store.append(payload, raw_format="json")
    hash2, ptr2, size2 = store.append(payload, raw_format="json")
    
    # Same bytes → same hash, pointer, size
    assert hash1 == hash2
    assert ptr1 == ptr2
    assert size1 == size2 == len(payload)
    
    # No duplication in store
    assert store.count() == 1


def test_raw_payload_store_deterministic_hash():
    """Hash is deterministic and consistent."""
    store = RawPayloadStore()
    
    payload = b'{"event_id": "abc123"}'
    hash1, ptr1, _ = store.append(payload, raw_format="json")
    
    # Retrieve and verify
    retrieved = store.get(ptr1)
    assert retrieved == payload
    
    # Hash is SHA-256
    import hashlib
    expected_hash = hashlib.sha256(payload).hexdigest()
    assert hash1 == expected_hash


def test_ingest_record_store_append_only_monotonicity():
    """Ingest record store is append-only with monotonic growth."""
    store = IngestRecordStore()
    
    assert store.count() == 0
    
    record1 = {
        "ingest_id": "id1",
        "raw_payload_hash": "hash1",
        "event_id": None,
        "idempotency_decision": "ACCEPT",
        "source_system": "test",
        "source_connector": "test",
        "source_environment": "test",
        "observed_at": "2026-01-01T00:00:00Z",
        "ingested_at": "2026-01-01T00:00:01Z",
        "source_timestamp": None,
        "raw_pointer": "raw:hash1",
        "raw_format": "json",
        "raw_size_bytes": 10,
        "ingest_protocol_version": "1.0.0",
        "adapter_version": "1.0.0",
        "status": "RECORDED",
        "warnings": []
    }
    
    store.append(record1)
    assert store.count() == 1
    
    record2 = {**record1, "ingest_id": "id2", "raw_payload_hash": "hash2", "raw_pointer": "raw:hash2"}
    store.append(record2)
    assert store.count() == 2
    
    # Monotonicity: count only increases
    all_records = store.all_records()
    assert len(all_records) == 2


def test_ingest_record_store_query_by_hash():
    """Query ingest records by raw payload hash."""
    store = IngestRecordStore()
    
    record1 = {
        "ingest_id": "id1",
        "raw_payload_hash": "hashA",
        "event_id": None,
        "idempotency_decision": "ACCEPT",
        "source_system": "test",
        "source_connector": "test",
        "source_environment": "test",
        "observed_at": "2026-01-01T00:00:00Z",
        "ingested_at": "2026-01-01T00:00:01Z",
        "source_timestamp": None,
        "raw_pointer": "raw:hashA",
        "raw_format": "json",
        "raw_size_bytes": 10,
        "ingest_protocol_version": "1.0.0",
        "adapter_version": "1.0.0",
        "status": "RECORDED",
        "warnings": []
    }
    
    record2 = {**record1, "ingest_id": "id2"}  # Same hash (duplicate)
    record3 = {**record1, "ingest_id": "id3", "raw_payload_hash": "hashB", "raw_pointer": "raw:hashB"}
    
    store.append(record1)
    store.append(record2)
    store.append(record3)
    
    # Query by hashA
    matches = store.scan_by_raw_payload_hash("hashA")
    assert len(matches) == 2
    assert {m["ingest_id"] for m in matches} == {"id1", "id2"}
    
    # Query by hashB
    matches = store.scan_by_raw_payload_hash("hashB")
    assert len(matches) == 1
    assert matches[0]["ingest_id"] == "id3"
    
    # Query non-existent hash
    matches = store.scan_by_raw_payload_hash("hashC")
    assert len(matches) == 0


def test_ingest_entrypoint_always_creates_record():
    """Ingest entrypoint always creates IngestRecord, even for duplicates."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    payload = json.dumps({"amount": 100, "source_event_id": "evt1"}).encode("utf-8")
    
    clock = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # First ingest
    record1 = ingest_raw_observation(
        payload,
        source_system="bank_a",
        source_connector="api",
        source_environment="prod",
        observed_at="2026-01-01T00:00:00Z",
        source_timestamp="2026-01-01T00:00:00Z",
        raw_format="json",
        adapter_version="1.0.0",
        raw_payload_store=raw_store,
        ingest_record_store=ingest_store,
        _clock=clock
    )
    
    assert record1["idempotency_decision"] == "ACCEPT"
    assert record1["event_id"] is not None
    assert ingest_store.count() == 1
    
    # Duplicate ingest (same payload)
    record2 = ingest_raw_observation(
        payload,
        source_system="bank_a",
        source_connector="api",
        source_environment="prod",
        observed_at="2026-01-01T00:00:00Z",
        source_timestamp="2026-01-01T00:00:00Z",
        raw_format="json",
        adapter_version="1.0.0",
        raw_payload_store=raw_store,
        ingest_record_store=ingest_store,
        _clock=clock
    )
    
    # Duplicate detected
    assert record2["idempotency_decision"] == "REJECT_DUPLICATE"
    assert record2["event_id"] == record1["event_id"]
    
    # CRITICAL: Record still created
    assert ingest_store.count() == 2


def test_timestamps_never_collapsed():
    """Timestamps (observed_at, source_timestamp, ingested_at) remain separate."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    payload = json.dumps({"amount": 50}).encode("utf-8")
    
    observed_at = "2026-01-01T10:00:00Z"
    source_timestamp = "2026-01-01T09:00:00Z"
    ingested_at_clock = datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
    
    record = ingest_raw_observation(
        payload,
        source_system="bank_b",
        source_connector="batch",
        source_environment="prod",
        observed_at=observed_at,
        source_timestamp=source_timestamp,
        raw_format="json",
        adapter_version="2.0.0",
        raw_payload_store=raw_store,
        ingest_record_store=ingest_store,
        _clock=ingested_at_clock
    )
    
    # All three timestamps present and distinct
    assert record["observed_at"] == observed_at
    assert record["source_timestamp"] == source_timestamp
    assert record["ingested_at"] == "2026-01-01T11:00:00+00:00"


def test_idempotency_decision_always_present():
    """Idempotency decision is always recorded (ACCEPT/REJECT_DUPLICATE/FLAG_AMBIGUOUS)."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    # Valid payload
    payload = json.dumps({"source_event_id": "evt_valid"}).encode("utf-8")
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
    
    assert record["idempotency_decision"] in ["ACCEPT", "REJECT_DUPLICATE", "FLAG_AMBIGUOUS"]
    assert "idempotency_decision" in record
    
    # Unparseable payload (should FLAG_AMBIGUOUS)
    bad_payload = b"not valid json"
    record2 = ingest_raw_observation(
        bad_payload,
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
    
    assert record2["idempotency_decision"] == "FLAG_AMBIGUOUS"
    assert len(record2["warnings"]) > 0


def test_ingest_id_always_present():
    """Ingest ID is always generated and non-empty."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    payload = json.dumps({"test": "data"}).encode("utf-8")
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
    
    assert "ingest_id" in record
    assert record["ingest_id"] != ""
    assert isinstance(record["ingest_id"], str)
