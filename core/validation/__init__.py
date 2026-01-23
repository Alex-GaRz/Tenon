"""
Validation core module.
RFC-01 + RFC-01A implementation.
"""

from .rejection_evidence import RejectionEvidence
from .validation_result import ValidationResult

__all__ = [
    "RejectionEvidence",
    "ValidationResult",
]
