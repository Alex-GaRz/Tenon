"""
RFC-06: Discrepancy Taxonomy - WORM Store

Append-only storage for discrepancies with no update or delete operations.
"""

from typing import Optional

from core.discrepancy.v1.models import Discrepancy


class AppendOnlyDiscrepancyStore:
    """
    WORM (Write-Once-Read-Many) store for discrepancies (RFC-06).
    
    ALLOWED operations:
    - append: Add new discrepancy (never overwrites)
    - get: Retrieve by discrepancy_id
    - list_by_flow: Retrieve all for a flow_id
    - iter_all: Iterate all discrepancies (audit/test)
    
    FORBIDDEN operations (violations will raise):
    - update, delete, upsert, replace, clear, truncate
    """
    
    def __init__(self) -> None:
        """Initialize empty store."""
        self._discrepancies: dict[str, Discrepancy] = {}
        self._by_flow: dict[str, list[str]] = {}
    
    def append(self, discrepancy: Discrepancy) -> None:
        """
        Append a new discrepancy (WORM - never overwrites).
        
        Args:
            discrepancy: Discrepancy to append
            
        Raises:
            ValueError: If discrepancy_id already exists (WORM violation)
            ValueError: If discrepancy is invalid
        """
        if not isinstance(discrepancy, Discrepancy):
            raise ValueError(
                f"Expected Discrepancy instance, got {type(discrepancy)}"
            )
        
        discrepancy_id = discrepancy.discrepancy_id
        
        # WORM enforcement: never overwrite
        if discrepancy_id in self._discrepancies:
            raise ValueError(
                f"WORM violation: discrepancy_id '{discrepancy_id}' already exists. "
                f"Cannot overwrite existing discrepancy."
            )
        
        # Store the discrepancy
        self._discrepancies[discrepancy_id] = discrepancy
        
        # Index by flow_id
        flow_id = discrepancy.flow_id
        if flow_id not in self._by_flow:
            self._by_flow[flow_id] = []
        self._by_flow[flow_id].append(discrepancy_id)
    
    def get(self, discrepancy_id: str) -> Optional[Discrepancy]:
        """
        Retrieve a discrepancy by ID.
        
        Args:
            discrepancy_id: Discrepancy identifier
            
        Returns:
            Discrepancy if found, None otherwise
        """
        return self._discrepancies.get(discrepancy_id)
    
    def list_by_flow(self, flow_id: str) -> list[Discrepancy]:
        """
        Retrieve all discrepancies for a given flow.
        
        Args:
            flow_id: Money flow identifier
            
        Returns:
            List of discrepancies (may be empty)
        """
        discrepancy_ids = self._by_flow.get(flow_id, [])
        return [self._discrepancies[did] for did in discrepancy_ids]
    
    def iter_all(self) -> list[Discrepancy]:
        """
        Iterate all discrepancies in the store.
        
        Used for auditing and testing.
        
        Returns:
            List of all discrepancies
        """
        return list(self._discrepancies.values())
    
    def __len__(self) -> int:
        """Return number of discrepancies in store."""
        return len(self._discrepancies)
