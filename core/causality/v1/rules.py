"""
RFC-07: Causality Model - Causal Rules Protocol

Defines the contract for versioned causal rules.
Rules must be pure functions with no side-effects.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from core.causality.v1.models import CausalityAttribution


class CausalRule(Protocol):
    """
    Protocol for causal attribution rules (RFC-07 §3.1, §6).
    
    Rules MUST be pure functions:
    - No I/O operations
    - No reading system clock
    - No mutation of input data
    - Deterministic output for same inputs
    
    Rules SHOULD emit UNKNOWN_CAUSE when causal attribution
    cannot be defended with available evidence (RFC-07 §8.2).
    
    Rules MUST NOT collapse multiple plausible causes into one.
    If multiple causes are plausible, emit multiple attributions.
    """
    
    rule_id: str
    rule_version: str
    
    def attribute(
        self,
        discrepancy: dict[str, Any],
        historical_evidence: dict[str, Any],
    ) -> list[CausalityAttribution]:
        """
        Attribute causality for a discrepancy based on historical evidence.
        
        Args:
            discrepancy: Discrepancy being investigated
            historical_evidence: Historical evidence available for attribution
            
        Returns:
            List of causal attributions (may be empty or multiple)
            
        Raises:
            ValueError: If rule_id or rule_version is empty
            ValueError: If emitted attribution has invalid cause_type
        """
        ...


class BaseCausalRule(ABC):
    """
    Abstract base class for causal attribution rules.
    
    Provides common validation and template for rule implementation.
    """
    
    def __init__(self, rule_id: str, rule_version: str) -> None:
        """
        Initialize causal rule.
        
        Args:
            rule_id: Unique identifier for this rule (non-empty)
            rule_version: Version of this rule (non-empty)
            
        Raises:
            ValueError: If rule_id or rule_version is empty
        """
        if not rule_id:
            raise ValueError("rule_id cannot be empty")
        if not rule_version:
            raise ValueError("rule_version cannot be empty")
        
        self.rule_id = rule_id
        self.rule_version = rule_version
    
    @abstractmethod
    def attribute(
        self,
        discrepancy: dict[str, Any],
        historical_evidence: dict[str, Any],
    ) -> list[CausalityAttribution]:
        """
        Attribute causality for a discrepancy based on historical evidence.
        
        Implementation MUST:
        - Be deterministic
        - Not perform I/O
        - Not read system clock
        - Not mutate inputs
        - Set model_version on all emitted attributions
        - Only emit cause_type values from the closed taxonomy
        - Not collapse multiple plausible causes (emit multiple if needed)
        - Emit UNKNOWN_CAUSE when evidence is weak/ambiguous
        
        Args:
            discrepancy: Discrepancy being investigated
            historical_evidence: Historical evidence available for attribution
            
        Returns:
            List of causal attributions (may be empty or multiple)
        """
        raise NotImplementedError


def validate_rule_output(
    attributions: list[CausalityAttribution],
    model_version: str,
) -> None:
    """
    Validate that rule output conforms to requirements.
    
    Args:
        attributions: List of attributions emitted by rule
        model_version: Expected model_version
        
    Raises:
        ValueError: If any attribution violates requirements
    """
    for attr in attributions:
        if not attr.model_version:
            raise ValueError("CausalityAttribution emitted without model_version")
        if attr.model_version != model_version:
            raise ValueError(
                f"CausalityAttribution model_version '{attr.model_version}' "
                f"does not match expected '{model_version}'"
            )
