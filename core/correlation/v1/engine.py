from typing import List
import hashlib
from .types import CorrelationLink, MoneyFlow, CorrelationEvidence
from .rules_registry import RuleRegistry
from .link_store import AppendOnlyLinkStore
from .scoring import score_from_evidence, clamp_score
from .linker import link_events


class CorrelationEngine:
    def __init__(self, registry: RuleRegistry, store: AppendOnlyLinkStore, engine_version: str = "v1") -> None:
        self.registry = registry
        self.store = store
        self.engine_version = engine_version
    
    def propose_links(self, canonical_events: List[dict]) -> List[CorrelationLink]:
        """
        Motor determinista: eventos -> propuestas de vínculos (no "truth", no merge).
        Evalúa TODAS las correlaciones plausibles (preserva ambigüedad).
        """
        if not canonical_events:
            return []
        
        # Ordenar eventos por event_id asc antes de evaluar (determinismo)
        sorted_events = sorted(canonical_events, key=lambda e: e.get('event_id', ''))
        
        # Evaluar reglas en orden estable
        rules = self.registry.list_rules()
        
        proposed_links = []
        
        for rule in rules:
            # Para cada regla, evaluar todos los pares de eventos
            for i, event1 in enumerate(sorted_events):
                for j, event2 in enumerate(sorted_events):
                    if i >= j:  # Evitar duplicados y auto-correlación
                        continue
                    
                    # Intentar correlacionar event1 con event2
                    link = self._try_correlate_events(event1, event2, rule)
                    if link:
                        proposed_links.append(link)
        
        return proposed_links
    
    def _try_correlate_events(self, event1: dict, event2: dict, rule) -> CorrelationLink:
        """
        Intenta correlacionar dos eventos según una regla específica.
        Retorna None si no hay correlación plausible.
        """
        event1_id = event1.get('event_id', '')
        event2_id = event2.get('event_id', '')
        
        if not event1_id or not event2_id or event1_id == event2_id:
            return None
        
        # Verificar aplicabilidad básica
        # (En una implementación real, verificaríamos event_kinds)
        
        # Generar evidencia basada en los eventos
        evidence = self._generate_evidence(event1, event2, rule)
        
        if not evidence:
            return None
        
        # Calcular score
        score = score_from_evidence(evidence)
        score = clamp_score(score)
        
        # Si el score es muy bajo, no crear el link
        if score < 0.1:
            return None
        
        # Determinar el tipo de link (simplificado)
        link_type = self._determine_link_type(event1, event2, evidence)
        
        # Generar link_id determinista
        link_id = self._generate_link_id(event1_id, event2_id, rule.rule_id, rule.rule_version)
        
        # Timestamp determinista basado en los eventos
        created_at = max(event1.get('timestamp', ''), event2.get('timestamp', ''))
        
        try:
            return link_events(
                source_event_id=event1_id,
                target_event_id=event2_id,
                link_type=link_type,
                rule=rule,
                evidence=evidence,
                score=score,
                engine_version=self.engine_version,
                created_at=created_at,
                link_id=link_id
            )
        except ValueError:
            return None
    
    def _generate_evidence(self, event1: dict, event2: dict, rule) -> List[CorrelationEvidence]:
        """Genera evidencia comparando dos eventos."""
        evidence = []
        
        # REFERENCE_MATCH: mismo external_reference
        if (event1.get('external_reference') and 
            event2.get('external_reference') and 
            event1.get('external_reference') == event2.get('external_reference')):
            evidence.append(CorrelationEvidence(
                evidence_type="REFERENCE_MATCH",
                pointer=f"events/{event1.get('event_id')}/{event2.get('event_id')}",
                details={"matched_reference": event1.get('external_reference')}
            ))
        
        # AMOUNT_TOLERANCE: montos similares
        amount1 = event1.get('amount')
        amount2 = event2.get('amount')
        if amount1 is not None and amount2 is not None:
            if amount1 != 0:
                tolerance = abs(amount1 - amount2) / abs(amount1)
                if tolerance <= 0.05:  # 5% de tolerancia
                    evidence.append(CorrelationEvidence(
                        evidence_type="AMOUNT_TOLERANCE",
                        pointer=f"amounts/{event1.get('event_id')}/{event2.get('event_id')}",
                        details={"tolerance_percentage": tolerance}
                    ))
        
        # TIME_WINDOW: eventos cercanos en tiempo
        ts1 = event1.get('timestamp')
        ts2 = event2.get('timestamp')
        if ts1 and ts2:
            # Simplificado: si ambos timestamps están presentes
            evidence.append(CorrelationEvidence(
                evidence_type="TIME_WINDOW",
                pointer=f"timestamps/{event1.get('event_id')}/{event2.get('event_id')}",
                details={"window_minutes": 60}  # Asumimos ventana de 1 hora
            ))
        
        return evidence
    
    def _determine_link_type(self, event1: dict, event2: dict, evidence: List[CorrelationEvidence]) -> str:
        """Determina el tipo de link basado en evidencia."""
        # Lógica simplificada
        for ev in evidence:
            if ev.evidence_type == "REFERENCE_MATCH":
                return "POTENTIAL_MATCH"
        
        return "RELATED"
    
    def _generate_link_id(self, event1_id: str, event2_id: str, rule_id: str, rule_version: str) -> str:
        """Genera un link_id determinista."""
        # Ordenar IDs para consistencia
        sorted_ids = sorted([event1_id, event2_id])
        content = f"{sorted_ids[0]}|{sorted_ids[1]}|{rule_id}|{rule_version}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def persist_links(self, links: List[CorrelationLink]) -> None:
        """Solo append; si link ya existe por link_id => ValueError"""
        for link in links:
            self.store.append(link)
    
    def build_money_flow(self, flow_id: str, event_ids: List[str]) -> MoneyFlow:
        """
        link_ids = todos los links del store cuyo source_event_id o target_event_id ∈ event_ids,
        ordenados lexicográficamente.
        """
        event_ids_set = set(event_ids)
        relevant_link_ids = []
        
        for link in self.store.iter_all():
            if (link.source_event_id in event_ids_set or 
                link.target_event_id in event_ids_set):
                relevant_link_ids.append(link.link_id)
        
        # Ordenar lexicográficamente
        relevant_link_ids.sort()
        
        return MoneyFlow(
            flow_id=flow_id,
            version="v1",
            event_ids=sorted(event_ids),  # También ordenar event_ids para consistencia
            link_ids=relevant_link_ids,
            created_at="2026-01-25T00:00:00Z"  # Timestamp fijo para determinismo
        )