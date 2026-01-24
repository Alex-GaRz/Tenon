"""RFC-08 Event Sourcing Evidence - Unit Tests"""
import pytest
from core.event_sourcing_evidence.v1.evidence_event import (
    EvidenceEvent,
    EvidenceEventType,
)
from core.event_sourcing_evidence.v1.evidence_log import EvidenceLog
from core.event_sourcing_evidence.v1.replay import replay_fingerprint


def test_evidence_event_valid_utc():
    """Valid UTC timestamp is accepted"""
    event = EvidenceEvent(
        event_id="test-001",
        event_type=EvidenceEventType.INGEST_RECEIVED,
        produced_at="2026-01-23T10:00:00Z",
        payload={},
        caused_by=[]
    )
    assert event.produced_at == "2026-01-23T10:00:00Z"


def test_evidence_event_invalid_utc():
    """Non-UTC timestamp raises ValueError"""
    with pytest.raises(ValueError, match="ISO-8601 UTC format ending in Z"):
        EvidenceEvent(
            event_id="test-002",
            event_type=EvidenceEventType.INGEST_RECEIVED,
            produced_at="2026-01-23T10:00:00",
            payload={},
            caused_by=[]
        )


def test_evidence_log_append_increments_sequence():
    """EvidenceLog.append returns monotonic sequence numbers"""
    log = EvidenceLog()
    event1 = EvidenceEvent(
        event_id="e1",
        event_type=EvidenceEventType.INGEST_RECEIVED,
        produced_at="2026-01-23T10:00:00Z",
        payload={},
        caused_by=[]
    )
    event2 = EvidenceEvent(
        event_id="e2",
        event_type=EvidenceEventType.NORMALIZATION_APPLIED,
        produced_at="2026-01-23T10:00:01Z",
        payload={},
        caused_by=["e1"]
    )

    seq1 = log.append(event1)
    seq2 = log.append(event2)

    assert seq1 == 1
    assert seq2 == 2


def test_evidence_log_rejects_time_reversal():
    """EvidenceLog rejects events with produced_at before last event"""
    log = EvidenceLog()
    event1 = EvidenceEvent(
        event_id="e1",
        event_type=EvidenceEventType.INGEST_RECEIVED,
        produced_at="2026-01-23T10:00:00Z",
        payload={},
        caused_by=[]
    )
    event2 = EvidenceEvent(
        event_id="e2",
        event_type=EvidenceEventType.NORMALIZATION_APPLIED,
        produced_at="2026-01-23T09:59:59Z",
        payload={},
        caused_by=[]
    )

    log.append(event1)
    with pytest.raises(ValueError, match="before last event"):
        log.append(event2)


def test_evidence_log_rejects_invalid_caused_by():
    """EvidenceLog rejects caused_by references to non-existent events"""
    log = EvidenceLog()
    event = EvidenceEvent(
        event_id="e1",
        event_type=EvidenceEventType.NORMALIZATION_APPLIED,
        produced_at="2026-01-23T10:00:00Z",
        payload={},
        caused_by=["nonexistent"]
    )

    with pytest.raises(ValueError, match="non-existent event_id"):
        log.append(event)


def test_evidence_log_at_or_before():
    """EvidenceLog.at_or_before filters by timestamp"""
    log = EvidenceLog()
    event1 = EvidenceEvent(
        event_id="e1",
        event_type=EvidenceEventType.INGEST_RECEIVED,
        produced_at="2026-01-23T10:00:00Z",
        payload={},
        caused_by=[]
    )
    event2 = EvidenceEvent(
        event_id="e2",
        event_type=EvidenceEventType.NORMALIZATION_APPLIED,
        produced_at="2026-01-23T10:00:01Z",
        payload={},
        caused_by=["e1"]
    )
    event3 = EvidenceEvent(
        event_id="e3",
        event_type=EvidenceEventType.STATE_TRANSITION,
        produced_at="2026-01-23T10:00:02Z",
        payload={},
        caused_by=["e2"]
    )

    log.append(event1)
    log.append(event2)
    log.append(event3)

    filtered = log.at_or_before("2026-01-23T10:00:01Z")
    assert len(filtered) == 2
    assert filtered[0][1].event_id == "e1"
    assert filtered[1][1].event_id == "e2"


def test_replay_fingerprint_deterministic():
    """replay_fingerprint produces same hash for same inputs"""
    events = [
        EvidenceEvent(
            event_id="e1",
            event_type=EvidenceEventType.INGEST_RECEIVED,
            produced_at="2026-01-23T10:00:00Z",
            payload={},
            caused_by=[]
        ),
        EvidenceEvent(
            event_id="e2",
            event_type=EvidenceEventType.NORMALIZATION_APPLIED,
            produced_at="2026-01-23T10:00:01Z",
            payload={},
            caused_by=["e1"]
        )
    ]

    fp1 = replay_fingerprint("v1.0", events)
    fp2 = replay_fingerprint("v1.0", events)

    assert fp1 == fp2
    assert len(fp1) == 64


def test_replay_fingerprint_changes_with_version():
    """replay_fingerprint changes when engine_version changes"""
    events = [
        EvidenceEvent(
            event_id="e1",
            event_type=EvidenceEventType.INGEST_RECEIVED,
            produced_at="2026-01-23T10:00:00Z",
            payload={},
            caused_by=[]
        )
    ]

    fp1 = replay_fingerprint("v1.0", events)
    fp2 = replay_fingerprint("v2.0", events)

    assert fp1 != fp2
