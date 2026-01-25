"""
RFC-11 Section 8.3 - Systemic Tests for Conformance Suite
RFC-11 Section 7.2 - Rejection by default on deviation
Tests multi-adapter integration and contract bypass attempts
"""

import pytest
import json
from pathlib import Path
from core.adapter_contracts.v1.conformance import ConformanceSuite
from core.adapter_contracts.v1.interface import IngestDeclaration


class TestRFC11ConformanceSuite:
    """
    RFC-11 Section 8.3 - Conformance systemic tests
    """
    
    @pytest.fixture
    def manifest_schema(self):
        """Load adapter manifest schema"""
        schema_path = Path("contracts/adapter_contracts/v1/adapter_manifest.schema.json")
        with open(schema_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def valid_contract(self):
        """Valid adapter contract"""
        return {
            "adapter_id": "test_adapter",
            "adapter_type": "BANK",
            "supported_formats": ["JSON"],
            "declared_event_capabilities": ["payment"],
            "schema_version": "1.0.0",
            "adapter_version": "1.0.0"
        }
    
    @pytest.fixture
    def conformance_suite(self, valid_contract):
        """Initialize conformance suite"""
        return ConformanceSuite("test_adapter", valid_contract)
    
    def test_contract_tests_schema_compliance(self, conformance_suite, manifest_schema):
        """
        RFC-11 Section 6.1 - Schema compliance test
        """
        sample_declarations = [
            {
                "source_system": "test_adapter",
                "payload_raw": {"data": "test"},
                "payload_format": "JSON",
                "adapter_version": "1.0.0"
            }
        ]
        
        conformance_suite.run_contract_tests(manifest_schema, sample_declarations)
        
        # Check schema compliance passed
        schema_test = next(
            r for r in conformance_suite.contract_tests_results 
            if r["test"] == "schema_compliance"
        )
        assert schema_test["result"] == "PASS"
    
    def test_contract_tests_reject_prohibited_fields(self, conformance_suite, manifest_schema):
        """
        RFC-11 Section 6.1 & 6.3 - Reject prohibited canonical fields
        """
        # Declaration with prohibited field
        prohibited_declaration = {
            "source_system": "test_adapter",
            "payload_raw": {"data": "test"},
            "payload_format": "JSON",
            "adapter_version": "1.0.0",
            "event_type": "malicious"  # PROHIBITED
        }
        
        conformance_suite.run_contract_tests(manifest_schema, [prohibited_declaration])
        
        # Should have failed the prohibited fields check
        prohibited_test = next(
            (r for r in conformance_suite.contract_tests_results 
             if "prohibited_fields_check" in r["test"]),
            None
        )
        assert prohibited_test is not None
        assert prohibited_test["result"] == "FAIL"
    
    def test_behavioral_payload_immutability(self, conformance_suite):
        """
        RFC-11 Section 6.2 - No mutation of payload
        RFC-11 Section 3.2 - Payload must remain raw
        """
        def mock_emit(declaration):
            # Correct behavior: return unchanged
            return declaration
        
        test_payload = {"original": "data"}
        
        conformance_suite.run_behavioral_tests(mock_emit, test_payload)
        
        # Check immutability test passed
        immutability_test = next(
            r for r in conformance_suite.behavioral_tests_results 
            if r["test"] == "payload_immutability"
        )
        assert immutability_test["result"] == "PASS"
    
    def test_behavioral_payload_mutation_detected(self, conformance_suite):
        """
        RFC-11 Section 6.2 - Detect payload mutation
        """
        def malicious_emit(declaration):
            # VIOLATION: mutates payload
            result = declaration.copy()
            result["payload_raw"] = {"mutated": "data"}
            return result
        
        test_payload = {"original": "data"}
        
        conformance_suite.run_behavioral_tests(malicious_emit, test_payload)
        
        # Check immutability test failed
        immutability_test = next(
            r for r in conformance_suite.behavioral_tests_results 
            if r["test"] == "payload_immutability"
        )
        assert immutability_test["result"] == "FAIL"
    
    def test_behavioral_idempotency(self, conformance_suite):
        """
        RFC-11 Section 6.2 - Idempotent behavior on retries
        """
        call_count = 0
        
        def idempotent_emit(declaration):
            nonlocal call_count
            call_count += 1
            return declaration
        
        test_payload = {"data": "test"}
        
        conformance_suite.run_behavioral_tests(idempotent_emit, test_payload)
        
        # Check idempotency test
        idempotency_test = next(
            r for r in conformance_suite.behavioral_tests_results 
            if r["test"] == "idempotency"
        )
        assert idempotency_test["result"] == "PASS"
        assert call_count >= 2  # Called at least twice
    
    def test_negative_reject_prohibited_fields(self, conformance_suite):
        """
        RFC-11 Section 6.3 - Reject writes to canonical fields
        RFC-11 Section 7.2 - Rejection by default
        """
        def mock_emit(declaration):
            return declaration
        
        conformance_suite.run_negative_tests(mock_emit)
        
        # Check all prohibited field rejections passed
        prohibited_tests = [
            r for r in conformance_suite.negative_tests_results 
            if r["test"].startswith("reject_prohibited_field_")
        ]
        
        assert len(prohibited_tests) > 0
        for test in prohibited_tests:
            assert test["result"] == "PASS", f"Failed to reject: {test['test']}"
    
    def test_negative_reject_domain_logic_injection(self, conformance_suite):
        """
        RFC-11 Section 6.3 - Reject domain logic injection
        """
        def correct_emit(declaration):
            # Only propagate allowed fields
            allowed = IngestDeclaration(
                source_system=declaration["source_system"],
                payload_raw=declaration["payload_raw"],
                payload_format=declaration["payload_format"],
                adapter_version=declaration["adapter_version"]
            )
            return allowed.to_dict()
        
        conformance_suite.run_negative_tests(correct_emit)
        
        # Check domain logic rejection
        domain_test = next(
            r for r in conformance_suite.negative_tests_results 
            if r["test"] == "reject_domain_logic_injection"
        )
        assert domain_test["result"] == "PASS"
    
    def test_generate_report_pass(self, conformance_suite, manifest_schema):
        """
        RFC-11 Section 6 & 7.2 - Generate PASS report
        """
        def mock_emit(declaration):
            return IngestDeclaration(
                source_system=declaration["source_system"],
                payload_raw=declaration["payload_raw"],
                payload_format=declaration["payload_format"],
                adapter_version=declaration["adapter_version"]
            ).to_dict()
        
        sample_declarations = [
            {
                "source_system": "test_adapter",
                "payload_raw": {"data": "test"},
                "payload_format": "JSON",
                "adapter_version": "1.0.0"
            }
        ]
        
        conformance_suite.run_contract_tests(manifest_schema, sample_declarations)
        conformance_suite.run_behavioral_tests(mock_emit, {"data": "test"})
        conformance_suite.run_negative_tests(mock_emit)
        
        report = conformance_suite.generate_report()
        
        assert report["adapter_id"] == "test_adapter"
        assert report["overall_result"] == "PASS"
        assert report["contract_tests"]["failed"] == 0
        assert report["behavioral_tests"]["failed"] == 0
        assert report["negative_tests"]["failed"] == 0
    
    def test_generate_report_fail_on_any_failure(self, conformance_suite, manifest_schema):
        """
        RFC-11 Section 7.2 - FAIL if any test fails
        RFC-11 Section 3.4 - Without conformance, no deployment
        """
        def malicious_emit(declaration):
            # Mutates payload - should fail
            result = declaration.copy()
            result["payload_raw"] = {"mutated": "data"}
            return result
        
        sample_declarations = [
            {
                "source_system": "test_adapter",
                "payload_raw": {"data": "test"},
                "payload_format": "JSON",
                "adapter_version": "1.0.0"
            }
        ]
        
        conformance_suite.run_contract_tests(manifest_schema, sample_declarations)
        conformance_suite.run_behavioral_tests(malicious_emit, {"data": "test"})
        conformance_suite.run_negative_tests(malicious_emit)
        
        report = conformance_suite.generate_report()
        
        assert report["overall_result"] == "FAIL"
        assert report["behavioral_tests"]["failed"] > 0
    
    def test_report_schema_validation(self, conformance_suite, manifest_schema):
        """
        RFC-11 Section 6 - Report must conform to schema
        """
        from jsonschema import validate
        
        def mock_emit(declaration):
            return declaration
        
        conformance_suite.run_contract_tests(manifest_schema, [])
        conformance_suite.run_behavioral_tests(mock_emit, {})
        conformance_suite.run_negative_tests(mock_emit)
        
        report = conformance_suite.generate_report()
        
        # Load conformance report schema
        report_schema_path = Path("contracts/adapter_contracts/v1/conformance_report.schema.json")
        with open(report_schema_path, 'r') as f:
            report_schema = json.load(f)
        
        # Validate report against schema
        validate(instance=report, schema=report_schema)
    
    def test_systemic_multiple_adapters(self, manifest_schema):
        """
        RFC-11 Section 8.3 - Test multiple adapters simultaneously
        """
        contracts = [
            {
                "adapter_id": "bank_adapter",
                "adapter_type": "BANK",
                "supported_formats": ["JSON"],
                "declared_event_capabilities": ["payment"],
                "schema_version": "1.0.0",
                "adapter_version": "1.0.0"
            },
            {
                "adapter_id": "erp_adapter",
                "adapter_type": "ERP",
                "supported_formats": ["CSV", "XML"],
                "declared_event_capabilities": ["invoice"],
                "schema_version": "1.0.0",
                "adapter_version": "2.0.0"
            }
        ]
        
        def mock_emit(declaration):
            allowed = IngestDeclaration(
                source_system=declaration.get("source_system", "test"),
                payload_raw=declaration.get("payload_raw", {}),
                payload_format=declaration.get("payload_format", "JSON"),
                adapter_version=declaration.get("adapter_version", "1.0.0")
            )
            return allowed.to_dict()
        
        results = []
        for contract in contracts:
            suite = ConformanceSuite(contract["adapter_id"], contract)
            suite.run_contract_tests(manifest_schema, [])
            suite.run_behavioral_tests(mock_emit, {})
            suite.run_negative_tests(mock_emit)
            results.append(suite.generate_report())
        
        # Both should pass
        assert all(r["overall_result"] == "PASS" for r in results)
        assert len(results) == 2
    
    def test_attempt_contract_bypass_rejected(self, conformance_suite):
        """
        RFC-11 Section 8.3 - Attempt to bypass contract enforcement
        RFC-11 Section 7.2 - Core remains unalterable
        """
        # Attempt to inject prohibited fields
        bypass_attempt = {
            "source_system": "test_adapter",
            "payload_raw": {"data": "test"},
            "payload_format": "JSON",
            "adapter_version": "1.0.0",
            "state": "INJECTED",  # PROHIBITED
            "event_type": "MALICIOUS"  # PROHIBITED
        }
        
        # Interface should reject
        with pytest.raises(ValueError, match="Prohibited canonical fields"):
            IngestDeclaration.validate_no_prohibited_fields(bypass_attempt)
