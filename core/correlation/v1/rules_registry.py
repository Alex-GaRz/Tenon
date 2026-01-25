from typing import List
from .types import CorrelationRule

DEFAULT_RULESET_VERSION = "v1"
ENGINE_VERSION = "v1"


class RuleRegistry:
    def __init__(self, rules: List[CorrelationRule]) -> None:
        self._rules = sorted(rules, key=lambda r: (r.rule_id, r.rule_version))
    
    def list_rules(self) -> List[CorrelationRule]:
        return self._rules[:]  # Return copy to preserve order stability
    
    def get(self, rule_id: str, rule_version: str) -> CorrelationRule:
        for rule in self._rules:
            if rule.rule_id == rule_id and rule.rule_version == rule_version:
                return rule
        raise ValueError(f"Rule not found: {rule_id}@{rule_version}")