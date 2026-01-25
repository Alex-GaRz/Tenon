"""
RFC-07: Causality Model - WORM Store

Append-only storage for causal attributions with no update or delete operations.
"""

from typing import Optional

from core.causality.v1.models import CausalityAttribution


class AppendOnlyCausalityStore:
    """
    WORM (Write-Once-Read-Many) store for causal attributions (RFC-07).
    
    ALLOWED operations:
    - append: Add new attribution (never overwrites)
    - get: Retrieve by causality_id
    - list_by_discrepancy: Retrieve all for a discrepancy_id
    - iter_all: Iterate all attributions (audit/test)
    
    FORBIDDEN operations (violations will raise):
    - update, delete, upsert, replace, clear, truncate
    
    Multiple attributions for the same discrepancy are preserved (no collapse).
    """
    
    def __init__(self) -> None:
        """Initialize empty store."""
        self._attributions: dict[str, CausalityAttribution] = {}
        self._by_discrepancy: dict[str, list[str]] = {}
    
    def append(self, attribution: CausalityAttribution) -> None:
        """
        Append a new causal attribution (WORM - never overwrites).
        
        Args:
            attribution: CausalityAttribution to append
            
        Raises:
            ValueError: If causality_id already exists (WORM violation)
            ValueError: If attribution is invalid
        """
        if not isinstance(attribution, CausalityAttribution):
            raise ValueError(
                f"Expected CausalityAttribution instance, got {type(attribution)}"
            )
        
        causality_id = attribution.causality_id
        
        # WORM enforcement: never overwrite
        if causality_id in self._attributions:
            raise ValueError(
                f"WORM violation: causality_id '{causality_id}' already exists. "
                f"Cannot overwrite existing attribution."
            )
        
        # Store the attribution
        self._attributions[causality_id] = attribution
        
        # Index by discrepancy_id
        discrepancy_id = attribution.discrepancy_id
        if discrepancy_id not in self._by_discrepancy:
            self._by_discrepancy[discrepancy_id] = []
        self._by_discrepancy[discrepancy_id].append(causality_id)
    
    def get(self, causality_id: str) -> Optional[CausalityAttribution]:
        """
        Retrieve a causal attribution by ID.
        
        Args:
            causality_id: Causality attribution identifier
            
        Returns:
            CausalityAttribution if found, None otherwise
        """
        return self._attributions.get(causality_id)
    
    def list_by_discrepancy(self, discrepancy_id: str) -> list[CausalityAttribution]:
        """
        Retrieve all causal attributions for a given discrepancy.
        
        Multiple attributions may exist for the same discrepancy.
        
        Args:
            discrepancy_id: Discrepancy identifier
            
        Returns:
            List of causal attributions (may be empty)
        """
        causality_ids = self._by_discrepancy.get(discrepancy_id, [])
        return [self._attributions[cid] for cid in causality_ids]
    
    def iter_all(self) -> list[CausalityAttribution]:
        """
        Iterate all causal attributions in the store.
        
        Used for auditing and testing.
        
        Returns:
            List of all causal attributions
        """
        return list(self._attributions.values())
    
    def __len__(self) -> int:
        """Return number of causal attributions in store."""
        return len(self._attributions)
