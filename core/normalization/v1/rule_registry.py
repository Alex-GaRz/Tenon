"""
RFC-03 Rule Registry: Deterministic normalization rule selection.

GUARANTEES:
- Exact matching only (no fallback magic)
- Deterministic: same signature → same rule
- No external APIs, no randomness
"""

from typing import Dict, Any, Optional, Tuple


class RuleRegistry:
    """Registry for normalization rules with exact matching."""
    
    def __init__(self):
        """Initialize empty registry."""
        # (source_system, raw_format, schema_hint) -> NormalizationRule
        self._rules: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    
    def register(self, rule: Dict[str, Any]) -> None:
        """
        Register a normalization rule.
        
        Args:
            rule: NormalizationRule conforming to schema
        
        Invariants:
            - Exact signature match required
            - No partial/fuzzy matching
        """
        sig = rule["input_signature"]
        key = (sig["source_system"], sig["raw_format"], sig["schema_hint"])
        
        # Overwrites previous rule for same signature (versioning handled externally)
        self._rules[key] = rule
    
    def get_rule(
        self,
        source_system: str,
        raw_format: str,
        schema_hint: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve normalization rule by exact signature match.
        
        Args:
            source_system: Source system identifier
            raw_format: Raw format (json/csv/etc)
            schema_hint: Schema version or type hint
        
        Returns:
            NormalizationRule or None if no exact match
        
        Invariants:
            - EXACT match required (all 3 fields)
            - No fallback to partial matches
            - Deterministic
        """
        key = (source_system, raw_format, schema_hint)
        return self._rules.get(key)
    
    def count(self) -> int:
        """Return count of registered rules (for testing)."""
        return len(self._rules)
