"""
RFC-13 Risk Observability - RiskAssessor
=========================================

Computa RiskAggregate desde ventana de señales.

PROHIBIDO:
- Side effects (función pura)
- Usar reloj del sistema (computed_at = time_window.end_at)
- Algoritmos no deterministas
"""

from typing import List, Dict, Any
from datetime import datetime
import hashlib

from core.risk.v1.enums import RiskSeverityLevel


class RiskAssessor:
    """
    Computa agregados de riesgo desde ventanas de señales.
    
    Responsabilidades:
    - Agregar señales en ventana temporal
    - Calcular overall_risk_level determinista
    - Identificar drivers (señales que conducen el riesgo global)
    
    Algoritmo determinista (RFC-13 §5.2):
    - overall_risk_level = max(severity_level) por orden CRITICAL>HIGH>MEDIUM>LOW
    - drivers = ids de señales que igualan overall_risk_level
    - computed_at = time_window.end_at (no reloj del sistema)
    
    Invariantes:
    - Función pura (mismo input → mismo output)
    - Determinismo radical (orden estable, sin heurísticas opacas)
    """
    
    def assess(
        self,
        time_window: Dict[str, str],
        signals: List[Dict[str, Any]],
        model_version: str
    ) -> Dict[str, Any]:
        """
        Computa RiskAggregate desde ventana de señales.
        
        Args:
            time_window: Dict con {"start_at": iso8601, "end_at": iso8601}
            signals: Lista de RiskSignals conformes a schema
            model_version: Versión del modelo de agregación
        
        Returns:
            RiskAggregate conforme a risk_aggregate.schema.json
        """
        if not signals:
            # Ventana sin señales → riesgo LOW por defecto
            return self._build_empty_aggregate(time_window, model_version)
        
        # Construir risk_profile (vector de señales)
        risk_profile = [
            {
                "risk_signal_id": sig["risk_signal_id"],
                "signal_type": sig["signal_type"],
                "severity_level": sig["severity_level"],
            }
            for sig in signals
        ]
        
        # Calcular overall_risk_level (max severity)
        overall_risk_level = self._compute_overall_risk(signals)
        
        # Identificar drivers (señales que igualan overall)
        drivers = self._identify_drivers(signals, overall_risk_level)
        
        # Generar aggregate_id determinista
        aggregate_id = self._generate_aggregate_id(time_window)
        
        # computed_at = time_window.end_at (determinismo)
        computed_at = time_window["end_at"]
        
        return {
            "aggregate_id": aggregate_id,
            "time_window": time_window,
            "risk_profile": risk_profile,
            "overall_risk_level": overall_risk_level.value,
            "drivers": drivers,
            "computed_at": computed_at,
            "model_version": model_version,
        }
    
    def _build_empty_aggregate(
        self,
        time_window: Dict[str, str],
        model_version: str
    ) -> Dict[str, Any]:
        """Construye agregado vacío (sin señales → riesgo LOW)."""
        return {
            "aggregate_id": self._generate_aggregate_id(time_window),
            "time_window": time_window,
            "risk_profile": [],
            "overall_risk_level": RiskSeverityLevel.LOW.value,
            "drivers": [],
            "computed_at": time_window["end_at"],
            "model_version": model_version,
        }
    
    def _compute_overall_risk(self, signals: List[Dict[str, Any]]) -> RiskSeverityLevel:
        """
        Calcula overall_risk_level como max(severity_level).
        
        Orden: CRITICAL > HIGH > MEDIUM > LOW
        """
        severities = [RiskSeverityLevel(sig["severity_level"]) for sig in signals]
        return RiskSeverityLevel.max(*severities)
    
    def _identify_drivers(
        self,
        signals: List[Dict[str, Any]],
        overall_risk_level: RiskSeverityLevel
    ) -> List[str]:
        """
        Identifica drivers: señales que igualan overall_risk_level.
        
        Orden estable (determinismo): por risk_signal_id alfabético
        """
        drivers = [
            sig["risk_signal_id"]
            for sig in signals
            if sig["severity_level"] == overall_risk_level.value
        ]
        return sorted(drivers)  # Orden estable
    
    def _generate_aggregate_id(self, time_window: Dict[str, str]) -> str:
        """
        Genera ID determinista de agregado mediante hash SHA256.
        
        Algoritmo: Hash de (start_at + end_at)
        Garantiza: Misma ventana → mismo ID (replay determinista)
        """
        start_at = datetime.fromisoformat(time_window["start_at"])
        end_at = datetime.fromisoformat(time_window["end_at"])
        
        start_str = start_at.strftime("%Y%m%d%H%M%S")
        end_str = end_at.strftime("%Y%m%d%H%M%S")
        
        # Generar hash determinista
        content = f"{start_str}_{end_str}"
        hash_digest = hashlib.sha256(content.encode('utf-8')).hexdigest()[:8]
        
        return f"RISKAGG_{start_str}_{end_str}_{hash_digest}"
