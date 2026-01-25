"""
RFC-06: Discrepancy Taxonomy - Diagnostic Rules Protocol

Defines the contract for versioned diagnostic rules.
Rules must be pure functions with no side-effects.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from core.discrepancy.v1.models import Discrepancy


class DiagnosticRule(Protocol):
    """
    Protocol for diagnostic rules (RFC-06 §3.2, §6).
    
    Rules MUST be pure functions:
    - No I/O operations
    - No reading system clock
    - No mutation of input data
    - Deterministic output for same inputs
    
    Rules SHOULD emit INSUFFICIENT_EVIDENCE when classification
    cannot be defended with available evidence (RFC-06 §3.4).
    """
    
    rule_id: str
    rule_version: str
    
    def evaluate(
        self,
        money_flow: dict[str, Any],
        money_state_evaluation: dict[str, Any],
    ) -> list[Discrepancy]:
        """
        Evaluate the rule against evidence to detect discrepancies.
        
        Args:
            money_flow: Money flow being diagnosed
            money_state_evaluation: State evaluation results
            
        Returns:
            List of detected discrepancies (may be empty)
            
        Raises:
            ValueError: If rule_id or rule_version is empty
            ValueError: If emitted discrepancy has invalid discrepancy_type
        """
        ...


class BaseDiagnosticRule(ABC):
    """
    Abstract base class for diagnostic rules.
    
    Provides common validation and template for rule implementation.
    """
    
    def __init__(self, rule_id: str, rule_version: str) -> None:
        """
        Initialize diagnostic rule.
        
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
    def evaluate(
        self,
        money_flow: dict[str, Any],
        money_state_evaluation: dict[str, Any],
    ) -> list[Discrepancy]:
        """
        Evaluate the rule against evidence to detect discrepancies.
        
        Implementation MUST:
        - Be deterministic
        - Not perform I/O
        - Not read system clock
        - Not mutate inputs
        - Set rule_id and rule_version on all emitted discrepancies
        - Only emit discrepancy_type values from the closed taxonomy
        
        Args:
            money_flow: Money flow being diagnosed
            money_state_evaluation: State evaluation results
            
        Returns:
            List of detected discrepancies (may be empty)
        """
        raise NotImplementedError


def validate_rule_output(discrepancies: list[Discrepancy], rule_id: str, rule_version: str) -> None:
    """
    Validate that rule output conforms to requirements.
    
    Args:
        discrepancies: List of discrepancies emitted by rule
        rule_id: Expected rule_id
        rule_version: Expected rule_version
        
    Raises:
        ValueError: If any discrepancy violates requirements
    """
    for disc in discrepancies:
        if not disc.rule_id:
            raise ValueError("Discrepancy emitted without rule_id")
        if not disc.rule_version:
            raise ValueError("Discrepancy emitted without rule_version")
        if disc.rule_id != rule_id:
            raise ValueError(
                f"Discrepancy rule_id '{disc.rule_id}' does not match "
                f"rule '{rule_id}'"
            )
        if disc.rule_version != rule_version:
            raise ValueError(
                f"Discrepancy rule_version '{disc.rule_version}' does not match "
                f"rule version '{rule_version}'"
            )
