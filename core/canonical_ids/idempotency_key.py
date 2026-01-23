"""
Idempotency key derivation.
RFC-01A implementation.

Derives deterministic idempotency keys from canonical event fields.
Ensures: same input fields + same version → same key.
"""

import hashlib
import json
from typing import Dict, Any, List


class IdempotencyKeyGenerator:
    """Generates deterministic idempotency keys for canonical events."""
    
    # ACTUALIZADO: Se incluyen versiones para que afecten la identidad
    KEY_FIELDS_PRIORITY = [
        "source_event_id",
        "external_reference",
        "source_system",
        "source_timestamp",
        "observed_at",
        "amount",
        "currency",
        "direction",
        "event_type",
        "normalizer_version",        # Nuevo
        "adapter_version",           # Nuevo
        "schema_version",            # Nuevo
        "_canonicalization_context"  # Nuevo (usado por el test)
    ]
    
    def __init__(self, version: str = "1.0.0"):
        """
        Initialize idempotency key generator.
        
        Args:
            version: Version of the key generation algorithm
        """
        self.version = version
    
    def generate(self, event: Dict[str, Any]) -> str:
        """
        Generate deterministic idempotency key from event.
        
        Priority order:
        1. If source_event_id exists and is unique: use it as primary component
        2. Otherwise use external_reference + source_system
        3. Fall back to hash of core fields
        
        Args:
            event: Canonical event dictionary
        
        Returns:
            Deterministic idempotency key (string)
        """
        # Extract key components in deterministic order
        components = []
        
        for field in self.KEY_FIELDS_PRIORITY:
            value = event.get(field)
            if value is not None:
                # Normalize value to string deterministically
                if isinstance(value, float):
                    # Normalize float to stable decimal representation
                    normalized = format(value, ".10f").rstrip("0").rstrip(".")
                    components.append(f"{field}:{normalized}")
                elif isinstance(value, int):
                    components.append(f"{field}:{value}")
                else:
                    # Strip whitespace from strings
                    normalized_str = str(value).strip()
                    components.append(f"{field}:{normalized_str}")
        
        # Create deterministic string representation
        key_string = "|".join(components)
        
        # Hash to fixed-length key
        key_hash = hashlib.sha256(key_string.encode("utf-8")).hexdigest()
        
        # Include version in key to ensure reproducibility
        return f"v{self.version}:{key_hash}"
    
    def extract_components(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key components from event (for debugging/evidence).
        
        Args:
            event: Canonical event dictionary
        
        Returns:
            Dictionary of extracted key components
        """
        components = {}
        for field in self.KEY_FIELDS_PRIORITY:
            value = event.get(field)
            if value is not None:
                components[field] = value
        return components
