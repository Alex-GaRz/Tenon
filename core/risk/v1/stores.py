"""
RFC-13 Risk Observability - Append-Only Stores
===============================================

Stores inmutables para señales, agregados y alertas.

PROHIBIDO:
- Métodos update, delete, upsert (append-only obligatorio por gobernanza)
- Side effects fuera de append (lectura pura en get/list)
"""

from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime
from abc import ABC, abstractmethod


class AppendOnlySignalStore:
    """
    Store append-only para RiskSignals.
    
    Operaciones permitidas:
    - append(signal): Añadir señal (inmutable)
    - get(risk_signal_id): Recuperar señal por ID
    - list(...): Listar señales con filtros
    - iter_window(...): Iterar señales en ventana temporal
    
    PROHIBIDO: update, delete, upsert
    """
    
    def __init__(self):
        """Inicializa store in-memory (determinista para tests)."""
        self._signals: List[Dict[str, Any]] = []
        self._index_by_id: Dict[str, Dict[str, Any]] = {}
    
    def append(self, signal: Dict[str, Any]) -> None:
        """
        Añade señal al store (append-only).
        
        Args:
            signal: RiskSignal conforme a schema
        
        Raises:
            ValueError: Si risk_signal_id ya existe (idempotencia)
        """
        risk_signal_id = signal["risk_signal_id"]
        
        if risk_signal_id in self._index_by_id:
            raise ValueError(f"Duplicate risk_signal_id: {risk_signal_id}")
        
        self._signals.append(signal)
        self._index_by_id[risk_signal_id] = signal
    
    def get(self, risk_signal_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera señal por ID.
        
        Returns:
            RiskSignal o None si no existe
        """
        return self._index_by_id.get(risk_signal_id)
    
    def list(
        self,
        signal_type: Optional[str] = None,
        scope: Optional[str] = None,
        severity_level: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista señales con filtros opcionales.
        
        Args:
            signal_type: Filtrar por tipo de señal
            scope: Filtrar por alcance
            severity_level: Filtrar por severidad
            limit: Máximo número de resultados
        
        Returns:
            Lista de RiskSignals (orden: por observed_at desc)
        """
        filtered = self._signals
        
        if signal_type:
            filtered = [s for s in filtered if s["signal_type"] == signal_type]
        
        if scope:
            filtered = [s for s in filtered if s["scope"] == scope]
        
        if severity_level:
            filtered = [s for s in filtered if s["severity_level"] == severity_level]
        
        # Ordenar por observed_at descendente (más reciente primero)
        sorted_signals = sorted(
            filtered,
            key=lambda s: s["observed_at"],
            reverse=True
        )
        
        if limit:
            return sorted_signals[:limit]
        
        return sorted_signals
    
    def iter_window(
        self,
        start_at: datetime,
        end_at: datetime
    ) -> Iterator[Dict[str, Any]]:
        """
        Itera señales en ventana temporal [start_at, end_at).
        
        Args:
            start_at: Inicio de ventana (inclusive)
            end_at: Fin de ventana (exclusive)
        
        Yields:
            RiskSignals en la ventana (orden: observed_at asc)
        """
        start_iso = start_at.isoformat()
        end_iso = end_at.isoformat()
        
        for signal in sorted(self._signals, key=lambda s: s["observed_at"]):
            observed_at = signal["observed_at"]
            if start_iso <= observed_at < end_iso:
                yield signal


class AppendOnlyAggregateStore:
    """
    Store append-only para RiskAggregates.
    
    Operaciones permitidas:
    - append(aggregate): Añadir agregado
    - get(aggregate_id): Recuperar agregado por ID
    - list(...): Listar agregados
    
    PROHIBIDO: update, delete, upsert
    """
    
    def __init__(self):
        """Inicializa store in-memory (determinista para tests)."""
        self._aggregates: List[Dict[str, Any]] = []
        self._index_by_id: Dict[str, Dict[str, Any]] = {}
    
    def append(self, aggregate: Dict[str, Any]) -> None:
        """
        Añade agregado al store (append-only).
        
        Args:
            aggregate: RiskAggregate conforme a schema
        
        Raises:
            ValueError: Si aggregate_id ya existe
        """
        aggregate_id = aggregate["aggregate_id"]
        
        if aggregate_id in self._index_by_id:
            raise ValueError(f"Duplicate aggregate_id: {aggregate_id}")
        
        self._aggregates.append(aggregate)
        self._index_by_id[aggregate_id] = aggregate
    
    def get(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera agregado por ID.
        
        Returns:
            RiskAggregate o None si no existe
        """
        return self._index_by_id.get(aggregate_id)
    
    def list(
        self,
        overall_risk_level: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista agregados con filtros opcionales.
        
        Args:
            overall_risk_level: Filtrar por nivel de riesgo global
            limit: Máximo número de resultados
        
        Returns:
            Lista de RiskAggregates (orden: por computed_at desc)
        """
        filtered = self._aggregates
        
        if overall_risk_level:
            filtered = [a for a in filtered if a["overall_risk_level"] == overall_risk_level]
        
        # Ordenar por computed_at descendente
        sorted_aggregates = sorted(
            filtered,
            key=lambda a: a["computed_at"],
            reverse=True
        )
        
        if limit:
            return sorted_aggregates[:limit]
        
        return sorted_aggregates


class AppendOnlyAlertStore:
    """
    Store append-only para RiskAlerts.
    
    Operaciones permitidas:
    - append(alert): Añadir alerta
    - get(alert_id): Recuperar alerta por ID
    - list(...): Listar alertas
    
    PROHIBIDO: update, delete, upsert
    """
    
    def __init__(self):
        """Inicializa store in-memory (determinista para tests)."""
        self._alerts: List[Dict[str, Any]] = []
        self._index_by_id: Dict[str, Dict[str, Any]] = {}
    
    def append(self, alert: Dict[str, Any]) -> None:
        """
        Añade alerta al store (append-only).
        
        Args:
            alert: RiskAlert conforme a schema
        
        Raises:
            ValueError: Si alert_id ya existe
        """
        alert_id = alert["alert_id"]
        
        if alert_id in self._index_by_id:
            raise ValueError(f"Duplicate alert_id: {alert_id}")
        
        self._alerts.append(alert)
        self._index_by_id[alert_id] = alert
    
    def get(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera alerta por ID.
        
        Returns:
            RiskAlert o None si no existe
        """
        return self._index_by_id.get(alert_id)
    
    def list(
        self,
        alert_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista alertas con filtros opcionales.
        
        Args:
            alert_type: Filtrar por tipo de alerta
            limit: Máximo número de resultados
        
        Returns:
            Lista de RiskAlerts (orden: por raised_at desc)
        """
        filtered = self._alerts
        
        if alert_type:
            filtered = [a for a in filtered if a["alert_type"] == alert_type]
        
        # Ordenar por raised_at descendente
        sorted_alerts = sorted(
            filtered,
            key=lambda a: a["raised_at"],
            reverse=True
        )
        
        if limit:
            return sorted_alerts[:limit]
        
        return sorted_alerts
