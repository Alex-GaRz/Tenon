"""
RFC-02 Ingest Entrypoint: Preserve raw observations with idempotency evaluation.

PROTOCOL:
1. Append raw payload to immutable store
2. Evaluate idempotency via RFC-01A (ALWAYS executed)
3. Create and append IngestRecord (even for duplicates/ambiguous)

GUARANTEES:
- Crudo always preserved (append-only)
- Idempotency decision always recorded
- Timestamps never collapsed (observed_at, source_timestamp, ingested_at separate)
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .raw_payload_store import RawPayloadStore
from .ingest_record_store import IngestRecordStore
from core.canonical_ids.idempotency_key import IdempotencyKeyGenerator
from core.canonical_ids.identity_decider import IdentityDecider, IdentityDecision


# In-memory registry of seen events for idempotency (simple implementation)
_SEEN_EVENTS: Dict[str, str] = {}  # idempotency_key -> event_id


def ingest_raw_observation(
    raw_bytes: bytes,
    *,
    source_system: str,
    source_connector: str,
    source_environment: str,
    observed_at: str,
    source_timestamp: Optional[str],
    raw_format: str,
    adapter_version: str,
    raw_payload_store: RawPayloadStore,
    ingest_record_store: IngestRecordStore,
    _clock: Optional[datetime] = None  # Injectable for deterministic tests
) -> Dict[str, Any]:
    """
    Ingest raw observation with idempotency evaluation.
    
    Args:
        raw_bytes: Raw payload bytes
        source_system: Originating system identifier
        source_connector: Connector/adapter identifier
        source_environment: Environment (prod/staging/dev)
        observed_at: RFC3339 timestamp when observation was captured
        source_timestamp: RFC3339 timestamp from source (may be null)
        raw_format: Format identifier (json/csv/pdf/etc)
        adapter_version: Version of adapter
        raw_payload_store: Raw payload store instance
        ingest_record_store: Ingest record store instance
        _clock: Injectable clock for deterministic tests (internal)
    
    Returns:
        IngestRecord dict conforming to schema
    
    Invariants:
        - Raw payload always appended (idempotent)
        - Idempotency ALWAYS evaluated via RFC-01A
        - IngestRecord ALWAYS created (even for duplicates)
        - Timestamps never collapsed
    """
    warnings: list[str] = []
    
    # Step 1: Append raw payload (idempotent)
    raw_payload_hash, raw_pointer, raw_size_bytes = raw_payload_store.append(
        raw_bytes, raw_format=raw_format
    )
    
    # Step 2: Evaluate idempotency via RFC-01A (MANDATORY)
    event_id: Optional[str] = None
    idempotency_decision: str = "FLAG_AMBIGUOUS"
    
    try:
        # Parse raw payload to extract fields for idempotency check
        parsed_event = _parse_raw_payload(raw_bytes, raw_format)
        
        if parsed_event is None:
            warnings.append("Could not parse raw payload for idempotency evaluation")
            idempotency_decision = "FLAG_AMBIGUOUS"
        else:
            # Enrich with metadata for idempotency key generation
            parsed_event["source_system"] = source_system
            parsed_event["adapter_version"] = adapter_version
            parsed_event["observed_at"] = observed_at
            
            # Generate idempotency key
            key_generator = IdempotencyKeyGenerator(version="1.0.0")
            idempotency_key = key_generator.generate(parsed_event)
            
            # Check for duplicates
            if idempotency_key in _SEEN_EVENTS:
                idempotency_decision = "REJECT_DUPLICATE"
                event_id = _SEEN_EVENTS[idempotency_key]
            else:
                idempotency_decision = "ACCEPT"
                event_id = str(uuid.uuid4())
                _SEEN_EVENTS[idempotency_key] = event_id
    
    except Exception as e:
        warnings.append(f"Idempotency evaluation error: {type(e).__name__}: {str(e)}")
        idempotency_decision = "FLAG_AMBIGUOUS"
        event_id = None
    
    # Step 3: Timestamp management (never collapse)
    ingested_at = (_clock or datetime.now(timezone.utc)).isoformat()
    
    # Step 4: Create IngestRecord
    ingest_id = str(uuid.uuid4())
    
    status = "RECORDED" if not warnings else "RECORDED_WITH_WARNINGS"
    
    ingest_record = {
        "ingest_id": ingest_id,
        "event_id": event_id,
        "idempotency_decision": idempotency_decision,
        "source_system": source_system,
        "source_connector": source_connector,
        "source_environment": source_environment,
        "observed_at": observed_at,
        "ingested_at": ingested_at,
        "source_timestamp": source_timestamp,
        "raw_payload_hash": raw_payload_hash,
        "raw_pointer": raw_pointer,
        "raw_format": raw_format,
        "raw_size_bytes": raw_size_bytes,
        "ingest_protocol_version": "1.0.0",
        "adapter_version": adapter_version,
        "status": status,
        "warnings": warnings
    }
    
    # Step 5: Append to store (always, even for duplicates)
    ingest_record_store.append(ingest_record)
    
    return ingest_record


def _parse_raw_payload(raw_bytes: bytes, raw_format: str) -> Optional[Dict[str, Any]]:
    """
    Parse raw payload for idempotency evaluation.
    
    Args:
        raw_bytes: Raw payload bytes
        raw_format: Format identifier
    
    Returns:
        Parsed event dict or None if unparseable
    """
    if raw_format == "json":
        try:
            return json.loads(raw_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
    
    # Other formats not implemented (CSV/PDF require format-specific parsers)
    return None
