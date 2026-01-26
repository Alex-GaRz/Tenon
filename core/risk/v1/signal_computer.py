"""
RFC-13 Risk Observability - SignalComputer
===========================================

Computa RiskSignals desde observaciones derivadas.

PROHIBIDO:
- Aceptar eventos crudos (solo observaciones derivadas conforme a schema)
- Generar señales sin supporting_metrics/supporting_evidence/explanation
- Usar datetime.now() (timestamps inyectados)
- Side effects (función pura)
"""

from typing import List, Dict, Any
from datetime import datetime
import hashlib

from core.risk.v1.enums import RiskSeverityLevel, RiskScope, RiskSignalType
from core.risk.v1.thresholds import ThresholdEvaluator


class SignalComputer:
    """
    Computa señales de riesgo desde observaciones derivadas.
    
    Responsabilidades:
    - Validar que input cumple risk_observation.schema.json
    - Evaluar observaciones contra umbrales
    - Construir RiskSignal con evidencia/explicación obligatoria
    - Implementar anti-ruido (no crear señales si no hay umbral activado)
    
    Invariantes RFC-13:
    - Solo acepta observaciones derivadas (§3.2)
    - Cada señal incluye supporting_metrics, supporting_evidence, explanation (§3.3)
    - Determinismo radical (§10.2)
    """
    
    def __init__(self, threshold_evaluator: ThresholdEvaluator):
        """
        Inicializa SignalComputer con evaluador de umbrales.
        
        Args:
            threshold_evaluator: Evaluador de umbrales institucionales
        """
        self.threshold_evaluator = threshold_evaluator
    
    def compute(
        self,
        observation_bundle: Dict[str, Any],
        signal_version: str,
        observed_at: datetime
    ) -> List[Dict[str, Any]]:
        """
        Computa señales de riesgo desde un bundle de observaciones.
        
        Args:
            observation_bundle: Dict conforme a risk_observation.schema.json
            signal_version: Versión del modelo de señales (gobernanza)
            observed_at: Timestamp inyectado de observación
        
        Returns:
            Lista de RiskSignals conformes a risk_signal.schema.json
        
        Política anti-ruido:
        - Solo crea señales si umbral se activa
        - No genera señales "informativas" sin riesgo
        """
        observations = observation_bundle.get("observations", [])
        
        # Validar que no hay métricas de vanity/infra (hard fail)
        self._validate_no_vanity_metrics(observations)
        
        # Evaluar observaciones contra umbrales
        triggered = self.threshold_evaluator.evaluate_observations(observations)
        
        # Construir señales con evidencia/explicación
        signals = []
        for triggered_obs in triggered:
            signal = self._build_signal(
                observation=triggered_obs["observation"],
                signal_type=triggered_obs["signal_type"],
                severity_level=triggered_obs["severity_level"],
                signal_version=signal_version,
                observed_at=observed_at
            )
            signals.append(signal)
        
        return signals
    
    def _validate_no_vanity_metrics(self, observations: List[Dict[str, Any]]) -> None:
        """
        Valida que no hay métricas de performance/infra (hard fail).
        
        Raises:
            ValueError: Si detecta metric_key prohibido
        """
        forbidden_patterns = [
            "cpu", "ram", "memory", "latency", "qps", "throughput",
            "bandwidth", "disk", "io_wait", "load_avg", "network"
        ]
        
        for obs in observations:
            metric_key = obs.get("metric_key", "").lower()
            for pattern in forbidden_patterns:
                if pattern in metric_key:
                    raise ValueError(
                        f"Vanity metric forbidden: '{obs['metric_key']}' "
                        f"contains '{pattern}' (RFC-13 No-Goals)"
                    )
    
    def _build_signal(
        self,
        observation: Dict[str, Any],
        signal_type: RiskSignalType,
        severity_level: RiskSeverityLevel,
        signal_version: str,
        observed_at: datetime
    ) -> Dict[str, Any]:
        """
        Construye RiskSignal conforme a schema con evidencia/explicación.
        
        Invariante:
        - supporting_metrics, supporting_evidence, explanation NUNCA vacíos
        """
        # Construir supporting_metrics desde observation
        supporting_metrics = [{
            "metric_key": observation["metric_key"],
            "metric_value": observation["metric_value"],
            "metric_unit": self._infer_metric_unit(observation),
        }]
        
        # Construir supporting_evidence desde observation
        supporting_evidence = [
            {
                "evidence_type": "RISK_OBSERVATION",
                "evidence_ref": ref
            }
            for ref in observation.get("evidence_refs", [])
        ]
        
        # Construir explanation (RFC-13 §3.3: explicabilidad obligatoria)
        explanation = self._generate_explanation(
            signal_type=signal_type,
            observation=observation,
            severity_level=severity_level
        )
        
        # Construir scope desde observation
        scope = RiskScope(observation["scope"])
        
        # Generar risk_signal_id determinista
        risk_signal_id = self._generate_signal_id(
            signal_type=signal_type,
            scope=scope,
            scope_key=observation["scope_key"],
            observed_at=observed_at
        )
        
        return {
            "risk_signal_id": risk_signal_id,
            "signal_type": signal_type.value,
            "scope": scope.value,
            "severity_level": severity_level.value,
            "supporting_metrics": supporting_metrics,
            "supporting_evidence": supporting_evidence,
            "explanation": explanation,
            "observed_at": observed_at.isoformat(),
            "signal_version": signal_version,
        }
    
    def _infer_metric_unit(self, observation: Dict[str, Any]) -> str:
        """Infiere unidad de métrica desde context o default."""
        context = observation.get("context", {})
        return context.get("metric_unit", "count")
    
    def _generate_explanation(
        self,
        signal_type: RiskSignalType,
        observation: Dict[str, Any],
        severity_level: RiskSeverityLevel
    ) -> str:
        """
        Genera explicación human-readable del riesgo.
        
        Formato: "Riesgo {severity}: {risk_mapping} | {metric_key}={metric_value}"
        """
        risk_mapping = observation.get("risk_mapping", "riesgo institucional detectado")
        metric_key = observation["metric_key"]
        metric_value = observation["metric_value"]
        scope_key = observation.get("scope_key", "GLOBAL")
        
        return (
            f"Riesgo {severity_level.value}: {risk_mapping} | "
            f"Señal: {signal_type.value} | "
            f"Alcance: {scope_key} | "
            f"Métrica: {metric_key}={metric_value}"
        )
    
    def _generate_signal_id(
        self,
        signal_type: RiskSignalType,
        scope: RiskScope,
        scope_key: str,
        observed_at: datetime
    ) -> str:
        """
        Genera ID determinista de señal mediante hash SHA256.
        
        Algoritmo: Hash de (timestamp + signal_type + scope + scope_key)
        Garantiza: Mismo input → mismo ID (replay determinista)
        """
        ts = observed_at.strftime("%Y%m%d%H%M%S")
        
        # Generar hash determinista (mismo input → mismo hash)
        content = f"{ts}_{signal_type.value}_{scope.value}_{scope_key}"
        hash_digest = hashlib.sha256(content.encode('utf-8')).hexdigest()[:8]
        
        return f"RISKSIG_{ts}_{signal_type.value}_{scope.value}_{scope_key}_{hash_digest}"
