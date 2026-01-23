"""
RFC-10 Test Support - In-Memory WORM Ledger
Simulated append-only ledger for testing.
"""

from typing import List, Dict
import uuid
from core.idempotency_guardian.v1.ports import WORMLedger


class InMemoryWORMLedger(WORMLedger):
    """
    In-memory WORM (Write-Once-Read-Many) ledger for testing.
    Simulates append-only behavior.
    """
    
    def __init__(self):
        self._entries: List[Dict] = []
        self._entry_map: Dict[str, Dict] = {}
    
    def append_entry(self, entry_data: dict) -> str:
        """
        Append entry to ledger.
        Returns reference to entry.
        """
        # Generate reference
        reference = f"worm-{uuid.uuid4()}"
        
        # Store with reference
        entry_with_ref = {
            "reference": reference,
            **entry_data
        }
        
        self._entries.append(entry_with_ref)
        self._entry_map[reference] = entry_with_ref
        
        return reference
    
    def get_entry(self, reference: str) -> dict:
        """Retrieve entry by reference."""
        if reference not in self._entry_map:
            raise KeyError(f"Entry not found: {reference}")
        return self._entry_map[reference]
    
    def get_all_entries(self) -> List[dict]:
        """Retrieve all entries in append order."""
        return list(self._entries)
    
    def count(self) -> int:
        """Count total entries."""
        return len(self._entries)
