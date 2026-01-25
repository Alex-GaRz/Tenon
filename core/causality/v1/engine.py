"""
RFC-07: Causality Model - Causality Engine

Pure function for causal attribution: f(discrepancy, evidence, rules) -> attributions
"""

from typing import Any

from core.causality.v1.models import CausalityAttribution
from core.causality.v1.enums import CausalityType
from core.causality.v1.rules import CausalRule


class CausalityEngine:
    """
    Pure causality attribution engine (RFC-07).
    
    Applies causal rules to discrepancies and evidence to generate attributions.
    All operations are deterministic and side-effect free.
    
    MAY emit multiple attributions for the same discrepancy (no forced uniqueness).
    """
    
    def attribute(
        self,
        discrepancy: dict[str, Any],
        historical_evidence: dict[str, Any],
        rules: list[CausalRule],
        attributed_at: str,
        model_version: str,
    ) -> list[CausalityAttribution]:
        """
        Attribute causality for a discrepancy.
        
        PURE FUNCTION:
        - No I/O
        - No system clock access
        - No mutation of inputs
        - Deterministic output
        
        CONSERVATISM:
        - If no rules produce defendable cause => emit UNKNOWN_CAUSE
        - Multiple plausible causes are preserved (not collapsed)
        
        Args:
            discrepancy: Discrepancy being investigated
            historical_evidence: Historical evidence for attribution
            rules: List of causal rules to apply
            attributed_at: Timestamp to assign (injected externally)
            model_version: Version of the causality model
            
        Returns:
            Deterministically ordered list of causal attributions
            
        Raises:
            ValueError: If attributed_at or model_version is empty
            ValueError: If any rule emits invalid attribution
        """
        if not attributed_at:
            raise ValueError("attributed_at cannot be empty")
        if not model_version:
            raise ValueError("model_version cannot be empty")
        
        discrepancy_id = discrepancy.get("discrepancy_id", "unknown")
        
        # Collect all attributions from all rules
        all_attributions: list[CausalityAttribution] = []
        
        for rule in rules:
            try:
                rule_attributions = rule.attribute(discrepancy, historical_evidence)
                
                # Validate and inject metadata
                for attr in rule_attributions:
                    self._validate_attribution(attr, model_version)
                    
                    # Inject attributed_at and model_version if needed
                    if attr.attributed_at != attributed_at or attr.model_version != model_version:
                        attr_dict = attr.to_dict()
                        attr_dict["attributed_at"] = attributed_at
                        attr_dict["model_version"] = model_version
                        attr = CausalityAttribution.from_dict(attr_dict)
                    
                    all_attributions.append(attr)
                    
            except Exception as e:
                raise ValueError(
                    f"Rule {rule.rule_id} v{rule.rule_version} failed: {e}"
                ) from e
        
        # Conservative fallback: if no attributions, emit UNKNOWN_CAUSE
        if not all_attributions:
            all_attributions = [self._create_unknown_cause(
                discrepancy_id,
                attributed_at,
                model_version,
            )]
        
        # Return deterministically sorted attributions
        return self._sort_attributions(all_attributions)
    
    def _validate_attribution(
        self,
        attr: CausalityAttribution,
        model_version: str,
    ) -> None:
        """
        Validate that an attribution conforms to requirements.
        
        Args:
            attr: Attribution to validate
            model_version: Expected model version
            
        Raises:
            ValueError: If validation fails
        """
        # Model version check is lenient here (will be injected if different)
        # Main validation happens in CausalityAttribution.__post_init__
        pass
    
    def _create_unknown_cause(
        self,
        discrepancy_id: str,
        attributed_at: str,
        model_version: str,
    ) -> CausalityAttribution:
        """
        Create UNKNOWN_CAUSE attribution for conservative fallback.
        
        Args:
            discrepancy_id: Discrepancy identifier
            attributed_at: Attribution timestamp
            model_version: Model version
            
        Returns:
            CausalityAttribution with UNKNOWN_CAUSE
        """
        return CausalityAttribution(
            causality_id=f"cause-unknown-{discrepancy_id}",
            discrepancy_id=discrepancy_id,
            cause_type=CausalityType.UNKNOWN_CAUSE,
            confidence_level=0.0,
            supporting_rules=["causality-engine-fallback"],
            explanation="No causal rule produced defendable attribution with available evidence",
            attributed_at=attributed_at,
            model_version=model_version,
        )
    
    def _sort_attributions(
        self,
        attributions: list[CausalityAttribution],
    ) -> list[CausalityAttribution]:
        """
        Sort attributions deterministically for stable output.
        
        Sort order:
        1. cause_type (alphabetically)
        2. confidence_level (descending)
        3. causality_id (alphabetically)
        
        Args:
            attributions: List of attributions to sort
            
        Returns:
            Sorted list of attributions
        """
        return sorted(
            attributions,
            key=lambda a: (
                a.cause_type.value,
                -a.confidence_level,  # Descending confidence
                a.causality_id,
            )
        )
