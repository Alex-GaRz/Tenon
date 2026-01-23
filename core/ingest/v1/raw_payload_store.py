"""
RFC-02 Raw Payload Store: Append-only immutable storage for raw observation bytes.

GUARANTEES:
- Append-only: no update, no delete
- Deterministic: same bytes → same hash → same pointer
- Idempotent: duplicate append returns existing pointer
"""

import hashlib
from typing import Dict, Tuple


class RawPayloadStore:
    """Append-only in-memory store for raw payload bytes."""
    
    def __init__(self):
        """Initialize empty store."""
        # hash -> (raw_bytes, raw_format)
        self._payloads: Dict[str, Tuple[bytes, str]] = {}
    
    def append(self, raw_bytes: bytes, *, raw_format: str) -> Tuple[str, str, int]:
        """
        Append raw payload to store (idempotent).
        
        Args:
            raw_bytes: Raw observation bytes
            raw_format: Format identifier (json/csv/pdf/etc)
        
        Returns:
            Tuple of (raw_payload_hash, raw_pointer, raw_size_bytes)
        
        Invariants:
            - Same bytes → same hash → same pointer
            - No overwrites: duplicate hash reuses existing entry
        """
        raw_payload_hash = hashlib.sha256(raw_bytes).hexdigest()
        raw_size_bytes = len(raw_bytes)
        
        # Idempotent: if already exists, return existing pointer
        if raw_payload_hash not in self._payloads:
            self._payloads[raw_payload_hash] = (raw_bytes, raw_format)
        
        # Pointer is hash (opaque but deterministic)
        raw_pointer = f"raw:{raw_payload_hash}"
        
        return (raw_payload_hash, raw_pointer, raw_size_bytes)
    
    def get(self, raw_pointer: str) -> bytes:
        """
        Retrieve raw payload by pointer.
        
        Args:
            raw_pointer: Opaque pointer returned by append()
        
        Returns:
            Raw payload bytes
        
        Raises:
            KeyError: If pointer not found
        """
        # Extract hash from pointer
        if not raw_pointer.startswith("raw:"):
            raise ValueError(f"Invalid raw_pointer format: {raw_pointer}")
        
        raw_hash = raw_pointer[4:]  # strip "raw:" prefix
        
        if raw_hash not in self._payloads:
            raise KeyError(f"Raw payload not found: {raw_pointer}")
        
        raw_bytes, _ = self._payloads[raw_hash]
        return raw_bytes
    
    def count(self) -> int:
        """Return count of unique payloads (for testing monotonicity)."""
        return len(self._payloads)
