"""RFC-08 Event Sourcing Evidence - Evidence Log"""
from typing import Optional
from core.event_sourcing_evidence.v1.evidence_event import EvidenceEvent


class EvidenceLog:
    def __init__(self):
        self._events: list[tuple[int, EvidenceEvent]] = []
        self._next_sequence: int = 1
        self._last_produced_at: Optional[str] = None
        self._event_ids: set[str] = set()

    def append(self, event: EvidenceEvent) -> int:
        if self._last_produced_at is not None and event.produced_at < self._last_produced_at:
            raise ValueError(
                f"produced_at {event.produced_at} is before last event {self._last_produced_at}"
            )

        for caused_by_id in event.caused_by:
            if caused_by_id not in self._event_ids:
                raise ValueError(
                    f"caused_by references non-existent event_id: {caused_by_id}"
                )

        sequence_number = self._next_sequence
        self._events.append((sequence_number, event))
        self._next_sequence += 1
        self._last_produced_at = event.produced_at
        self._event_ids.add(event.event_id)

        return sequence_number

    def all(self) -> list[tuple[int, EvidenceEvent]]:
        return list(self._events)

    def at_or_before(self, iso_dt: str) -> list[tuple[int, EvidenceEvent]]:
        return [(seq, evt) for seq, evt in self._events if evt.produced_at <= iso_dt]
