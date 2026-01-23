"""
RFC-02 Systemic Tests: End-to-end ingest scenarios with fixtures.

Scenarios:
- Retry same payload (duplicate detection)
- Out-of-order timestamps (temporal independence)
- Historical backfill (months of retroactive data)
- Partial adapter failure recovery (resume after crash)
"""

import json
from datetime import datetime, timezone

from core.ingest.v1.raw_payload_store import RawPayloadStore
from core.ingest.v1.ingest_record_store import IngestRecordStore
from core.ingest.v1.entrypoint import ingest_raw_observation


def test_systemic_retry_same_payload(tmp_path):
    """Systemic: Retry same payload → duplicate detected, record still created."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    # Load fixture
    fixture_path = tmp_path.parent / "fixtures" / "rfc02_ingest_append_only" / "retry_same_payload.json"
    
    # Fixture inline (simulating file)
    fixture = {
        "scenario": "retry_same_payload",
        "payload": {"source_event_id": "evt_retry_001", "amount": 500},
        "retry_count": 3
    }
    
    payload_bytes = json.dumps(fixture["payload"]).encode("utf-8")
    
    clock = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    records = []
    for _ in range(fixture["retry_count"]):
        record = ingest_raw_observation(
            payload_bytes,
            source_system="retry_test",
            source_connector="api",
            source_environment="prod",
            observed_at="2026-01-01T12:00:00Z",
            source_timestamp="2026-01-01T12:00:00Z",
            raw_format="json",
            adapter_version="1.0.0",
            raw_payload_store=raw_store,
            ingest_record_store=ingest_store,
            _clock=clock
        )
        records.append(record)
    
    # Assertions
    assert records[0]["idempotency_decision"] == "ACCEPT"
    assert all(r["idempotency_decision"] == "REJECT_DUPLICATE" for r in records[1:])
    
    # All records created
    assert ingest_store.count() == fixture["retry_count"]
    
    # Only one raw payload
    assert raw_store.count() == 1


def test_systemic_out_of_order_timestamps(tmp_path):
    """Systemic: Out-of-order timestamps → all accepted (temporal independence)."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    fixture = {
        "scenario": "out_of_order_timestamps",
        "events": [
            {"source_event_id": "evt_003", "observed_at": "2026-01-01T15:00:00Z"},
            {"source_event_id": "evt_001", "observed_at": "2026-01-01T10:00:00Z"},
            {"source_event_id": "evt_002", "observed_at": "2026-01-01T12:00:00Z"}
        ]
    }
    
    clock = datetime(2026, 1, 1, 16, 0, 0, tzinfo=timezone.utc)
    
    for event in fixture["events"]:
        payload = json.dumps({"source_event_id": event["source_event_id"]}).encode("utf-8")
        ingest_raw_observation(
            payload,
            source_system="temporal_test",
            source_connector="batch",
            source_environment="prod",
            observed_at=event["observed_at"],
            source_timestamp=event["observed_at"],
            raw_format="json",
            adapter_version="1.0.0",
            raw_payload_store=raw_store,
            ingest_record_store=ingest_store,
            _clock=clock
        )
    
    # All accepted (unique events)
    records = ingest_store.all_records()
    assert all(r["idempotency_decision"] == "ACCEPT" for r in records)
    assert len(records) == 3


def test_systemic_historical_backfill_months(tmp_path):
    """Systemic: Backfill months of historical data → monotonic growth."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    fixture = {
        "scenario": "historical_backfill",
        "months": 3,
        "events_per_month": 10
    }
    
    total_events = fixture["months"] * fixture["events_per_month"]
    
    clock = datetime(2026, 1, 23, 0, 0, 0, tzinfo=timezone.utc)
    
    for month in range(fixture["months"]):
        for evt in range(fixture["events_per_month"]):
            event_id = f"evt_m{month}_e{evt}"
            payload = json.dumps({"source_event_id": event_id, "month": month}).encode("utf-8")
            
            ingest_raw_observation(
                payload,
                source_system="backfill_test",
                source_connector="batch",
                source_environment="prod",
                observed_at=f"2025-{10+month:02d}-01T00:00:00Z",
                source_timestamp=f"2025-{10+month:02d}-01T00:00:00Z",
                raw_format="json",
                adapter_version="1.0.0",
                raw_payload_store=raw_store,
                ingest_record_store=ingest_store,
                _clock=clock
            )
    
    # Monotonic growth
    assert ingest_store.count() == total_events
    assert raw_store.count() == total_events  # All unique


def test_systemic_partial_adapter_failure_recovery(tmp_path):
    """Systemic: Adapter crashes mid-batch → resume without re-ingesting duplicates."""
    raw_store = RawPayloadStore()
    ingest_store = IngestRecordStore()
    
    fixture = {
        "scenario": "partial_failure_recovery",
        "batch_size": 20,
        "failure_point": 12
    }
    
    clock = datetime(2026, 1, 23, 10, 0, 0, tzinfo=timezone.utc)
    
    # First attempt: ingest up to failure_point
    for i in range(fixture["failure_point"]):
        payload = json.dumps({"source_event_id": f"batch_evt_{i}"}).encode("utf-8")
        ingest_raw_observation(
            payload,
            source_system="adapter_crash_test",
            source_connector="batch",
            source_environment="prod",
            observed_at="2026-01-23T10:00:00Z",
            source_timestamp=None,
            raw_format="json",
            adapter_version="1.0.0",
            raw_payload_store=raw_store,
            ingest_record_store=ingest_store,
            _clock=clock
        )
    
    # Simulate crash
    count_before_recovery = ingest_store.count()
    assert count_before_recovery == fixture["failure_point"]
    
    # Recovery: re-attempt entire batch (includes duplicates)
    for i in range(fixture["batch_size"]):
        payload = json.dumps({"source_event_id": f"batch_evt_{i}"}).encode("utf-8")
        ingest_raw_observation(
            payload,
            source_system="adapter_crash_test",
            source_connector="batch",
            source_environment="prod",
            observed_at="2026-01-23T10:00:00Z",
            source_timestamp=None,
            raw_format="json",
            adapter_version="1.0.0",
            raw_payload_store=raw_store,
            ingest_record_store=ingest_store,
            _clock=clock
        )
    
    # All events recorded (duplicates + new)
    final_count = ingest_store.count()
    expected = fixture["failure_point"] + fixture["batch_size"]
    assert final_count == expected
    
    # Raw store: only unique payloads
    assert raw_store.count() == fixture["batch_size"]
