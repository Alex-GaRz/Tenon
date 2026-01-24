"""RFC-08 Event Sourcing Evidence - Evidence Event"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvidenceEventType(Enum):
    INGEST_RECEIVED = "INGEST_RECEIVED"
    NORMALIZATION_APPLIED = "NORMALIZATION_APPLIED"
    CORRELATION_MATCH = "CORRELATION_MATCH"
    STATE_TRANSITION = "STATE_TRANSITION"
    DISCREPANCY_DETECTED = "DISCREPANCY_DETECTED"
    AUDIT_CHECKPOINT = "AUDIT_CHECKPOINT"


ISO8601_UTC_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$')


@dataclass(frozen=True)
class EvidenceEvent:
    event_id: str
    event_type: EvidenceEventType
    produced_at: str
    payload: dict[str, Any]
    caused_by: list[str]

    def __post_init__(self):
        if not ISO8601_UTC_PATTERN.match(self.produced_at):
            raise ValueError(
                f"produced_at must be ISO-8601 UTC format ending in Z: {self.produced_at}"
            )
