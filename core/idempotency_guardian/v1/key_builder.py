"""
RFC-10 Idempotency Guardian v1 - Key Builder
Deterministic construction of idempotency keys.
"""

import hashlib
import json
from typing import Any, Dict, Callable, Optional
from .types import IdempotencyKey, Scope


class KeyBuilder:
    """
    Builds deterministic idempotency keys.
    Ensures same inputs always produce same key.
    """

    def __init__(self, scope: Scope, hash_fn: Optional[Callable[[str], str]] = None):
        self.scope = scope
        self._hash_fn = hash_fn  # For testing: inject controlled hash function

    def build(
        self,
        principal: str,
        subject: str,
        payload: Dict[str, Any]
    ) -> IdempotencyKey:
        """
        Build deterministic key from inputs.
        
        Args:
            principal: Identity initiating the operation
            subject: Entity being operated upon
            payload: Operation payload (must be JSON-serializable)
        
        Returns:
            IdempotencyKey with deterministic key field
        """
        payload_hash = self._hash_payload(payload)
        
        # Deterministic key construction
        key_components = [
            self.scope.value,
            principal,
            subject,
            payload_hash
        ]
        
        key_string = "|".join(key_components)
        deterministic_key = self._hash_string(key_string)
        
        return IdempotencyKey(
            key=deterministic_key,
            scope=self.scope,
            principal=principal,
            subject=subject,
            payload_hash=payload_hash,
            version="1.0.0"
        )

    def _hash_payload(self, payload: Dict[str, Any]) -> str:
        """
        Create deterministic hash of payload.
        Uses sorted JSON serialization for consistency.
        """
        # Sort keys for deterministic serialization
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return self._hash_string(payload_json)

    def _hash_string(self, value: str) -> str:
        """
        Hash string to fixed-length digest.
        """
        if self._hash_fn is not None:
            # Use injected hash function (for testing)
            return self._hash_fn(value)
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
