"""
RFC-11 Adapter Contracts v1
"""

from .interface import IngestDeclaration
from .registry import AdapterRegistry
from .conformance import ConformanceSuite

__all__ = [
    "IngestDeclaration",
    "AdapterRegistry",
    "ConformanceSuite",
]
