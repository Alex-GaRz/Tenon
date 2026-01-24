"""RFC-09 Immutable Ledger WORM - Ledger Entry"""
import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class LedgerEntryType(Enum):
    EVIDENCE_SNAPSHOT = "EVIDENCE_SNAPSHOT"
    STATE_CHECKPOINT = "STATE_CHECKPOINT"
    AUDIT_RECORD = "AUDIT_RECORD"
    DISCREPANCY_LOG = "DISCREPANCY_LOG"


ISO8601_UTC_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$')


@dataclass(frozen=True)
class RetentionPolicy:
    retention_period: str
    immutable_until: str

    def __post_init__(self):
        if not ISO8601_UTC_PATTERN.match(self.immutable_until):
            raise ValueError(
                f"immutable_until must be ISO-8601 UTC format ending in Z: {self.immutable_until}"
            )


@dataclass(frozen=True)
class LedgerEntry:
    sequence_number: int
    entry_type: LedgerEntryType
    content: bytes
    content_hash: str
    written_at: str
    retention_policy: RetentionPolicy
    previous_entry_hash: str
    entry_header_hash: str

    def __post_init__(self):
        if not ISO8601_UTC_PATTERN.match(self.written_at):
            raise ValueError(
                f"written_at must be ISO-8601 UTC format ending in Z: {self.written_at}"
            )


def sha256_hex(data: bytes) -> str:
    """Compute SHA-256 hash of bytes and return as hex string"""
    return hashlib.sha256(data).hexdigest()
