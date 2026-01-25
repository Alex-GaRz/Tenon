from typing import Protocol, Iterator, List
from .types import MoneyStateEvaluation


class AppendOnlyStateStore(Protocol):
    def append(self, evaluation: MoneyStateEvaluation) -> None:
        """Agrega una evaluación al store. Debe rechazar duplicados por evaluation_id."""
        ...
    
    def iter_all(self) -> Iterator[MoneyStateEvaluation]:
        """Itera sobre todas las evaluaciones en el store."""
        ...
    
    def iter_by_flow(self, flow_id: str) -> Iterator[MoneyStateEvaluation]:
        """Itera sobre evaluaciones que pertenecen al flow_id dado."""
        ...


class InMemoryAppendOnlyStateStore:
    def __init__(self):
        self._evaluations: List[MoneyStateEvaluation] = []
        self._evaluation_ids: set = set()
    
    def append(self, evaluation: MoneyStateEvaluation) -> None:
        # Invariante: rechaza evaluation_id duplicado
        if evaluation.evaluation_id in self._evaluation_ids:
            raise ValueError(f"Duplicate evaluation_id: {evaluation.evaluation_id}")
        
        self._evaluations.append(evaluation)
        self._evaluation_ids.add(evaluation.evaluation_id)
    
    def iter_all(self) -> Iterator[MoneyStateEvaluation]:
        yield from self._evaluations
    
    def iter_by_flow(self, flow_id: str) -> Iterator[MoneyStateEvaluation]:
        for evaluation in self._evaluations:
            if evaluation.flow_id == flow_id:
                yield evaluation