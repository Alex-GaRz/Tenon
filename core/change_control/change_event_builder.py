"""
Change Event Builder

Constructs ChangeEvent payloads conforming to the v1 schema contract.

RFC: RFC-12 (Change Control)
Status: EARLY
"""

from datetime import datetime
from typing import Dict, Any

from .change_declaration import ChangeDeclaration, VersionTransition


class ChangeEventBuilder:
    """
    Constructs ChangeEvent payloads conforming to contract v1 schema.
    """
    
    @staticmethod
    def build(declaration: ChangeDeclaration) -> Dict[str, Any]:
        """
        Build ChangeEvent payload from declaration.
        
        Args:
            declaration: ChangeDeclaration to convert to event
            
        Returns:
            Dictionary conforming to change_event.schema.json v1
        """
        versions_affected = [
            {
                "component": vt.component,
                "from_version": vt.from_version,
                "to_version": vt.to_version,
            }
            for vt in declaration.versions_affected
        ]
        
        return {
            "rfc_id": declaration.rfc_id,
            "effective_at": declaration.effective_at.isoformat(),
            "components_impacted": list(declaration.components_impacted),
            "versions_affected": versions_affected,
            "change_type": declaration.change_type.value,
            "compatibility": declaration.compatibility.value,
        }
