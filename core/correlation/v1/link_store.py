from typing import Protocol, Iterator, List
from .types import CorrelationLink


class AppendOnlyLinkStore(Protocol):
    def append(self, link: CorrelationLink) -> None:
        """Agrega un link al store. Debe rechazar duplicados por link_id."""
        ...
    
    def iter_all(self) -> Iterator[CorrelationLink]:
        """Itera sobre todos los links en el store."""
        ...
    
    def iter_by_event(self, event_id: str) -> Iterator[CorrelationLink]:
        """Itera sobre links que involucran el event_id dado."""
        ...


class InMemoryAppendOnlyLinkStore:
    def __init__(self):
        self._links: List[CorrelationLink] = []
        self._link_ids: set = set()
    
    def append(self, link: CorrelationLink) -> None:
        # Invariante: rechaza duplicado exacto de link_id
        if link.link_id in self._link_ids:
            raise ValueError(f"Duplicate link_id: {link.link_id}")
        
        self._links.append(link)
        self._link_ids.add(link.link_id)
    
    def iter_all(self) -> Iterator[CorrelationLink]:
        yield from self._links
    
    def iter_by_event(self, event_id: str) -> Iterator[CorrelationLink]:
        for link in self._links:
            if link.source_event_id == event_id or link.target_event_id == event_id:
                yield link