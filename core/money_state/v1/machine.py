from typing import List
import hashlib
from .types import MoneyStateEvaluation, TransitionRule, MONEY_STATES
from .state_store import AppendOnlyStateStore


class MoneyStateMachine:
    def __init__(
        self,
        transitions: List[TransitionRule],
        store: AppendOnlyStateStore,
        machine_version: str = "v1",
        state_version: str = "v1"
    ) -> None:
        # Validar que todas las transiciones usan estados válidos
        for transition in transitions:
            if transition.from_state not in MONEY_STATES:
                raise ValueError(f"Invalid from_state: {transition.from_state}")
            if transition.to_state not in MONEY_STATES:
                raise ValueError(f"Invalid to_state: {transition.to_state}")
        
        self.transitions = transitions
        self.store = store
        self.machine_version = machine_version
        self.state_version = state_version
    
    def evaluate(
        self,
        *,
        flow_id: str,
        canonical_events: List[dict],
        correlation_links: List[dict],
        evaluated_at: str,
        evidence_pointer: str
    ) -> MoneyStateEvaluation:
        """
        Máquina diagnóstica: consume eventos + links y emite evaluaciones (append-only).
        Determinismo: depende SOLO de inputs (eventos, links, transitions, versiones) 
        y del evaluated_at/evidence_pointer provistos.
        """
        
        # Extraer evidencia disponible de eventos y links
        available_evidence = self._extract_evidence(canonical_events, correlation_links)
        
        # Determinar el estado actual basado en evidencia y transiciones
        current_state, transition_reason, confidence = self._determine_state(
            available_evidence, 
            canonical_events, 
            correlation_links
        )
        
        # Generar evaluation_id determinista
        evaluation_id = self._generate_evaluation_id(
            flow_id, canonical_events, correlation_links, evaluated_at, evidence_pointer
        )
        
        # Seleccionar event_id principal (el primero ordenado lexicográficamente)
        event_id = self._select_primary_event_id(canonical_events)
        
        # Timestamp principal (el más reciente de los eventos)
        timestamp = self._select_primary_timestamp(canonical_events)
        
        return MoneyStateEvaluation(
            evaluation_id=evaluation_id,
            flow_id=flow_id,
            event_id=event_id,
            timestamp=timestamp,
            state=current_state,
            transition_reason=transition_reason,
            evidence_pointer=evidence_pointer,
            state_version=self.state_version,
            machine_version=self.machine_version,
            confidence_level=confidence,
            evaluated_at=evaluated_at
        )
    
    def _extract_evidence(self, canonical_events: List[dict], correlation_links: List[dict]) -> List[str]:
        """Extrae tipos de evidencia disponible de eventos y links."""
        evidence_types = []
        
        # Evidencia de eventos
        for event in canonical_events:
            event_type = event.get('event_type', '')
            
            if event_type == 'payment_initiated':
                evidence_types.append('INITIATION_SIGNAL')
            elif event_type == 'authorization_confirmed':
                evidence_types.append('AUTHORIZATION_CONFIRMATION')
            elif event_type == 'authorization_denied':
                evidence_types.append('AUTHORIZATION_DENIAL')
            elif event_type == 'processing_started':
                evidence_types.append('PROCESSING_START')
            elif event_type == 'settlement_confirmed':
                evidence_types.append('SETTLEMENT_CONFIRMATION')
            elif event_type == 'processing_failed':
                evidence_types.append('PROCESSING_FAILURE')
            elif event_type == 'settlement_rejected':
                evidence_types.append('SETTLEMENT_REJECTION')
            elif event_type == 'refund_requested':
                evidence_types.append('REFUND_REQUEST')
            elif event_type == 'refund_confirmed':
                evidence_types.append('REFUND_CONFIRMATION')
            elif event_type == 'reversal_requested':
                evidence_types.append('REVERSAL_REQUEST')
            elif event_type == 'reversal_confirmed':
                evidence_types.append('REVERSAL_CONFIRMATION')
            elif event_type == 'timeout_exceeded':
                evidence_types.append('TIMEOUT_EXCEEDED')
        
        # Evidencia de correlation links
        for link in correlation_links:
            link_type = link.get('link_type', '')
            if link_type == 'SEQUENCE':
                evidence_types.append('SEQUENCE_OBSERVED')
            elif link_type == 'REVERSAL':
                evidence_types.append('REVERSAL_LINK')
            elif link_type == 'REFUND':
                evidence_types.append('REFUND_LINK')
        
        return list(set(evidence_types))  # Eliminar duplicados
    
    def _determine_state(self, available_evidence: List[str], events: List[dict], links: List[dict]) -> tuple[str, str, float]:
        """
        Determina el estado basado en evidencia disponible y transiciones.
        Conservadurismo: si múltiples estados plausibles ⇒ state="AMBIGUOUS".
        """
        
        # Detectar evidencia contradictoria explícitamente
        has_settlement = 'SETTLEMENT_CONFIRMATION' in available_evidence
        has_failure = 'PROCESSING_FAILURE' in available_evidence or 'SETTLEMENT_REJECTION' in available_evidence
        
        if has_settlement and has_failure:
            return "AMBIGUOUS", "Contradictory evidence: both settlement and failure signals detected", 0.5
        
        # Evaluar todas las transiciones posibles
        possible_states = []
        
        for transition in self.transitions:
            # Verificar si tenemos evidencia requerida
            has_required = all(evidence in available_evidence for evidence in transition.required_evidence)
            
            # Verificar que no tenemos evidencia prohibida
            has_forbidden = any(evidence in available_evidence for evidence in transition.forbidden_evidence)
            
            if has_required and not has_forbidden:
                possible_states.append((
                    transition.to_state,
                    f"Transition from {transition.from_state} to {transition.to_state}",
                    0.8 if has_required else 0.3
                ))
        
        # Si no hay transiciones posibles, determinar por patrones de evidencia
        if not possible_states:
            if 'SETTLEMENT_CONFIRMATION' in available_evidence:
                return "SETTLED", "Settlement evidence found", 0.9
            elif 'PROCESSING_FAILURE' in available_evidence:
                return "FAILED", "Failure evidence found", 0.9
            elif 'AUTHORIZATION_CONFIRMATION' in available_evidence:
                return "AUTHORIZED", "Authorization evidence found", 0.7
            elif 'INITIATION_SIGNAL' in available_evidence:
                return "INITIATED", "Initiation evidence found", 0.7
            else:
                return "UNKNOWN", "Insufficient evidence", 0.1
        
        # Conservadurismo: si múltiples estados plausibles => AMBIGUOUS
        if len(possible_states) > 1:
            # Verificar si hay estados conflictivos (ej: SETTLED y FAILED)
            state_names = [state[0] for state in possible_states]
            if ('SETTLED' in state_names and 'FAILED' in state_names) or \
               ('AUTHORIZED' in state_names and 'FAILED' in state_names):
                return "AMBIGUOUS", "Multiple plausible states detected: conflicting terminal states", 0.5
        
        # Retornar el estado con mayor confianza
        possible_states.sort(key=lambda x: x[2], reverse=True)
        best_state = possible_states[0]
        
        return best_state[0], best_state[1], min(best_state[2], 1.0)
    
    def _generate_evaluation_id(
        self, 
        flow_id: str, 
        events: List[dict], 
        links: List[dict], 
        evaluated_at: str, 
        evidence_pointer: str
    ) -> str:
        """Genera un evaluation_id determinista basado en los inputs."""
        # Crear contenido determinista
        sorted_event_ids = sorted([e.get('event_id', '') for e in events])
        sorted_link_ids = sorted([l.get('link_id', '') for l in links])
        
        content = f"{flow_id}|{','.join(sorted_event_ids)}|{','.join(sorted_link_ids)}|{evaluated_at}|{evidence_pointer}"
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def _select_primary_event_id(self, events: List[dict]) -> str:
        """Selecciona el event_id principal (el primero ordenado lexicográficamente)."""
        if not events:
            return ""
        
        event_ids = [e.get('event_id', '') for e in events if e.get('event_id')]
        return min(event_ids) if event_ids else ""
    
    def _select_primary_timestamp(self, events: List[dict]) -> str:
        """Selecciona el timestamp más reciente de los eventos."""
        if not events:
            return ""
        
        timestamps = [e.get('timestamp', '') for e in events if e.get('timestamp')]
        return max(timestamps) if timestamps else ""
    
    def persist(self, evaluation: MoneyStateEvaluation) -> None:
        """Persiste la evaluación en el store append-only."""
        self.store.append(evaluation)