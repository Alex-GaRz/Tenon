"""
RFC-12 Change Control — Systemic Test: Replay Determinism

Validates minimal version resolution:
- Events before effective_at use original version
- Events after effective_at use new version
- Replay produces identical decisions

RFC: RFC-12 (Change Control)
Status: EARLY
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from core.change_control.version_registry import VersionRegistry
from core.change_control.version_resolver import VersionResolver
from core.change_control.change_types import ChangeType, Compatibility
from core.change_control.change_declaration import ChangeDeclaration, VersionTransition
from core.change_control.change_event_builder import ChangeEventBuilder


@pytest.fixture
def fixture_data():
    """Load upgrade history scenario fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "rfc12_change_control" / "scenario_upgrade_history.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


@pytest.fixture
def registry(fixture_data):
    """Create version registry from fixture data."""
    reg = VersionRegistry()
    
    for version_info in fixture_data["setup"]["versions"]:
        reg.register(
            component=fixture_data["setup"]["component"],
            version=version_info["version"],
            effective_at=datetime.fromisoformat(version_info["effective_at"].replace("Z", "+00:00")),
            description=version_info["description"]
        )
    
    return reg


@pytest.fixture
def resolver(registry):
    """Create version resolver."""
    return VersionResolver(registry)


def test_events_before_effective_date_use_original_version(resolver, fixture_data):
    """
    GIVEN: Events with timestamps before upgrade effective_at
    WHEN: Version is resolved for these events
    THEN: Original version (v1.0.0) is used
    """
    component = fixture_data["setup"]["component"]
    
    pre_upgrade_events = [
        e for e in fixture_data["test_events"]
        if e["expected_version"] == "v1.0.0"
    ]
    
    assert len(pre_upgrade_events) > 0
    
    for event in pre_upgrade_events:
        timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        resolved_entry = resolver.resolve(component, timestamp)
        
        assert resolved_entry is not None
        assert resolved_entry.version == event["expected_version"]


def test_events_after_effective_date_use_new_version(resolver, fixture_data):
    """
    GIVEN: Events with timestamps at or after upgrade effective_at
    WHEN: Version is resolved for these events
    THEN: New version (v2.0.0) is used
    """
    component = fixture_data["setup"]["component"]
    
    post_upgrade_events = [
        e for e in fixture_data["test_events"]
        if e["expected_version"] == "v2.0.0"
    ]
    
    assert len(post_upgrade_events) > 0
    
    for event in post_upgrade_events:
        timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        resolved_entry = resolver.resolve(component, timestamp)
        
        assert resolved_entry is not None
        assert resolved_entry.version == event["expected_version"]


def test_replay_produces_identical_decisions(registry, fixture_data):
    """
    GIVEN: A set of events processed once
    WHEN: Events are reprocessed (replayed)
    THEN: Version resolution produces identical results
    """
    component = fixture_data["setup"]["component"]
    
    resolver1 = VersionResolver(registry)
    first_pass = []
    
    for event in fixture_data["test_events"]:
        timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        entry = resolver1.resolve(component, timestamp)
        version = entry.version if entry else None
        first_pass.append((event["timestamp"], version))
    
    resolver2 = VersionResolver(registry)
    second_pass = []
    
    for event in fixture_data["test_events"]:
        timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        entry = resolver2.resolve(component, timestamp)
        version = entry.version if entry else None
        second_pass.append((event["timestamp"], version))
    
    assert first_pass == second_pass


def test_change_event_contains_only_minimal_fields():
    """
    GIVEN: A change declaration
    WHEN: ChangeEvent is built
    THEN: Event contains ONLY minimal required fields (no ledger/evidence)
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
    
    # Must have required fields
    required_fields = [
        "rfc_id",
        "effective_at",
        "components_impacted",
        "versions_affected",
        "change_type",
        "compatibility"
    ]
    
    for field in required_fields:
        assert field in event
    
    # Must NOT have ledger/evidence/persistence fields
    forbidden_fields = [
        "event_id",
        "ledger_ref",
        "persisted_at",
        "description",
        "migration_notes",
        "evidence_references"
    ]
    
    for field in forbidden_fields:
        assert field not in event
