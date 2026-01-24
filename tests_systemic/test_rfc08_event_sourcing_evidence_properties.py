"""RFC-08 Event Sourcing Evidence - Property Tests"""
import pytest
from core.event_sourcing_evidence.v1.evidence_event import (
    EvidenceEvent,
    EvidenceEventType,
)
from core.event_sourcing_evidence.v1.evidence_log import EvidenceLog


def test_property_evidence_log_append_only():
    """EvidenceLog never allows modification or deletion of events"""
    log = EvidenceLog()
    event = EvidenceEvent(
        event_id="e1",
        event_type=EvidenceEventType.INGEST_RECEIVED,
        produced_at="2026-01-23T10:00:00Z",
        payload={},
        caused_by=[]
    )

    log.append(event)
    all_events_before = log.all()

    all_events_after = log.all()
    assert len(all_events_before) == len(all_events_after)
    assert all_events_before[0][1].event_id == all_events_after[0][1].event_id


def test_property_sequence_numbers_unique_and_monotonic():
    """Sequence numbers are unique and strictly increasing"""
    log = EvidenceLog()
    sequences = []

    for i in range(5):
        event = EvidenceEvent(
            event_id=f"e{i}",
            event_type=EvidenceEventType.INGEST_RECEIVED,
            produced_at=f"2026-01-23T10:00:0{i}Z",
            payload={},
            caused_by=[]
        )
        seq = log.append(event)
        sequences.append(seq)

    assert sequences == [1, 2, 3, 4, 5]
    assert len(set(sequences)) == len(sequences)


def test_property_total_order_by_time_then_sequence():
    """Events are totally ordered: first by produced_at, then by sequence"""
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
        produced_at="2026-01-23T10:00:00Z",
        payload={},
        caused_by=["e1"]
    )
    event3 = EvidenceEvent(
        event_id="e3",
        event_type=EvidenceEventType.STATE_TRANSITION,
        produced_at="2026-01-23T10:00:01Z",
        payload={},
        caused_by=["e2"]
    )

    log.append(event1)
    log.append(event2)
    log.append(event3)

    all_events = log.all()

    assert all_events[0][1].produced_at <= all_events[1][1].produced_at
    assert all_events[1][1].produced_at <= all_events[2][1].produced_at

    assert all_events[0][0] < all_events[1][0] < all_events[2][0]


def test_property_immutable_events():
    """EvidenceEvent is immutable"""
    event = EvidenceEvent(
        event_id="e1",
        event_type=EvidenceEventType.INGEST_RECEIVED,
        produced_at="2026-01-23T10:00:00Z",
        payload={},
        caused_by=[]
    )

    with pytest.raises(AttributeError):
        event.event_id = "modified"


def test_property_causality_integrity():
    """caused_by can only reference events already in the log"""
    log = EvidenceLog()

    event1 = EvidenceEvent(
        event_id="e1",
        event_type=EvidenceEventType.INGEST_RECEIVED,
        produced_at="2026-01-23T10:00:00Z",
        payload={},
        caused_by=[]
    )
    log.append(event1)

    event2_valid = EvidenceEvent(
        event_id="e2",
        event_type=EvidenceEventType.NORMALIZATION_APPLIED,
        produced_at="2026-01-23T10:00:01Z",
        payload={},
        caused_by=["e1"]
    )
    log.append(event2_valid)

    event3_invalid = EvidenceEvent(
        event_id="e3",
        event_type=EvidenceEventType.STATE_TRANSITION,
        produced_at="2026-01-23T10:00:02Z",
        payload={},
        caused_by=["e99"]
    )

    with pytest.raises(ValueError, match="non-existent event_id"):
        log.append(event3_invalid)
