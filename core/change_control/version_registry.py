"""
Version Registry

Registry for managing coexisting versions of components in TENON system.

RFC: RFC-12 (Change Control)
Status: EARLY
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class VersionEntry:
    """
    Entry in the version registry for a specific component version.
    
    Attributes:
        component: Component identifier
        version: Version identifier (semver)
        effective_at: When this version becomes active
        description: Human-readable version description
    """
    component: str
    version: str
    effective_at: datetime
    description: str = ""


class VersionRegistry:
    """
    Registry maintaining awareness of all coexisting versions.
    """
    
    def __init__(self):
        """Initialize empty version registry."""
        self._versions: Dict[str, List[VersionEntry]] = {}
    
    def register(
        self,
        component: str,
        version: str,
        effective_at: datetime,
        description: str = ""
    ) -> None:
        """
        Register a new version for a component.
        
        Args:
            component: Component identifier
            version: Version identifier (semver)
            effective_at: When this version becomes active
            description: Optional description
        """
        if component not in self._versions:
            self._versions[component] = []
        
        entry = VersionEntry(
            component=component,
            version=version,
            effective_at=effective_at,
            description=description
        )
        
        self._versions[component].append(entry)
        self._versions[component].sort(key=lambda v: v.effective_at)
    
    def get_versions(self, component: str) -> List[VersionEntry]:
        """
        Get all registered versions for a component.
        
        Args:
            component: Component identifier
            
        Returns:
            List of VersionEntry objects, sorted by effective_at
        """
        return list(self._versions.get(component, []))
