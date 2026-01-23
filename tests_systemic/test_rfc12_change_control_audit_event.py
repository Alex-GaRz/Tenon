"""
RFC-12 Change Control — Systemic Test: Audit Event Generation

Validates minimal ChangeEvent evidence generation:
- Contains only required v1 fields
- Provides before/after state via effective_at
- Does not require ledger persistence

RFC: RFC-12 (Change Control)
Status: EARLY
"""

import pytest
from datetime import datetime, timezone

from core.change_control.change_types import ChangeType, Compatibility
from core.change_control.change_declaration import ChangeDeclaration, VersionTransition
from core.change_control.change_event_builder import ChangeEventBuilder


def test_change_event_contains_only_minimal_v1_fields():
    """
    GIVEN: A change declaration
    WHEN: ChangeEvent is built
    THEN: Event contains ONLY minimal required v1 fields
    """
    declaration = ChangeDeclaration(
        rfc_id="RFC-12",
        change_type=ChangeType.MINOR,
        compatibility=Compatibility.BACKWARD_COMPATIBLE,
        effective_at=datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        components_impacted=["canonical_event"],
        versions_affected=[
            VersionTransition(
                component="canonical_event",
                from_version="v1.0.0",
                to_version="v1.1.0"
            )
        ]
    )
    
    event = ChangeEventBuilder.build(declaration)
    
    # Required v1 fields
    required_fields = [
        "rfc_id",
        "effective_at",
        "components_impacted",
        "versions_affected",
        "change_type",
        "compatibility"
    ]
    
    for field in required_fields:
        assert field in event, f"Missing required field: {field}"
    
    # Must NOT have ledger/persistence fields
    forbidden_fields = [
        "event_id",
        "ledger_ref",
        "persisted_at",
        "description",
        "migration_notes",
        "evidence_references"
    ]
    
    for field in forbidden_fields:
        assert field not in event, f"Forbidden field present: {field}"


def test_before_after_state_explicable_by_effective_at():
    """
    GIVEN: A change declaration with effective_at
    WHEN: ChangeEvent is built
    THEN: Before/after state is explicable via versions_affected and effective_at
    """
    declaration = ChangeDeclaration(
        rfc_id="RFC-12",
        change_type=ChangeType.MAJOR,
        compatibility=Compatibility.BREAKING,
        effective_at=datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        components_impacted=["money_state_machine"],
        versions_affected=[
            VersionTransition(
                component="money_state_machine",
                from_version="v1.0.0",
                to_version="v2.0.0"
            )
        ]
    )
    
    event = ChangeEventBuilder.build(declaration)
    
    # Effective date present
    assert "effective_at" in event
    effective_at = datetime.fromisoformat(event["effective_at"].replace("Z", "+00:00"))
    assert effective_at == declaration.effective_at
    
    # Before/after state in versions_affected
    assert len(event["versions_affected"]) > 0
    version_entry = event["versions_affected"][0]
    
    before_version = version_entry["from_version"]
    after_version = version_entry["to_version"]
    
    assert before_version == "v1.0.0", "Before state captured"
    assert after_version == "v2.0.0", "After state captured"
    assert before_version != after_version, "Must show actual change"


def test_change_event_does_not_require_ledger():
    """
    GIVEN: A change declaration
    WHEN: ChangeEvent is built
    THEN: Event is returned as dict, NOT persisted to ledger
    
    Note: Ledger integration is out of scope for early-phase RFC-12.
    """
    declaration = ChangeDeclaration(
        rfc_id="RFC-12",
        change_type=ChangeType.PATCH,
        compatibility=Compatibility.BACKWARD_COMPATIBLE,
        effective_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
        components_impacted=["correlation_engine"],
        versions_affected=[
            VersionTransition("correlation_engine", "v1.0.0", "v1.0.1")
        ]
    )
    
    event = ChangeEventBuilder.build(declaration)
    
    # Should return a dict
    assert isinstance(event, dict)
    
    # Should NOT have persistence metadata
    assert "event_id" not in event
    assert "ledger_ref" not in event
    assert "persisted_at" not in event
