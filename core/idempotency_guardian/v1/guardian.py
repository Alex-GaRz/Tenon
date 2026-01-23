"""
RFC-10 Idempotency Guardian v1 - Guardian
Core idempotency decision logic and execution gate.
"""

import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar
from .types import IdempotencyKey, IdempotencyRecord, Decision, Scope
from .ports import IdempotencyStore, WORMLedger


T = TypeVar('T')


class ExecutionGate:
    """
    Result of idempotency check.
    Contains decision and controls whether execution proceeds.
    """
    
    def __init__(self, decision: Decision, record: IdempotencyRecord):
        self.decision = decision
        self.record = record
    
    def should_execute(self) -> bool:
        """
        Determine if execution should proceed.
        ONLY ACCEPT_FIRST allows execution.
        """
        return self.decision == Decision.ACCEPT_FIRST


class Guardian:
    """
    Idempotency Guardian - ensures at-most-once execution.
    
    Operational model:
    1. Calculate deterministic key
    2. Decide WITHOUT executing effects
    3. Register append-only + evidence via WORM ledger
    4. Emit execution gate ONLY if ACCEPT_FIRST
    """
    
    RULE_VERSION = "1.0.0"
    
    def __init__(
        self,
        store: IdempotencyStore,
        worm_ledger: WORMLedger
    ):
        self.store = store
        self.worm_ledger = worm_ledger
    
    def check(self, idempotency_key: IdempotencyKey) -> ExecutionGate:
        """
        Check idempotency and return execution gate.
        
        Args:
            idempotency_key: The deterministic key to check
        
        Returns:
            ExecutionGate with decision
        """
        now = datetime.utcnow()
        
        # Check for existing record
        existing = self.store.find_by_key(idempotency_key.key)
        
        if existing is None:
            # First observation - ACCEPT
            decision = Decision.ACCEPT_FIRST
            first_seen_at = now
            notes = None
        else:
            # Key exists - check for ambiguity
            # Parse fingerprint from existing record notes
            existing_fingerprint = self._parse_fingerprint(existing.notes)
            current_fingerprint = self._build_fingerprint(idempotency_key)
            
            if existing_fingerprint != current_fingerprint:
                # Same key, different fingerprint - AMBIGUOUS
                decision = Decision.FLAG_AMBIGUOUS
                notes = f"Ambiguous: fingerprint mismatch. Expected: {existing_fingerprint}, Got: {current_fingerprint}"
            else:
                # Same key, same fingerprint - REJECT DUPLICATE
                decision = Decision.REJECT_DUPLICATE
                notes = None
            
            first_seen_at = existing.first_seen_at
        
        # Append to WORM ledger for evidence
        evidence_entry = {
            "type": "idempotency_check",
            "key": idempotency_key.key,
            "scope": idempotency_key.scope.value,
            "principal": idempotency_key.principal,
            "subject": idempotency_key.subject,
            "payload_hash": idempotency_key.payload_hash,
            "decision": decision.value,
            "timestamp": now.isoformat()
        }
        evidence_ref = self.worm_ledger.append_entry(evidence_entry)
        
        # Build fingerprint for storage
        if decision == Decision.ACCEPT_FIRST:
            fingerprint = self._build_fingerprint(idempotency_key)
            notes = f"fingerprint:{fingerprint}"
        
        # Create record
        record = IdempotencyRecord(
            idempotency_record_id=str(uuid.uuid4()),
            idempotency_key=idempotency_key.key,
            scope=idempotency_key.scope,
            decision=decision,
            first_seen_at=first_seen_at,
            decided_at=now,
            evidence_refs=[evidence_ref],
            rule_version=self.RULE_VERSION,
            notes=notes
        )
        
        # Append to store (append-only: ALL decisions, not just ACCEPT_FIRST)
        self.store.append(record)
        
        return ExecutionGate(decision, record)
    
    def _build_fingerprint(self, key: IdempotencyKey) -> str:
        """Build fingerprint from key components."""
        return f"{key.scope.value}|{key.principal}|{key.subject}|{key.payload_hash}|{key.version}"
    
    def _parse_fingerprint(self, notes: Optional[str]) -> str:
        """Parse fingerprint from notes field."""
        if notes and notes.startswith("fingerprint:"):
            return notes.split("fingerprint:", 1)[1]
        return ""
    
    def guard(
        self,
        idempotency_key: IdempotencyKey,
        operation: Callable[[], T]
    ) -> Optional[T]:
        """
        Guard an operation with idempotency check.
        Execute operation ONLY if ACCEPT_FIRST.
        
        Args:
            idempotency_key: The deterministic key
            operation: Function to execute if allowed
        
        Returns:
            Result of operation if executed, None otherwise
        """
        gate = self.check(idempotency_key)
        
        if gate.should_execute():
            return operation()
        else:
            return None
