"""
RFC-11 Section 8.1 - Unit Tests for Adapter Registry
RFC-11 Section 8.2 - Determinism validation
Tests strict schema validation and versioning enforcement
"""

import pytest
import json
from pathlib import Path
from core.adapter_contracts.v1.registry import AdapterRegistry
from core.adapter_contracts.v1.interface import IngestDeclaration


class TestRFC11AdapterRegistry:
    """
    RFC-11 Section 8.1 - Registry unit tests
    """
    
    @pytest.fixture
    def schema_path(self):
        """Path to adapter manifest schema"""
        return Path("contracts/adapter_contracts/v1/adapter_manifest.schema.json")
    
    @pytest.fixture
    def registry(self, schema_path):
        """Initialize registry with schema"""
        reg = AdapterRegistry()
        reg.load_schema(schema_path)
        return reg
    
    @pytest.fixture
    def valid_contract(self):
        """Valid adapter contract"""
        return {
            "adapter_id": "test_bank_adapter",
            "adapter_type": "BANK",
            "supported_formats": ["JSON", "CSV"],
            "declared_event_capabilities": ["payment_received", "payment_sent"],
            "schema_version": "1.0.0",
            "adapter_version": "1.0.0"
        }
    
    def test_register_valid_contract(self, registry, valid_contract):
        """
        RFC-11 Section 3.3 - Valid contract registration
        """
        registry.register_adapter("test_bank_adapter", valid_contract)
        
        retrieved = registry.get_contract("test_bank_adapter")
        assert retrieved == valid_contract
    
    def test_reject_missing_required_field(self, registry, valid_contract):
        """
        RFC-11 Section 8.1 - Reject contract missing required fields
        """
        invalid_contract = valid_contract.copy()
        del invalid_contract["adapter_id"]
        
        with pytest.raises(ValueError, match="Contract validation failed"):
            registry.register_adapter("test_adapter", invalid_contract)
    
    def test_reject_invalid_adapter_type(self, registry, valid_contract):
        """
        RFC-11 Section 8.1 - Reject invalid adapter_type enum
        """
        invalid_contract = valid_contract.copy()
        invalid_contract["adapter_type"] = "INVALID_TYPE"
        
        with pytest.raises(ValueError, match="Contract validation failed"):
            registry.register_adapter("test_adapter", invalid_contract)
    
    def test_reject_invalid_format(self, registry, valid_contract):
        """
        RFC-11 Section 8.1 - Reject invalid supported_formats enum
        """
        invalid_contract = valid_contract.copy()
        invalid_contract["supported_formats"] = ["INVALID_FORMAT"]
        
        with pytest.raises(ValueError, match="Contract validation failed"):
            registry.register_adapter("test_adapter", invalid_contract)
    
    def test_require_versioning(self, registry, valid_contract):
        """
        RFC-11 Section 8.1 - Versioning is mandatory
        """
        # Missing schema_version
        invalid_contract = valid_contract.copy()
        del invalid_contract["schema_version"]
        
        with pytest.raises(ValueError, match="Contract validation failed"):
            registry.register_adapter("test_adapter", invalid_contract)
        
        # Missing adapter_version
        invalid_contract = valid_contract.copy()
        del invalid_contract["adapter_version"]
        
        with pytest.raises(ValueError, match="Contract validation failed"):
            registry.register_adapter("test_adapter", invalid_contract)
    
    def test_reject_additional_properties(self, registry, valid_contract):
        """
        RFC-11 Section 8.1 - Reject contracts with additional properties
        """
        invalid_contract = valid_contract.copy()
        invalid_contract["unexpected_field"] = "should_fail"
        
        with pytest.raises(ValueError, match="Contract validation failed"):
            registry.register_adapter("test_adapter", invalid_contract)
    
    def test_reject_ingest_without_contract(self, registry):
        """
        RFC-11 Section 3.3 - No contract = rejection
        """
        declaration = {
            "source_system": "unregistered_adapter",
            "payload_raw": {"test": "data"},
            "payload_format": "JSON",
            "adapter_version": "1.0.0"
        }
        
        with pytest.raises(ValueError, match="No valid contract"):
            registry.validate_ingest("unregistered_adapter", declaration)
    
    def test_validate_ingest_format_support(self, registry, valid_contract):
        """
        RFC-11 Section 5 - Validate format is supported
        """
        registry.register_adapter("test_bank_adapter", valid_contract)
        
        # Valid format
        valid_declaration = {
            "source_system": "test_bank_adapter",
            "payload_raw": {"test": "data"},
            "payload_format": "JSON",
            "adapter_version": "1.0.0"
        }
        registry.validate_ingest("test_bank_adapter", valid_declaration)
        
        # Unsupported format
        invalid_declaration = {
            "source_system": "test_bank_adapter",
            "payload_raw": {"test": "data"},
            "payload_format": "XML",
            "adapter_version": "1.0.0"
        }
        
        with pytest.raises(ValueError, match="Unsupported format"):
            registry.validate_ingest("test_bank_adapter", invalid_declaration)
    
    def test_validate_source_system_match(self, registry, valid_contract):
        """
        RFC-11 Section 5 - source_system must match adapter_id
        """
        registry.register_adapter("test_bank_adapter", valid_contract)
        
        mismatched_declaration = {
            "source_system": "different_adapter",
            "payload_raw": {"test": "data"},
            "payload_format": "JSON",
            "adapter_version": "1.0.0"
        }
        
        with pytest.raises(ValueError, match="source_system mismatch"):
            registry.validate_ingest("test_bank_adapter", mismatched_declaration)
    
    def test_require_adapter_version_in_declaration(self, registry, valid_contract):
        """
        RFC-11 Section 8.1 - adapter_version required in declaration
        """
        registry.register_adapter("test_bank_adapter", valid_contract)
        
        declaration_no_version = {
            "source_system": "test_bank_adapter",
            "payload_raw": {"test": "data"},
            "payload_format": "JSON"
        }
        
        with pytest.raises(ValueError, match="adapter_version required"):
            registry.validate_ingest("test_bank_adapter", declaration_no_version)
    
    def test_list_adapters(self, registry, valid_contract):
        """
        RFC-11 Section 3.3 - List registered adapters
        """
        assert registry.list_adapters() == []
        
        registry.register_adapter("adapter1", valid_contract)
        assert registry.list_adapters() == ["adapter1"]
        
        contract2 = valid_contract.copy()
        contract2["adapter_id"] = "adapter2"
        registry.register_adapter("adapter2", contract2)
        
        assert set(registry.list_adapters()) == {"adapter1", "adapter2"}
    
    def test_determinism_same_input_same_validation(self, registry, valid_contract):
        """
        RFC-11 Section 8.2 - Deterministic validation
        """
        # Register twice with same contract
        registry.register_adapter("test_adapter", valid_contract)
        
        declaration = {
            "source_system": "test_adapter",
            "payload_raw": {"test": "data"},
            "payload_format": "JSON",
            "adapter_version": "1.0.0"
        }
        
        # Multiple validations should behave identically
        registry.validate_ingest("test_adapter", declaration)
        registry.validate_ingest("test_adapter", declaration)
        registry.validate_ingest("test_adapter", declaration)
        
        # No exception = deterministic acceptance
