"""
RFC-11 Section 6 - Conformance Suite
RFC-11 Section 3.4 - Verification gatekeeper
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Callable
from jsonschema import validate, ValidationError


class ConformanceSuite:
    """
    RFC-11 Section 6 - Conformance verification suite
    RFC-11 Section 3.4 - Gatekeeper for deployment/ingestion
    """
    
    def __init__(self, adapter_id: str, adapter_contract: Dict[str, Any]):
        """
        Initialize conformance suite
        
        Args:
            adapter_id: Adapter under test
            adapter_contract: Adapter contract definition
        """
        self.adapter_id = adapter_id
        self.adapter_contract = adapter_contract
        self.test_suite_version = "1.0.0"
        
        # Test results storage
        self.contract_tests_results: List[Dict[str, Any]] = []
        self.behavioral_tests_results: List[Dict[str, Any]] = []
        self.negative_tests_results: List[Dict[str, Any]] = []
    
    def run_contract_tests(
        self, 
        manifest_schema: Dict[str, Any],
        sample_declarations: List[Dict[str, Any]]
    ) -> None:
        """
        RFC-11 Section 6.1 - Contract compliance tests
        
        Tests:
        - Schema compliance
        - Version validation
        - Absence of prohibited fields
        
        Args:
            manifest_schema: Adapter manifest schema
            sample_declarations: Sample ingest declarations to test
        """
        # Test 1: Schema compliance
        try:
            validate(instance=self.adapter_contract, schema=manifest_schema)
            self.contract_tests_results.append({
                "test": "schema_compliance",
                "result": "PASS",
                "message": "Contract complies with schema"
            })
        except ValidationError as e:
            self.contract_tests_results.append({
                "test": "schema_compliance",
                "result": "FAIL",
                "message": f"Schema validation failed: {e.message}"
            })
        
        # Test 2: Version fields present
        required_versions = ["schema_version", "adapter_version"]
        for field in required_versions:
            if field in self.adapter_contract:
                self.contract_tests_results.append({
                    "test": f"version_field_{field}",
                    "result": "PASS",
                    "message": f"{field} present"
                })
            else:
                self.contract_tests_results.append({
                    "test": f"version_field_{field}",
                    "result": "FAIL",
                    "message": f"{field} missing"
                })
        
        # Test 3: Prohibited fields absent in declarations
        from .interface import IngestDeclaration
        
        for idx, declaration in enumerate(sample_declarations):
            try:
                IngestDeclaration.validate_no_prohibited_fields(declaration)
                self.contract_tests_results.append({
                    "test": f"prohibited_fields_check_{idx}",
                    "result": "PASS",
                    "message": "No prohibited fields"
                })
            except ValueError as e:
                self.contract_tests_results.append({
                    "test": f"prohibited_fields_check_{idx}",
                    "result": "FAIL",
                    "message": str(e)
                })
    
    def run_behavioral_tests(
        self,
        emit_function: Callable[[Dict[str, Any]], Dict[str, Any]],
        test_payload: Any
    ) -> None:
        """
        RFC-11 Section 6.2 - Behavioral tests
        
        Tests:
        - No mutation of payload
        - Idempotency on retries
        
        Args:
            emit_function: Adapter's emit function to test
            test_payload: Test payload
        """
        # Test 1: No mutation of payload
        original_payload = test_payload.copy() if isinstance(test_payload, dict) else test_payload
        
        declaration = {
            "source_system": self.adapter_id,
            "payload_raw": test_payload,
            "payload_format": "JSON",
            "adapter_version": self.adapter_contract.get("adapter_version", "1.0.0")
        }
        
        try:
            result = emit_function(declaration)
            
            # Check payload unchanged
            if result.get("payload_raw") == original_payload:
                self.behavioral_tests_results.append({
                    "test": "payload_immutability",
                    "result": "PASS",
                    "message": "Payload not mutated"
                })
            else:
                self.behavioral_tests_results.append({
                    "test": "payload_immutability",
                    "result": "FAIL",
                    "message": "Payload was mutated"
                })
        except Exception as e:
            self.behavioral_tests_results.append({
                "test": "payload_immutability",
                "result": "FAIL",
                "message": f"Error during test: {str(e)}"
            })
        
        # Test 2: Idempotency
        try:
            result1 = emit_function(declaration)
            result2 = emit_function(declaration)
            
            if result1 == result2:
                self.behavioral_tests_results.append({
                    "test": "idempotency",
                    "result": "PASS",
                    "message": "Idempotent behavior confirmed"
                })
            else:
                self.behavioral_tests_results.append({
                    "test": "idempotency",
                    "result": "FAIL",
                    "message": "Non-idempotent behavior detected"
                })
        except Exception as e:
            self.behavioral_tests_results.append({
                "test": "idempotency",
                "result": "FAIL",
                "message": f"Error during test: {str(e)}"
            })
    
    def run_negative_tests(
        self,
        emit_function: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        RFC-11 Section 6.3 - Negative tests
        
        Tests:
        - Rejection of canonical field writes
        - Rejection of domain logic injection
        
        Args:
            emit_function: Adapter's emit function to test
        """
        from .interface import IngestDeclaration
        
        # Test 1: Reject canonical field writes
        prohibited_fields = IngestDeclaration.PROHIBITED_FIELDS
        
        for field in prohibited_fields:
            malicious_declaration = {
                "source_system": self.adapter_id,
                "payload_raw": {"data": "test"},
                "payload_format": "JSON",
                "adapter_version": "1.0.0",
                field: "malicious_value"
            }
            
            try:
                # Should raise ValueError
                IngestDeclaration.validate_no_prohibited_fields(malicious_declaration)
                self.negative_tests_results.append({
                    "test": f"reject_prohibited_field_{field}",
                    "result": "FAIL",
                    "message": f"Failed to reject prohibited field: {field}"
                })
            except ValueError:
                self.negative_tests_results.append({
                    "test": f"reject_prohibited_field_{field}",
                    "result": "PASS",
                    "message": f"Correctly rejected prohibited field: {field}"
                })
        
        # Test 2: Reject domain logic injection attempt
        domain_logic_declaration = {
            "source_system": self.adapter_id,
            "payload_raw": {"data": "test"},
            "payload_format": "JSON",
            "adapter_version": "1.0.0",
            "custom_business_rule": "inject_logic"
        }
        
        # Adapter should not process custom fields beyond contract
        try:
            result = emit_function(domain_logic_declaration)
            # Check that custom field was not propagated
            if "custom_business_rule" not in result:
                self.negative_tests_results.append({
                    "test": "reject_domain_logic_injection",
                    "result": "PASS",
                    "message": "Domain logic injection prevented"
                })
            else:
                self.negative_tests_results.append({
                    "test": "reject_domain_logic_injection",
                    "result": "FAIL",
                    "message": "Domain logic injection not prevented"
                })
        except Exception as e:
            self.negative_tests_results.append({
                "test": "reject_domain_logic_injection",
                "result": "PASS",
                "message": f"Rejected with exception: {str(e)}"
            })
    
    def generate_report(self) -> Dict[str, Any]:
        """
        RFC-11 Section 6 - Generate conformance report
        RFC-11 Section 7.2 - Evidence of acceptance/rejection
        
        Returns:
            Conformance report
        """
        contract_passed = sum(
            1 for r in self.contract_tests_results if r["result"] == "PASS"
        )
        contract_failed = sum(
            1 for r in self.contract_tests_results if r["result"] == "FAIL"
        )
        
        behavioral_passed = sum(
            1 for r in self.behavioral_tests_results if r["result"] == "PASS"
        )
        behavioral_failed = sum(
            1 for r in self.behavioral_tests_results if r["result"] == "FAIL"
        )
        
        negative_passed = sum(
            1 for r in self.negative_tests_results if r["result"] == "PASS"
        )
        negative_failed = sum(
            1 for r in self.negative_tests_results if r["result"] == "FAIL"
        )
        
        # RFC-11 Section 3.4 - Without conformance, no deployment/ingestion
        overall_result = "PASS" if (
            contract_failed == 0 and 
            behavioral_failed == 0 and 
            negative_failed == 0
        ) else "FAIL"
        
        report = {
            "adapter_id": self.adapter_id,
            "test_suite_version": self.test_suite_version,
            "contract_tests": {
                "passed": contract_passed,
                "failed": contract_failed,
                "details": self.contract_tests_results
            },
            "behavioral_tests": {
                "passed": behavioral_passed,
                "failed": behavioral_failed,
                "details": self.behavioral_tests_results
            },
            "negative_tests": {
                "passed": negative_passed,
                "failed": negative_failed,
                "details": self.negative_tests_results
            },
            "overall_result": overall_result
        }
        
        return report
    
    def save_report(self, output_path: Path) -> None:
        """
        Save conformance report to file
        
        Args:
            output_path: Path to save report
        """
        report = self.generate_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
