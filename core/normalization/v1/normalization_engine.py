"""
RFC-03 Normalization Engine: Deterministic raw→canonical transformation.

GUARANTEES:
- Strong determinism: no clock, no external APIs, no randomness
- UNKNOWN for fields not inferible by explicit rule
- Diff always created and stored
- normalizer_version mandatory
"""

import json
from typing import Dict, Any, Optional, Tuple

from core.ingest.v1.raw_payload_store import RawPayloadStore
from .rule_registry import RuleRegistry
from .diff_store import DiffStore


NORMALIZER_VERSION = "1.0.0"


def normalize_ingest_record(
    ingest_record: Dict[str, Any],
    raw_store: RawPayloadStore,
    rule_registry: RuleRegistry,
    diff_store: DiffStore
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Normalize ingest record to canonical event.
    
    Args:
        ingest_record: IngestRecord from RFC-02
        raw_store: Raw payload store
        rule_registry: Rule registry
        diff_store: Diff store
    
    Returns:
        Tuple of (canonical_event, normalization_result)
        - canonical_event: None if no rule or normalization failed
        - normalization_result: Always present (conforming to schema)
    
    Invariants:
        - Deterministic: no clock, no random, no external calls
        - Fields not in mapping → not populated (or "UNKNOWN")
        - Diff always created
        - normalizer_version always present
    """
    warnings: list[str] = []
    applied_rules: list[Dict[str, Any]] = []
    
    # Step 1: Retrieve raw payload
    try:
        raw_bytes = raw_store.get(ingest_record["raw_pointer"])
    except KeyError:
        warnings.append(f"Raw payload not found: {ingest_record['raw_pointer']}")
        return _create_failed_result(ingest_record, warnings, diff_store)
    
    # Step 2: Select normalization rule (exact match only)
    rule = rule_registry.get_rule(
        source_system=ingest_record["source_system"],
        raw_format=ingest_record["raw_format"],
        schema_hint=ingest_record.get("schema_hint", "default")
    )
    
    if rule is None:
        warnings.append(
            f"No normalization rule for "
            f"({ingest_record['source_system']}, {ingest_record['raw_format']}, default)"
        )
        return _create_failed_result(ingest_record, warnings, diff_store)
    
    # Step 3: Parse raw payload
    try:
        raw_data = _parse_raw(raw_bytes, ingest_record["raw_format"])
    except Exception as e:
        warnings.append(f"Failed to parse raw payload: {type(e).__name__}: {str(e)}")
        return _create_failed_result(ingest_record, warnings, diff_store)
    
    # Step 4: Apply mapping (deterministic)
    canonical_event = {}
    mappings_applied = []
    
    for mapping in rule["mapping"]:
        raw_path = mapping["raw_path"]
        canonical_path = mapping["canonical_path"]
        
        # Simple field extraction (no complex JSONPath for now)
        value = _extract_field(raw_data, raw_path)
        
        if value is not None:
            _set_field(canonical_event, canonical_path, value)
            mappings_applied.append({
                "raw_path": raw_path,
                "canonical_path": canonical_path
            })
        else:
            # Field not inferible → "UNKNOWN"
            _set_field(canonical_event, canonical_path, "UNKNOWN")
            warnings.append(f"Field {raw_path} not found, set {canonical_path}=UNKNOWN")
    
    # Step 5: Set event_id (use from ingest_record if available)
    canonical_event["event_id"] = ingest_record.get("event_id", "UNKNOWN")
    
    # Step 6: Create diff document
    diff_document = {
        "raw_pointer": ingest_record["raw_pointer"],
        "applied_rule": {
            "rule_id": rule["rule_id"],
            "rule_version": rule["rule_version"],
            "normalizer_version": rule["normalizer_version"]
        },
        "mappings_applied": mappings_applied,
        "warnings": warnings
    }
    
    diff_reference = diff_store.append(diff_document)
    
    # Step 7: Build normalization result
    applied_rules.append({
        "rule_id": rule["rule_id"],
        "rule_version": rule["rule_version"],
        "normalizer_version": rule["normalizer_version"]
    })
    
    normalization_result = {
        "event_id": canonical_event.get("event_id"),
        "normalizer_version": NORMALIZER_VERSION,
        "applied_rules": applied_rules,
        "warnings": warnings,
        "diff_reference": diff_reference
    }
    
    return (canonical_event, normalization_result)


def _create_failed_result(
    ingest_record: Dict[str, Any],
    warnings: list[str],
    diff_store: DiffStore
) -> Tuple[None, Dict[str, Any]]:
    """Create normalization result for failed normalization."""
    
    # Create minimal diff document
    diff_document = {
        "raw_pointer": ingest_record["raw_pointer"],
        "applied_rule": {
            "rule_id": "NONE",
            "rule_version": "NONE",
            "normalizer_version": NORMALIZER_VERSION
        },
        "mappings_applied": [],
        "warnings": warnings
    }
    
    diff_reference = diff_store.append(diff_document)
    
    normalization_result = {
        "event_id": None,
        "normalizer_version": NORMALIZER_VERSION,
        "applied_rules": [],
        "warnings": warnings,
        "diff_reference": diff_reference
    }
    
    return (None, normalization_result)


def _parse_raw(raw_bytes: bytes, raw_format: str) -> Dict[str, Any]:
    """Parse raw payload based on format."""
    if raw_format == "json":
        return json.loads(raw_bytes.decode("utf-8"))
    else:
        raise ValueError(f"Unsupported raw_format: {raw_format}")


def _extract_field(data: Dict[str, Any], path: str) -> Any:
    """Extract field from data using simple dot notation."""
    keys = path.split(".")
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value


def _set_field(data: Dict[str, Any], path: str, value: Any) -> None:
    """Set field in data using simple dot notation."""
    keys = path.split(".")
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
