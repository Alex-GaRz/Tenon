"""
RFC-13 Risk Observability - Core Domain
========================================

Dominio canónico `risk` - Observabilidad institucional basada en riesgo.

Exports estables (sin side effects, solo functional core):
- Enums: RiskSeverityLevel, RiskScope, RiskSignalType, RiskAlertType
- Compute: SignalComputer, RiskAssessor, AlertBuilder
- Stores: AppendOnlySignalStore, AppendOnlyAggregateStore, AppendOnlyAlertStore
- Thresholds: ThresholdEvaluator
- Views: build_executive_view, build_operational_view
"""

from core.risk.v1.enums import (
    RiskSeverityLevel,
    RiskScope,
    RiskSignalType,
    RiskAlertType,
)

from core.risk.v1.thresholds import ThresholdEvaluator

from core.risk.v1.signal_computer import SignalComputer

from core.risk.v1.risk_assessor import RiskAssessor

from core.risk.v1.alert_builder import AlertBuilder

from core.risk.v1.stores import (
    AppendOnlySignalStore,
    AppendOnlyAggregateStore,
    AppendOnlyAlertStore,
)

from core.risk.v1.views import (
    build_executive_view,
    build_operational_view,
)

__all__ = [
    # Enums
    "RiskSeverityLevel",
    "RiskScope",
    "RiskSignalType",
    "RiskAlertType",
    # Compute
    "SignalComputer",
    "RiskAssessor",
    "AlertBuilder",
    # Stores
    "AppendOnlySignalStore",
    "AppendOnlyAggregateStore",
    "AppendOnlyAlertStore",
    # Thresholds
    "ThresholdEvaluator",
    # Views
    "build_executive_view",
    "build_operational_view",
]
