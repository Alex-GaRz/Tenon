"""RFC-08 Event Sourcing Evidence - Replay Determinism"""
import hashlib
from core.event_sourcing_evidence.v1.evidence_event import EvidenceEvent


def replay_fingerprint(engine_version: str, events: list[EvidenceEvent]) -> str:
    event_ids = [event.event_id for event in events]
    fingerprint_input = engine_version + "|" + ";".join(event_ids)
    return hashlib.sha256(fingerprint_input.encode('utf-8')).hexdigest()
