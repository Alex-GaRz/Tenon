"""
RFC-06: Discrepancy Taxonomy - Discrepancy Detector

Pure function for detecting discrepancies: f(evidence, rules) -> discrepancies
"""

from typing import Any

from core.discrepancy.v1.models import Discrepancy
from core.discrepancy.v1.rules import DiagnosticRule


class DiscrepancyDetector:
    """
    Pure discrepancy detection engine (RFC-06).
    
    Applies diagnostic rules to evidence to detect discrepancies.
    All operations are deterministic and side-effect free.
    """
    
    def detect(
        self,
        money_flow: dict[str, Any],
        money_state_evaluation: dict[str, Any],
        rules: list[DiagnosticRule],
        detected_at: str,
    ) -> list[Discrepancy]:
        """
        Detect discrepancies by applying rules to evidence.
        
        PURE FUNCTION:
        - No I/O
        - No system clock access
        - No mutation of inputs
        - Deterministic output
        
        Args:
            money_flow: Money flow being diagnosed
            money_state_evaluation: State evaluation results
            rules: List of diagnostic rules to apply
            detected_at: Timestamp to assign to detected discrepancies (injected)
            
        Returns:
            Deterministically ordered list of discrepancies
            
        Raises:
            ValueError: If detected_at is empty
            ValueError: If any rule emits invalid discrepancy
        """
        if not detected_at:
            raise ValueError("detected_at cannot be empty")
        
        # Collect all discrepancies from all rules
        all_discrepancies: list[Discrepancy] = []
        
        for rule in rules:
            try:
                rule_discrepancies = rule.evaluate(money_flow, money_state_evaluation)
                
                # Validate and inject detected_at timestamp
                for disc in rule_discrepancies:
                    # Validate the discrepancy (lenient on rule_id for reconstruction)
                    
                    # Always inject the correct timestamp
                    disc_dict = disc.to_dict()
                    disc_dict["detected_at"] = detected_at
                    
                    # Validate rule_id/rule_version match
                    if disc.rule_id != rule.rule_id:
                        raise ValueError(
                            f"Discrepancy rule_id '{disc.rule_id}' does not match "
                            f"emitting rule '{rule.rule_id}'"
                        )
                    if disc.rule_version != rule.rule_version:
                        raise ValueError(
                            f"Discrepancy rule_version '{disc.rule_version}' does not match "
                            f"emitting rule version '{rule.rule_version}'"
                        )
                    
                    # Reconstruct with injected timestamp
                    disc = Discrepancy.from_dict(disc_dict)
                    all_discrepancies.append(disc)
                    
            except Exception as e:
                raise ValueError(
                    f"Rule {rule.rule_id} v{rule.rule_version} failed: {e}"
                ) from e
        
        # Return deterministically sorted discrepancies
        return self._sort_discrepancies(all_discrepancies)
    
    def _validate_discrepancy(self, disc: Discrepancy, rule: DiagnosticRule) -> None:
        """
        Validate that a discrepancy conforms to requirements.
        
        Args:
            disc: Discrepancy to validate
            rule: Rule that emitted the discrepancy
            
        Raises:
            ValueError: If validation fails
        """
        if disc.rule_id != rule.rule_id:
            raise ValueError(
                f"Discrepancy rule_id '{disc.rule_id}' does not match "
                f"emitting rule '{rule.rule_id}'"
            )
        if disc.rule_version != rule.rule_version:
            raise ValueError(
                f"Discrepancy rule_version '{disc.rule_version}' does not match "
                f"emitting rule version '{rule.rule_version}'"
            )
    
    def _sort_discrepancies(self, discrepancies: list[Discrepancy]) -> list[Discrepancy]:
        """
        Sort discrepancies deterministically for stable output.
        
        Sort order:
        1. discrepancy_type (alphabetically)
        2. rule_id (alphabetically)
        3. rule_version (alphabetically)
        4. discrepancy_id (alphabetically)
        
        Args:
            discrepancies: List of discrepancies to sort
            
        Returns:
            Sorted list of discrepancies
        """
        return sorted(
            discrepancies,
            key=lambda d: (
                d.discrepancy_type.value,
                d.rule_id,
                d.rule_version,
                d.discrepancy_id,
            )
        )
