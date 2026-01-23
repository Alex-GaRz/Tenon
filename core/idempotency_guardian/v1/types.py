"""
RFC-10 Idempotency Guardian v1 - Types
Defines core types for idempotency decisions.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Scope(Enum):
    """Scope of idempotency check."""
    INGEST = "INGEST"
    CANONICALIZE = "CANONICALIZE"
    EVIDENCE_WRITE = "EVIDENCE_WRITE"


class Decision(Enum):
    """Idempotency decision."""
    ACCEPT_FIRST = "ACCEPT_FIRST"
    REJECT_DUPLICATE = "REJECT_DUPLICATE"
    FLAG_AMBIGUOUS = "FLAG_AMBIGUOUS"


@dataclass(frozen=True)
class IdempotencyKey:
    """
    Deterministic key for idempotency decision.
    Immutable after construction.
    """
    key: str
    scope: Scope
    principal: str
    subject: str
    payload_hash: str
    version: str = "1.0.0"


@dataclass(frozen=True)
class IdempotencyRecord:
    """
    Append-only record of idempotency decision.
    Immutable after construction.
    """
    idempotency_record_id: str
    idempotency_key: str
    scope: Scope
    decision: Decision
    first_seen_at: datetime
    decided_at: datetime
    evidence_refs: List[str]
    rule_version: str
    notes: Optional[str] = None
