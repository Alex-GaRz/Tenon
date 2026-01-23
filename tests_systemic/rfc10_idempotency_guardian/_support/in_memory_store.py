"""
RFC-10 Test Support - In-Memory Idempotency Store
Append-only in-memory implementation for testing.
"""

from typing import Optional, Dict, List
from core.idempotency_guardian.v1.types import IdempotencyRecord
from core.idempotency_guardian.v1.ports import IdempotencyStore


class InMemoryIdempotencyStore(IdempotencyStore):
    """
    In-memory append-only store for testing.
    Thread-safe for basic concurrent testing.
    Stores ALL decisions (ACCEPT_FIRST, REJECT_DUPLICATE, FLAG_AMBIGUOUS).
    """
    
    def __init__(self):
        self._records_by_key: Dict[str, List[IdempotencyRecord]] = {}
        self._append_log = []  # For audit trail (all records in order)
    
    def find_by_key(self, key: str) -> Optional[IdempotencyRecord]:
        """
        Find first (original) record by key.
        Returns the ACCEPT_FIRST record if it exists, else None.
        """
        records = self._records_by_key.get(key, [])
        if not records:
            return None
        # Return first record (should be ACCEPT_FIRST if it exists)
        return records[0]
    
    def append(self, record: IdempotencyRecord) -> None:
        """
        Append new record (append-only).
        Never raises on duplicate key - always appends.
        """
        if record.idempotency_key not in self._records_by_key:
            self._records_by_key[record.idempotency_key] = []
        
        self._records_by_key[record.idempotency_key].append(record)
        self._append_log.append(record)
    
    def get_all_records(self):
        """Get all records in append order (for testing)."""
        return list(self._append_log)
    
    def count(self) -> int:
        """Count total records (all appended records)."""
        return len(self._append_log)
