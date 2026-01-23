"""
RFC-10 Idempotency Guardian v1 - Ports
Defines port interfaces for external dependencies.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from .types import IdempotencyKey, IdempotencyRecord


class IdempotencyStore(ABC):
    """
    Port for storing and retrieving idempotency records.
    Append-only semantics.
    """

    @abstractmethod
    def find_by_key(self, key: str) -> Optional[IdempotencyRecord]:
        """
        Find existing record by idempotency key.
        Returns None if not found.
        """
        pass

    @abstractmethod
    def append(self, record: IdempotencyRecord) -> None:
        """
        Append new record to store.
        Must not modify existing records.
        """
        pass


class WORMLedger(ABC):
    """
    Port for WORM (Write-Once-Read-Many) ledger.
    Used for evidence references.
    """

    @abstractmethod
    def append_entry(self, entry_data: dict) -> str:
        """
        Append entry to WORM ledger.
        Returns reference to the entry.
        """
        pass

    @abstractmethod
    def get_entry(self, reference: str) -> dict:
        """
        Retrieve entry by reference.
        """
        pass

    @abstractmethod
    def get_all_entries(self) -> List[dict]:
        """
        Retrieve all entries in order.
        For replay purposes.
        """
        pass
