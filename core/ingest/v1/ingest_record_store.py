"""
RFC-02 Ingest Record Store: Append-only storage for ingest records.

GUARANTEES:
- Append-only: no update, no delete, no upsert
- Monotonicity: record count only increases
- Queryable by raw_payload_hash for duplicate detection
"""

from typing import List, Dict, Any


class IngestRecordStore:
    """Append-only in-memory store for ingest records."""
    
    def __init__(self):
        """Initialize empty store."""
        # All records in append order
        self._records: List[Dict[str, Any]] = []
        
        # Index: raw_payload_hash -> list of ingest_ids
        self._hash_index: Dict[str, List[str]] = {}
    
    def append(self, record: Dict[str, Any]) -> None:
        """
        Append ingest record to store.
        
        Args:
            record: IngestRecord conforming to schema
        
        Invariants:
            - Record is immutable after append
            - No duplicates prevented (append-only semantics)
            - Hash index maintained for queries
        """
        # Append to main store
        self._records.append(record)
        
        # Update hash index
        raw_payload_hash = record["raw_payload_hash"]
        if raw_payload_hash not in self._hash_index:
            self._hash_index[raw_payload_hash] = []
        self._hash_index[raw_payload_hash].append(record["ingest_id"])
    
    def scan_by_raw_payload_hash(self, raw_payload_hash: str) -> List[Dict[str, Any]]:
        """
        Retrieve all ingest records for a given raw payload hash.
        
        Args:
            raw_payload_hash: SHA-256 hash of raw payload
        
        Returns:
            List of IngestRecord dicts (may be empty)
        
        Usage:
            Used for duplicate detection and replay analysis
        """
        if raw_payload_hash not in self._hash_index:
            return []
        
        ingest_ids = self._hash_index[raw_payload_hash]
        
        # Linear scan (acceptable for in-memory store)
        return [r for r in self._records if r["ingest_id"] in ingest_ids]
    
    def count(self) -> int:
        """Return total count of records (for testing monotonicity)."""
        return len(self._records)
    
    def all_records(self) -> List[Dict[str, Any]]:
        """Return all records in append order (for testing)."""
        return list(self._records)
