"""RFC-08 Event Sourcing Evidence - Systemic Tests"""
import json
from pathlib import Path
from core.event_sourcing_evidence.v1.evidence_event import EvidenceEvent, EvidenceEventType
from core.event_sourcing_evidence.v1.evidence_log import EvidenceLog
from core.event_sourcing_evidence.v1.replay import replay_fingerprint


def load_fixture(filename: str) -> dict:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "rfc08_event_sourcing_evidence" / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def events_from_json(events_data: list) -> list[EvidenceEvent]:
    return [
        EvidenceEvent(
            event_id=e["event_id"],
            event_type=EvidenceEventType[e["event_type"]],
            produced_at=e["produced_at"],
            payload=e["payload"],
            caused_by=e["caused_by"]
        )
        for e in events_data
    ]


def test_systemic_linear_sequence_acceptance():
    """Linear sequence of events is accepted and ordered correctly"""
    log = EvidenceLog()
    fixture = load_fixture("scenario_months_history.json")
    events = events_from_json(fixture["events"])

    seq1 = log.append(events[0])
    seq2 = log.append(events[1])
    seq3 = log.append(events[2])

    assert seq1 == 1
    assert seq2 == 2
    assert seq3 == 3

    all_events = log.all()
    assert len(all_events) == 3
    assert all_events[0][1].event_id == "evt-001"
    assert all_events[1][1].event_id == "evt-002"
    assert all_events[2][1].event_id == "evt-003"


def test_systemic_causality_graph():
    """Events with multiple causal dependencies maintain integrity"""
    log = EvidenceLog()
    fixture = load_fixture("scenario_point_in_time.json")
    events = events_from_json(fixture["events"])

    log.append(events[0])
    log.append(events[1])
    log.append(events[2])

    all_events = log.all()
    assert len(all_events) == 3

    correlation_event = all_events[2][1]
    assert correlation_event.event_id == "evt-103"
    assert set(correlation_event.caused_by) == {"evt-101", "evt-102"}


def test_systemic_time_order_violation_rejected():
    """Event with timestamp before previous event is rejected"""
    log = EvidenceLog()
    
    event1 = EvidenceEvent(
        event_id="evt-201",
        event_type=EvidenceEventType.INGEST_RECEIVED,
        produced_at="2026-01-23T12:00:00Z",
        payload={},
        caused_by=[]
    )
    event2 = EvidenceEvent(
        event_id="evt-202",
        event_type=EvidenceEventType.NORMALIZATION_APPLIED,
        produced_at="2026-01-23T11:59:59Z",
        payload={},
        caused_by=["evt-201"]
    )

    log.append(event1)

    try:
        log.append(event2)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "before last event" in str(e)


def test_systemic_at_or_before_temporal_query():
    """at_or_before correctly filters events by timestamp"""
    log = EvidenceLog()
    fixture = load_fixture("scenario_point_in_time.json")
    events = events_from_json(fixture["events"])

    for event in events:
        log.append(event)

    cutoff = fixture["cutoff_produced_at"]
    filtered = log.at_or_before(cutoff)
    assert len(filtered) == 2
    assert filtered[0][1].event_id == "evt-101"
    assert filtered[1][1].event_id == "evt-102"


def test_systemic_replay_determinism():
    """Replay fingerprint is deterministic for same event sequence"""
    fixture = load_fixture("scenario_version_divergence.json")
    events = events_from_json(fixture["events"])
    
    version1 = fixture["engine_versions"][0]
    version2 = fixture["engine_versions"][1]

    fp1 = replay_fingerprint(version1, events)
    fp2 = replay_fingerprint(version1, events)

    assert fp1 == fp2

    fp_different_version = replay_fingerprint(version2, events)
    assert fp1 != fp_different_version


def test_systemic_full_lifecycle():
    """Full lifecycle: ingest, normalize, correlate, transition"""
    log = EvidenceLog()
    fixture = load_fixture("scenario_months_history.json")
    events = events_from_json(fixture["events"])

    for event in events:
        log.append(event)

    all_events = log.all()

    assert all_events[0][1].event_type.value == "INGEST_RECEIVED"
    assert all_events[1][1].event_type.value == "NORMALIZATION_APPLIED"
    assert all_events[2][1].event_type.value == "STATE_TRANSITION"

    assert all_events[1][1].caused_by == ["evt-001"]
    assert all_events[2][1].caused_by == ["evt-002"]

    fp = replay_fingerprint("v1.0.0", events)
    assert len(fp) == 64
