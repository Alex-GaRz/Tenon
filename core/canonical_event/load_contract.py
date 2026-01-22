"""
Contract loader for CanonicalEvent schema versions.
RFC-01 + RFC-01A implementation.
"""

import json
from pathlib import Path
from typing import Dict, Any


class ContractLoader:
    """Loads JSON Schema contracts by version."""
    
    def __init__(self, contracts_root: Path = None):
        """
        Initialize contract loader.
        
        Args:
            contracts_root: Root path to contracts directory.
                           Defaults to repo contracts/ folder.
        """
        if contracts_root is None:
            # Default to repo structure: core/.. -> contracts/
            contracts_root = Path(__file__).parent.parent.parent / "contracts"
        self.contracts_root = Path(contracts_root)
    
    def load_canonical_event_schema(self, version: str) -> Dict[str, Any]:
        """
        Load CanonicalEvent schema by version.
        
        Args:
            version: Semantic version string (e.g., "1.0.0")
        
        Returns:
            Parsed JSON Schema dictionary
        
        Raises:
            FileNotFoundError: If schema version does not exist
            ValueError: If version format is invalid
        """
        # Validate semver format
        parts = version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"Invalid version format: {version}. Expected semver (e.g., '1.0.0')")
        
        schema_path = (
            self.contracts_root 
            / "canonical_event" 
            / f"v{version}" 
            / "CanonicalEvent.schema.json"
        )
        
        if not schema_path.exists():
            raise FileNotFoundError(
                f"Schema not found for version {version}: {schema_path}"
            )
        
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_lineage_link_schema(self, version: str) -> Dict[str, Any]:
        """
        Load LineageLink schema by version.
        
        Args:
            version: Semantic version string (e.g., "1.0.0")
        
        Returns:
            Parsed JSON Schema dictionary
        
        Raises:
            FileNotFoundError: If schema version does not exist
            ValueError: If version format is invalid
        """
        parts = version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"Invalid version format: {version}")
        
        schema_path = (
            self.contracts_root 
            / "canonical_ids" 
            / f"v{version}" 
            / "LineageLink.schema.json"
        )
        
        if not schema_path.exists():
            raise FileNotFoundError(
                f"LineageLink schema not found for version {version}: {schema_path}"
            )
        
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_identity_decision_schema(self, version: str) -> Dict[str, Any]:
        """
        Load IdentityDecision schema by version.
        
        Args:
            version: Semantic version string (e.g., "1.0.0")
        
        Returns:
            Parsed JSON Schema dictionary
        
        Raises:
            FileNotFoundError: If schema version does not exist
            ValueError: If version format is invalid
        """
        parts = version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"Invalid version format: {version}")
        
        schema_path = (
            self.contracts_root 
            / "canonical_ids" 
            / f"v{version}" 
            / "IdentityDecision.schema.json"
        )
        
        if not schema_path.exists():
            raise FileNotFoundError(
                f"IdentityDecision schema not found for version {version}: {schema_path}"
            )
        
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
