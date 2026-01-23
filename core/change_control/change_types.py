"""
Change Control Type Enumerations

Institutional enumerations for classifying changes and their compatibility impact
in the TENON system.

RFC: RFC-12 (Change Control)
Status: EARLY
"""

from enum import Enum


class ChangeType(Enum):
    """
    Classification of changes following semantic versioning principles.
    
    Patch: Bug fixes, documentation corrections, no functional changes
    Minor: New functionality, non-breaking additions, optional features
    Major: Breaking changes, API contract modifications, schema evolution
    """
    PATCH = "Patch"
    MINOR = "Minor"
    MAJOR = "Major"


class Compatibility(Enum):
    """
    Compatibility impact classification for changes.
    
    BACKWARD_COMPATIBLE: Old code works with new version
    FORWARD_COMPATIBLE: New code can handle old data/schemas
    BREAKING: Requires migration, not compatible with previous versions
    
    RULE: If change_type == Major, then compatibility MUST be BREAKING
    """
    BACKWARD_COMPATIBLE = "backward-compatible"
    FORWARD_COMPATIBLE = "forward-compatible"
    BREAKING = "breaking"
