"""
Version Resolver

Deterministic version resolution based on effective dates for TENON system.

RFC: RFC-12 (Change Control)
Status: EARLY
"""

from datetime import datetime
from typing import Optional

from .version_registry import VersionRegistry, VersionEntry


class VersionResolver:
    """
    Provides deterministic version resolution based on timestamps.
    
    Resolution algorithm:
        if event.timestamp < change.effective_at:
            use original_version
        else:
            use new_version
    """
    
    def __init__(self, registry: VersionRegistry):
        """
        Initialize resolver with a version registry.
        
        Args:
            registry: VersionRegistry containing component versions
        """
        self.registry = registry
    
    def resolve(
        self,
        component: str,
        timestamp: datetime
    ) -> Optional[VersionEntry]:
        """
        Resolve which version should be used for a component at a given timestamp.
        
        Algorithm:
        1. Get all versions for component from registry
        2. Filter versions where effective_at <= timestamp
        3. Return latest version that was active at that timestamp
        
        Args:
            component: Component identifier
            timestamp: Timestamp to resolve version for
            
        Returns:
            VersionEntry for the active version, or None if component
            didn't exist or no version was active at that timestamp
        """
        versions = self.registry.get_versions(component)
        
        if not versions:
            return None
        
        active_versions = [
            v for v in versions
            if v.effective_at <= timestamp
        ]
        
        if not active_versions:
            return None
        
        return active_versions[-1]
