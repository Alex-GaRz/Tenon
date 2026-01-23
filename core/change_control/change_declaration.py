"""
Change Declaration

Declarative structure for change control in TENON system.

RFC: RFC-12 (Change Control)
Status: EARLY
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from .change_types import ChangeType, Compatibility


@dataclass(frozen=True)
class VersionTransition:
    """
    Represents a version transition for a specific component.
    
    Attributes:
        component: Component identifier
        from_version: Original version (semver)
        to_version: New version (semver)
    """
    component: str
    from_version: str
    to_version: str


@dataclass(frozen=True)
class ChangeDeclaration:
    """
    Declarative structure for a change control event.
    
    Attributes:
        rfc_id: RFC identifier authorizing this change
        change_type: Classification (Patch, Minor, Major)
        compatibility: Compatibility impact
        effective_at: Timestamp when change becomes active (ISO 8601 UTC)
        components_impacted: List of affected system components
        versions_affected: List of version transitions
    """
    rfc_id: str
    change_type: ChangeType
    compatibility: Compatibility
    effective_at: datetime
    components_impacted: List[str]
    versions_affected: List[VersionTransition]
