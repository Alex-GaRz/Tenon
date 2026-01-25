from dataclasses import dataclass
from typing import List

# Enum EXACTO con orden estable
MONEY_STATES = (
    "EXPECTED",
    "INITIATED", 
    "AUTHORIZED",
    "IN_TRANSIT",
    "SETTLED",
    "REFUNDED",
    "REVERSED",
    "FAILED",
    "EXPIRED",
    "AMBIGUOUS",
    "UNKNOWN"
)


@dataclass(frozen=True)
class MoneyStateEvaluation:
    evaluation_id: str
    flow_id: str
    event_id: str
    timestamp: str
    state: str
    transition_reason: str
    evidence_pointer: str
    state_version: str
    machine_version: str
    confidence_level: float
    evaluated_at: str


@dataclass(frozen=True)
class TransitionRule:
    from_state: str
    to_state: str
    required_evidence: List[str]
    forbidden_evidence: List[str]
    timeout_policy: dict
    transition_rule_version: str