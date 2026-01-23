"""
Schema validator for CanonicalEvent.
RFC-01 + RFC-01A implementation.

Validates events against JSON Schema contracts (version-specific).
"""

from typing import Dict, Any, List
import jsonschema
from jsonschema import Draft7Validator, RefResolver

from .load_contract import ContractLoader


class ValidationError:
    """Represents a single validation error."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
    
    def __repr__(self):
        return f"ValidationError(field='{self.field}', message='{self.message}')"


class SchemaValidationResult:
    """Result of schema validation."""
    
    def __init__(self, valid: bool, errors: List[ValidationError] = None):
        self.valid = valid
        self.errors = errors or []
    
    def __bool__(self):
        return self.valid
    
    def __repr__(self):
        if self.valid:
            return "SchemaValidationResult(valid=True)"
        return f"SchemaValidationResult(valid=False, errors={len(self.errors)})"


class SchemaValidator:
    """Validates CanonicalEvent against JSON Schema contract."""
    
    def __init__(self, contract_loader: ContractLoader = None):
        """
        Initialize schema validator.
        
        Args:
            contract_loader: ContractLoader instance. If None, creates default.
        """
        self.contract_loader = contract_loader or ContractLoader()
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        # Cache for dependency schemas (like LineageLink)
        self._dependency_cache: Dict[str, Any] = {}
    
    def validate(self, event: Dict[str, Any]) -> SchemaValidationResult:
        """
        Validate a CanonicalEvent against its schema version.
        
        Args:
            event: Event dictionary to validate
        
        Returns:
            SchemaValidationResult with validation status and errors
        """
        # Extract schema_version from event
        schema_version = event.get("schema_version")
        if not schema_version:
            return SchemaValidationResult(
                valid=False,
                errors=[ValidationError(
                    field="schema_version",
                    message="Missing required field: schema_version"
                )]
            )
        
        # Load schema (with caching)
        try:
            schema = self._get_schema(schema_version)
        except (FileNotFoundError, ValueError) as e:
            return SchemaValidationResult(
                valid=False,
                errors=[ValidationError(
                    field="schema_version",
                    message=f"Invalid schema version: {e}",
                    value=schema_version
                )]
            )
        
        # --- FIX: Offline Resolution Logic ---
        # The schema uses an absolute $id (https://tenon.canonical/...)
        # but relative refs ($ref: ../../../...). This causes jsonschema to try
        # fetching from the network. We must provide a local store map.
        
        # 1. Load the dependency (LineageLink)
        # We assume dependencies track the main version or are v1.0.0
        # For this implementation, we explicitly load v1.0.0 as referenced in the contract.
        if "lineage_v1.0.0" not in self._dependency_cache:
            self._dependency_cache["lineage_v1.0.0"] = (
                self.contract_loader.load_lineage_link_schema("1.0.0")
            )
        lineage_schema = self._dependency_cache["lineage_v1.0.0"]

        # 2. Map the calculated URI to the local schema
        # Base ID: https://tenon.canonical/schemas/canonical_event/v1.0.0/CanonicalEvent.schema.json
        # Ref: ../../../canonical_ids/v1.0.0/LineageLink.schema.json
        # Resolved URI: https://tenon.canonical/canonical_ids/v1.0.0/LineageLink.schema.json
        lineage_uri = "https://tenon.canonical/canonical_ids/v1.0.0/LineageLink.schema.json"
        
        store = {
            lineage_uri: lineage_schema
        }

        # 3. Create Resolver
        resolver = RefResolver(
            base_uri=schema.get("$id", ""),
            referrer=schema,
            store=store
        )
        # -------------------------------------

        # Validate against schema using the resolver
        validator = Draft7Validator(schema, resolver=resolver)
        errors = []
        
        for error in validator.iter_errors(event):
            # Extract field path
            field_path = ".".join(str(p) for p in error.path) if error.path else error.validator
            
            errors.append(ValidationError(
                field=field_path,
                message=error.message,
                value=error.instance if hasattr(error, 'instance') else None
            ))
        
        return SchemaValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )
    
    def _get_schema(self, version: str) -> Dict[str, Any]:
        """
        Get schema by version (with caching).
        
        Args:
            version: Schema version
        
        Returns:
            Schema dictionary
        """
        if version not in self._schema_cache:
            self._schema_cache[version] = (
                self.contract_loader.load_canonical_event_schema(version)
            )
        return self._schema_cache[version]