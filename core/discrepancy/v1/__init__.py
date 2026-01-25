"""
RFC-06: Discrepancy Taxonomy - Public API v1

This module exposes the public API for discrepancy detection and classification.
No side-effects are executed on import.
"""

from core.discrepancy.v1.enums import DiscrepancyType, SeverityHint
from core.discrepancy.v1.models import Discrepancy
from core.discrepancy.v1.detector import DiscrepancyDetector
from core.discrepancy.v1.store import AppendOnlyDiscrepancyStore

__all__ = [
    "DiscrepancyType",
    "SeverityHint",
    "Discrepancy",
    "DiscrepancyDetector",
    "AppendOnlyDiscrepancyStore",
]
