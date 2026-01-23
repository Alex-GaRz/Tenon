"""
RFC-03 Diff Store: Append-only storage for raw→canonical diffs.

GUARANTEES:
- Append-only: no update, no delete
- Opaque stable diff_reference per insert
- Deterministic retrieval
"""

import uuid
from typing import Dict, Any


class DiffStore:
    """Append-only in-memory store for diff documents."""
    
    def __init__(self):
        """Initialize empty store."""
        # diff_reference -> diff_document
        self._diffs: Dict[str, Dict[str, Any]] = {}
    
    def append(self, diff_document: Dict[str, Any]) -> str:
        """
        Append diff document to store.
        
        Args:
            diff_document: Diff conforming to raw_to_canon_diff.schema.json
        
        Returns:
            Opaque stable diff_reference (string)
        
        Invariants:
            - diff_reference is unique and stable
            - No overwrites
        """
        # Generate opaque stable reference
        diff_reference = f"diff:{uuid.uuid4()}"
        
        # Store (no duplicates check for simplicity; each append gets unique ref)
        self._diffs[diff_reference] = diff_document
        
        return diff_reference
    
    def get(self, diff_reference: str) -> Dict[str, Any]:
        """
        Retrieve diff document by reference.
        
        Args:
            diff_reference: Opaque reference returned by append()
        
        Returns:
            Diff document dict
        
        Raises:
            KeyError: If reference not found
        """
        if diff_reference not in self._diffs:
            raise KeyError(f"Diff not found: {diff_reference}")
        
        return self._diffs[diff_reference]
    
    def count(self) -> int:
        """Return count of diffs (for testing monotonicity)."""
        return len(self._diffs)
