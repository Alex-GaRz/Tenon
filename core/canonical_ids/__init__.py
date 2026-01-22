"""
Canonical IDs core module.
RFC-01A implementation.
"""

from .idempotency_key import IdempotencyKeyGenerator
from .identity_decider import IdentityDecider, IdentityDecision, IdentityMatch
from .lineage_validator import LineageValidator

__all__ = [
    "IdempotencyKeyGenerator",
    "IdentityDecider",
    "IdentityDecision",
    "IdentityMatch",
    "LineageValidator",
]
