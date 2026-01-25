"""
RFC-11 Section 3.3 & 5 - Adapter Registry
Manages adapter contract definitions and validation
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError


class AdapterRegistry:
    """
    RFC-11 Section 3.3 - Registry for adapter contracts
    RFC-11 Section 5 - Contract validation (step 4)
    """
    
    def __init__(self, contracts_base_path: Optional[Path] = None):
        """
        Initialize registry
        
        Args:
            contracts_base_path: Base path for contracts (default: /contracts/adapters/)
        """
        if contracts_base_path is None:
            # RFC-11 Section 4.3 - Default location
            contracts_base_path = Path("contracts/adapter_contracts")
        
        self.contracts_base_path = Path(contracts_base_path)
        self._contracts: Dict[str, Dict[str, Any]] = {}
        self._schema: Optional[Dict[str, Any]] = None
    
    def load_schema(self, schema_path: Path) -> None:
        """
        Load adapter manifest schema
        
        Args:
            schema_path: Path to adapter_manifest.schema.json
        """
        with open(schema_path, 'r') as f:
            self._schema = json.load(f)
    
    def register_adapter(self, adapter_id: str, contract: Dict[str, Any]) -> None:
        """
        RFC-11 Section 3.3 - Register adapter contract
        
        Args:
            adapter_id: Adapter identifier
            contract: Contract definition
            
        Raises:
            ValueError: If contract invalid or schema not loaded
        """
        if self._schema is None:
            raise ValueError("Schema not loaded. Call load_schema() first.")
        
        # Validate against schema
        try:
            validate(instance=contract, schema=self._schema)
        except ValidationError as e:
            raise ValueError(f"Contract validation failed: {e.message}")
        
        # RFC-11 Section 3.3 - Store valid contract
        self._contracts[adapter_id] = contract
    
    def get_contract(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve adapter contract
        
        Args:
            adapter_id: Adapter identifier
            
        Returns:
            Contract or None if not found
        """
        return self._contracts.get(adapter_id)
    
    def validate_ingest(self, adapter_id: str, declaration: Dict[str, Any]) -> None:
        """
        RFC-11 Section 5 - Validate ingestion against contract
        RFC-11 Section 3.3 - Without valid contract, ingestion rejected
        
        Args:
            adapter_id: Adapter identifier
            declaration: Ingest declaration
            
        Raises:
            ValueError: If validation fails
        """
        contract = self.get_contract(adapter_id)
        
        # RFC-11 Section 3.3 - No contract = rejection
        if contract is None:
            raise ValueError(
                f"No valid contract for adapter: {adapter_id}. Ingestion rejected."
            )
        
        # Validate source_system matches
        if declaration.get("source_system") != adapter_id:
            raise ValueError(
                f"source_system mismatch: expected {adapter_id}, got {declaration.get('source_system')}"
            )
        
        # Validate payload_format is supported
        payload_format = declaration.get("payload_format")
        supported_formats = contract.get("supported_formats", [])
        
        if payload_format not in supported_formats:
            raise ValueError(
                f"Unsupported format {payload_format}. Adapter supports: {supported_formats}"
            )
        
        # Validate adapter_version present
        if not declaration.get("adapter_version"):
            raise ValueError("adapter_version required")
    
    def list_adapters(self) -> list:
        """
        List all registered adapters
        
        Returns:
            List of adapter IDs
        """
        return list(self._contracts.keys())
