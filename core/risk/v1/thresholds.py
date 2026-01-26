"""
RFC-13 Risk Observability - Evaluación de Umbrales
====================================================

Evaluador determinista de umbrales institucionales (sin auto-ajuste).

PROHIBIDO:
- Usar datetime.now() o time.time() (timestamps inyectados)
- Auto-ajustar umbrales (gobernados por change control RFC-12)
- Side effects (solo lectura/agregación)
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.risk.v1.enums import RiskSeverityLevel, RiskScope, RiskSignalType


class ThresholdEvaluator:
    """
    Evaluador determinista de umbrales institucionales.
    
    Responsabilidades:
    - Cargar y validar threshold_set desde JSON (conforme a schema)
    - Evaluar observations contra umbrales
    - Mapear valores a severidad según reglas explícitas
    
    Invariantes:
    - Función pura (mismo input → mismo output)
    - No mutación de upstream
    - Timestamps inyectados (no reloj del sistema)
    """
    
    def __init__(self, threshold_set: Dict[str, Any]):
        """
        Inicializa el evaluador con un threshold_set validado.
        
        Args:
            threshold_set: Dict conforme a risk_threshold_set.schema.json
        
        Raises:
            ValueError: Si el threshold_set no es válido
        """
        self._validate_threshold_set(threshold_set)
        self.threshold_set = threshold_set
        self.rules_by_key = self._index_rules()
    
    @classmethod
    def from_file(cls, path: Path) -> "ThresholdEvaluator":
        """Carga threshold_set desde archivo JSON."""
        with open(path, "r", encoding="utf-8") as f:
            threshold_set = json.load(f)
        return cls(threshold_set)
    
    def _validate_threshold_set(self, threshold_set: Dict[str, Any]) -> None:
        """Valida estructura mínima del threshold_set."""
        required_fields = ["threshold_set_id", "threshold_set_version", "approved_change_ref", "rules"]
        for field in required_fields:
            if field not in threshold_set:
                raise ValueError(f"threshold_set missing required field: {field}")
        
        if not threshold_set["approved_change_ref"]:
            raise ValueError("approved_change_ref must be non-empty (institutional governance)")
        
        # Permitir threshold_set vacío para tests de validación (anti-vanity)
        # En producción, threshold_set sin reglas es válido (silencio total = anti-ruido)
        
        # Verificar que no hay campos de auto-ajuste (hard fail)
        forbidden_fields = ["auto_tune", "learning", "adaptive"]
        for field in forbidden_fields:
            if field in threshold_set:
                raise ValueError(f"Auto-adjustment forbidden: '{field}' field not allowed")
    
    def _index_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Indexa reglas por (signal_type, scope, metric_key) para lookup eficiente."""
        index = {}
        for rule in self.threshold_set["rules"]:
            key = (rule["signal_type"], rule["scope"], rule["metric_key"])
            if key not in index:
                index[key] = []
            index[key].append(rule)
        return index
    
    def evaluate(
        self,
        signal_type: RiskSignalType,
        scope: RiskScope,
        metric_key: str,
        metric_value: float
    ) -> Optional[RiskSeverityLevel]:
        """
        Evalúa un valor de métrica contra umbrales y retorna severidad.
        
        Args:
            signal_type: Tipo de señal a evaluar
            scope: Alcance de la señal
            metric_key: Clave de la métrica
            metric_value: Valor observado
        
        Returns:
            RiskSeverityLevel si el umbral se activa, None en caso contrario
        
        Algoritmo determinista:
        - Busca regla matching (signal_type, scope, metric_key)
        - Evalúa severity_mapping en orden
        - Retorna la mayor severidad que cumple condición
        """
        key = (signal_type.value, scope.value, metric_key)
        rules = self.rules_by_key.get(key, [])
        
        if not rules:
            return None  # No hay umbral definido → no generar señal (anti-ruido)
        
        # Evaluar todas las reglas matching y retornar la mayor severidad
        triggered_severities = []
        for rule in rules:
            severity = self._evaluate_rule(rule, metric_value)
            if severity:
                triggered_severities.append(severity)
        
        if not triggered_severities:
            return None
        
        return RiskSeverityLevel.max(*triggered_severities)
    
    def _evaluate_rule(
        self,
        rule: Dict[str, Any],
        metric_value: float
    ) -> Optional[RiskSeverityLevel]:
        """Evalúa una regla específica y retorna severidad si se cumple."""
        severity_mapping = rule.get("severity_mapping", [])
        
        # Evaluar en orden inverso (CRITICAL → LOW) para retornar la mayor severidad
        sorted_mapping = sorted(
            severity_mapping,
            key=lambda m: self._severity_order(m["severity_level"]),
            reverse=True
        )
        
        for mapping in sorted_mapping:
            if self._check_threshold(metric_value, mapping):
                return RiskSeverityLevel(mapping["severity_level"])
        
        return None
    
    def _check_threshold(self, value: float, mapping: Dict[str, Any]) -> bool:
        """Evalúa condición de umbral (GT, GTE, LT, LTE, EQ)."""
        threshold_value = mapping["threshold_value"]
        operator = mapping["operator"]
        
        if operator == "GT":
            return value > threshold_value
        elif operator == "GTE":
            return value >= threshold_value
        elif operator == "LT":
            return value < threshold_value
        elif operator == "LTE":
            return value <= threshold_value
        elif operator == "EQ":
            return value == threshold_value
        else:
            raise ValueError(f"Unknown operator: {operator}")
    
    def _severity_order(self, severity: str) -> int:
        """Retorna orden numérico de severidad para sorting."""
        order = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4
        }
        return order.get(severity, 0)
    
    def evaluate_observations(
        self,
        observations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evalúa un batch de observaciones y retorna las que activan umbrales.
        
        Args:
            observations: Lista de observations conforme a risk_observation.schema.json
        
        Returns:
            Lista de dicts con {observation, signal_type, severity_level}
        """
        triggered = []
        
        for obs in observations:
            # Intentar evaluar contra todos los tipos de señal relevantes
            # (en práctica, la observación debería indicar el signal_type esperado)
            metric_key = obs["metric_key"]
            metric_value = obs["metric_value"]
            scope = RiskScope(obs["scope"])
            
            # Por ahora, evaluamos contra todos los signal_types
            # (en implementación real, la observación debería sugerir el tipo)
            for signal_type in RiskSignalType:
                severity = self.evaluate(signal_type, scope, metric_key, metric_value)
                if severity:
                    triggered.append({
                        "observation": obs,
                        "signal_type": signal_type,
                        "severity_level": severity,
                    })
        
        return triggered
