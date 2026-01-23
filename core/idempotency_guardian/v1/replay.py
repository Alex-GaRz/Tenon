"""
RFC-10 Idempotency Guardian v1 - Replay
Replay idempotency decisions from WORM ledger.
"""

from typing import List
from .types import IdempotencyRecord, Decision, Scope
from .ports import WORMLedger, IdempotencyStore
from datetime import datetime


class ReplayEngine:
    """
    Replays idempotency decisions from WORM ledger.
    Ensures deterministic reconstruction of state.
    """
    
    def __init__(
        self,
        worm_ledger: WORMLedger,
        store: IdempotencyStore
    ):
        self.worm_ledger = worm_ledger
        self.store = store
    
    def replay_all(self) -> List[IdempotencyRecord]:
        """
        Replay all decisions from WORM ledger.
        Reconstructs idempotency store state deterministically.
        
        Returns:
            List of replayed records in order
        """
        entries = self.worm_ledger.get_all_entries()
        replayed_records = []
        
        for entry in entries:
            if entry.get("type") == "idempotency_check":
                record = self._reconstruct_record(entry)
                replayed_records.append(record)
        
        return replayed_records
    
    def _reconstruct_record(self, entry: dict) -> IdempotencyRecord:
        """
        Reconstruct IdempotencyRecord from WORM ledger entry.
        """
        # Parse timestamp
        timestamp = datetime.fromisoformat(entry["timestamp"])
        
        # Parse scope
        scope = Scope[entry["scope"]]
        
        # Parse decision
        decision = Decision[entry["decision"]]
        
        # Reconstruct record
        record = IdempotencyRecord(
            idempotency_record_id=entry.get("record_id", "replayed"),
            idempotency_key=entry["key"],
            scope=scope,
            decision=decision,
            first_seen_at=timestamp,
            decided_at=timestamp,
            evidence_refs=[],  # Evidence ref is the entry itself
            rule_version="1.0.0",
            notes="Replayed from WORM ledger"
        )
        
        return record
    
    def verify_determinism(self) -> bool:
        """
        Verify that replay produces deterministic results.
        Replays twice and compares outcomes.
        
        Returns:
            True if both replays produce identical results
        """
        first_replay = self.replay_all()
        second_replay = self.replay_all()
        
        if len(first_replay) != len(second_replay):
            return False
        
        for i, (first, second) in enumerate(zip(first_replay, second_replay)):
            if first.idempotency_key != second.idempotency_key:
                return False
            if first.decision != second.decision:
                return False
        
        return True
