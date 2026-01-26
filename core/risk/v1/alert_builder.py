"""
RFC-13 Risk Observability - AlertBuilder
=========================================

Construye RiskAlerts desde RiskAggregates.

PROHIBIDO:
- Side effects (función pura)
- Heurísticas no gobernadas (clasificación determinista a alert_type)
"""

from typing import List, Dict, Any
from datetime import datetime
import hashlib

from core.risk.v1.enums import RiskSeverityLevel, RiskAlertType


class AlertBuilder:
    """
    Construye alertas institucionales desde agregados de riesgo.
    
    Responsabilidades:
    - Clasificar agregados a alert_type determinista
    - Construir RiskAlert con impacto + recomendación + evidencia
    - Asegurar que alertas indican **riesgo**, no "error"
    
    Regla de clasificación determinista (hard-coded institucional):
    - CRITICAL severity → INSTITUTIONAL_BREACH
    - HIGH severity → RISK_ESCALATION
    - MEDIUM severity → EARLY_WARNING
    - LOW severity → no genera alerta (anti-ruido)
    
    Invariantes:
    - Función pura (mismo input → mismo output)
    - Evidencia/impacto/recomendación NUNCA vacíos
    """
    
    def build(
        self,
        aggregate: Dict[str, Any],
        alert_version: str,
        raised_at: datetime
    ) -> List[Dict[str, Any]]:
        """
        Construye alertas desde un RiskAggregate.
        
        Args:
            aggregate: RiskAggregate conforme a schema
            alert_version: Versión del modelo de alerting
            raised_at: Timestamp inyectado de generación
        
        Returns:
            Lista de RiskAlerts conformes a risk_alert.schema.json
        """
        overall_risk_level = RiskSeverityLevel(aggregate["overall_risk_level"])
        
        # Política anti-ruido: no generar alertas para LOW risk
        if overall_risk_level == RiskSeverityLevel.LOW:
            return []
        
        # Clasificar a alert_type determinista
        alert_type = self._classify_alert_type(overall_risk_level)
        
        # Construir alerta
        alert = self._build_alert(
            aggregate=aggregate,
            alert_type=alert_type,
            alert_version=alert_version,
            raised_at=raised_at
        )
        
        return [alert]
    
    def _classify_alert_type(self, severity: RiskSeverityLevel) -> RiskAlertType:
        """
        Clasifica severidad a alert_type (regla institucional hard-coded).
        
        Mapeo determinista:
        - CRITICAL → INSTITUTIONAL_BREACH
        - HIGH → RISK_ESCALATION
        - MEDIUM → EARLY_WARNING
        """
        if severity == RiskSeverityLevel.CRITICAL:
            return RiskAlertType.INSTITUTIONAL_BREACH
        elif severity == RiskSeverityLevel.HIGH:
            return RiskAlertType.RISK_ESCALATION
        elif severity == RiskSeverityLevel.MEDIUM:
            return RiskAlertType.EARLY_WARNING
        else:
            # LOW no debería llegar aquí (filtrado en build())
            return RiskAlertType.EARLY_WARNING
    
    def _build_alert(
        self,
        aggregate: Dict[str, Any],
        alert_type: RiskAlertType,
        alert_version: str,
        raised_at: datetime
    ) -> Dict[str, Any]:
        """
        Construye RiskAlert con evidencia/impacto/recomendación.
        
        Invariante:
        - signal_ids, evidence_refs, potential_impact, operational_recommendation NUNCA vacíos
        """
        # Extraer signal_ids desde drivers
        signal_ids = aggregate.get("drivers", [])
        
        # Si no hay drivers, usar todas las señales (fallback)
        if not signal_ids:
            signal_ids = [sig["risk_signal_id"] for sig in aggregate["risk_profile"]]
        
        # Construir evidence_refs (placeholder: en implementación real, agregar desde señales)
        evidence_refs = [f"AGG_EVIDENCE:{aggregate['aggregate_id']}"]
        
        # Generar potential_impact (determinista desde alert_type + aggregate)
        potential_impact = self._generate_impact(alert_type, aggregate)
        
        # Generar operational_recommendation (determinista desde alert_type)
        operational_recommendation = self._generate_recommendation(alert_type, aggregate)
        
        # Generar alert_id
        alert_id = self._generate_alert_id(alert_type, raised_at)
        
        return {
            "alert_id": alert_id,
            "alert_type": alert_type.value,
            "aggregate_id": aggregate["aggregate_id"],
            "signal_ids": signal_ids,
            "evidence_refs": evidence_refs,
            "potential_impact": potential_impact,
            "operational_recommendation": operational_recommendation,
            "raised_at": raised_at.isoformat(),
            "alert_version": alert_version,
        }
    
    def _generate_impact(
        self,
        alert_type: RiskAlertType,
        aggregate: Dict[str, Any]
    ) -> str:
        """
        Genera descripción de impacto potencial institucional.
        
        Formato determinista por alert_type.
        """
        overall_risk = aggregate["overall_risk_level"]
        driver_count = len(aggregate.get("drivers", []))
        
        impact_templates = {
            RiskAlertType.INSTITUTIONAL_BREACH: (
                f"IMPACTO CRÍTICO: Violación de umbral institucional detectada. "
                f"Riesgo global: {overall_risk}. "
                f"{driver_count} señal(es) crítica(s) activa(s). "
                f"Requiere intervención inmediata para prevenir impacto financiero/operativo/legal."
            ),
            RiskAlertType.RISK_ESCALATION: (
                f"IMPACTO MATERIAL: Riesgo operativo en escalamiento. "
                f"Riesgo global: {overall_risk}. "
                f"{driver_count} señal(es) de alto riesgo activa(s). "
                f"Degradación sistémica en curso; riesgo de impacto financiero o incumplimiento SLA."
            ),
            RiskAlertType.EARLY_WARNING: (
                f"IMPACTO INCIPIENTE: Degradación temprana detectada. "
                f"Riesgo global: {overall_risk}. "
                f"{driver_count} señal(es) de riesgo medio activa(s). "
                f"Ventana de oportunidad para prevenir escalamiento."
            ),
        }
        
        return impact_templates.get(
            alert_type,
            f"Impacto institucional: riesgo {overall_risk} con {driver_count} driver(s)."
        )
    
    def _generate_recommendation(
        self,
        alert_type: RiskAlertType,
        aggregate: Dict[str, Any]
    ) -> str:
        """
        Genera recomendación operativa para intervención humana.
        
        Formato determinista por alert_type.
        """
        recommendation_templates = {
            RiskAlertType.INSTITUTIONAL_BREACH: (
                "ACCIÓN INMEDIATA: (1) Revisar señales críticas en drivers. "
                "(2) Activar protocolo de respuesta a incidente institucional. "
                "(3) Escalar a comité de riesgo. "
                "(4) Documentar evidencia para auditoría."
            ),
            RiskAlertType.RISK_ESCALATION: (
                "ACCIÓN PRIORITARIA: (1) Analizar tendencia de señales de alto riesgo. "
                "(2) Revisar cambios recientes (RFC-12). "
                "(3) Evaluar necesidad de rollback o mitigación. "
                "(4) Monitorear evolución en próximas ventanas."
            ),
            RiskAlertType.EARLY_WARNING: (
                "ACCIÓN PREVENTIVA: (1) Investigar señales de riesgo medio. "
                "(2) Identificar causas raíz (discrepancias, correlación, estados). "
                "(3) Planificar intervención antes de escalamiento. "
                "(4) Documentar hallazgos para gobernanza."
            ),
        }
        
        return recommendation_templates.get(
            alert_type,
            "Revisar agregado de riesgo y señales activas. Escalar según política institucional."
        )
    
    def _generate_alert_id(self, alert_type: RiskAlertType, raised_at: datetime) -> str:
        """
        Genera ID determinista de alerta mediante hash SHA256.
        
        Algoritmo: Hash de (alert_type + timestamp)
        Garantiza: Mismo input → mismo ID (replay determinista)
        """
        ts = raised_at.strftime("%Y%m%d%H%M%S")
        
        # Generar hash determinista
        content = f"{alert_type.value}_{ts}"
        hash_digest = hashlib.sha256(content.encode('utf-8')).hexdigest()[:8]
        
        return f"ALERT_{alert_type.value}_{ts}_{hash_digest}"
