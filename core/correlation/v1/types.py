from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CorrelationEvidence:
    evidence_type: str
    pointer: str
    details: dict


@dataclass(frozen=True)
class CorrelationLink:
    link_id: str
    source_event_id: str
    target_event_id: str
    link_type: str
    rule_id: str
    rule_version: str
    version: str
    score: float
    evidence: List[CorrelationEvidence]
    engine_version: str
    created_at: str


@dataclass(frozen=True)
class CorrelationRule:
    rule_id: str
    rule_version: str
    applicability: dict
    evidence_required: List[str]
    explanation_template: str


@dataclass(frozen=True)
class MoneyFlow:
    flow_id: str
    version: str
    event_ids: List[str]
    link_ids: List[str]
    created_at: str