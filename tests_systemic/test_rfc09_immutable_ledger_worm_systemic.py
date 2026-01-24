"""RFC-09 Immutable Ledger WORM - Systemic Tests"""
import base64
import json
from pathlib import Path
from core.immutable_ledger_worm.v1.ledger_entry import (
    LedgerEntryType,
    RetentionPolicy,
    sha256_hex,
)
from core.immutable_ledger_worm.v1.worm_ledger import WORMLedger


def load_fixture(filename: str) -> dict:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "rfc09_immutable_ledger_worm" / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_systemic_chain_ok():
    """Valid WORM chain verifies successfully"""
    fixture = load_fixture("scenario_chain_ok.json")
    ledger = WORMLedger()
    entries = []
    
    for write in fixture["writes"]:
        content = base64.b64decode(write["content_base64"])
        policy = RetentionPolicy(
            retention_period=write["retention_policy_id"],
            immutable_until="2033-01-23T10:00:00Z"
        )
        entry = ledger.append(
            entry_type=LedgerEntryType[write["entry_type"]],
            content=content,
            written_at=write["written_at"],
            retention_policy=policy
        )
        entries.append(entry)

    assert len(entries) == 3
    assert entries[0].sequence_number == 1
    assert entries[1].sequence_number == 2
    assert entries[2].sequence_number == 3

    assert entries[0].previous_entry_hash == "0" * 64
    assert entries[1].previous_entry_hash == entries[0].entry_header_hash
    assert entries[2].previous_entry_hash == entries[1].entry_header_hash

    valid, error = ledger.verify_chain()
    assert valid is True
    assert error is None


def test_systemic_verify_chain_full():
    """verify_chain recalculates all hashes"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    content1 = b"evidence-snapshot-001"
    entry1 = ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=content1,
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )

    content2 = b"state-checkpoint-002"
    entry2 = ledger.append(
        entry_type=LedgerEntryType.STATE_CHECKPOINT,
        content=content2,
        written_at="2026-01-23T10:00:01Z",
        retention_policy=policy
    )

    valid, error = ledger.verify_chain()
    assert valid is True

    assert entry1.content_hash == sha256_hex(content1)
    assert entry2.content_hash == sha256_hex(content2)


def test_systemic_retention_policy():
    """Retention policy is stored with each entry"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    entry = ledger.append(
        entry_type=LedgerEntryType.AUDIT_RECORD,
        content=b"audit-data",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )

    assert entry.retention_policy.retention_period == "P7Y"
    assert entry.retention_policy.immutable_until == "2033-01-23T10:00:00Z"


def test_systemic_full_lifecycle():
    """Full lifecycle: append multiple entry types, verify chain"""
    ledger = WORMLedger()

    policy1 = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )
    entry1 = ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"snapshot-001",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy1
    )

    policy2 = RetentionPolicy(
        retention_period="P10Y",
        immutable_until="2036-01-23T10:00:01Z"
    )
    entry2 = ledger.append(
        entry_type=LedgerEntryType.STATE_CHECKPOINT,
        content=b"checkpoint-002",
        written_at="2026-01-23T10:00:01Z",
        retention_policy=policy2
    )

    policy3 = RetentionPolicy(
        retention_period="P5Y",
        immutable_until="2031-01-23T10:00:02Z"
    )
    entry3 = ledger.append(
        entry_type=LedgerEntryType.AUDIT_RECORD,
        content=b"audit-003",
        written_at="2026-01-23T10:00:02Z",
        retention_policy=policy3
    )

    policy4 = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:03Z"
    )
    entry4 = ledger.append(
        entry_type=LedgerEntryType.DISCREPANCY_LOG,
        content=b"discrepancy-004",
        written_at="2026-01-23T10:00:03Z",
        retention_policy=policy4
    )

    all_entries = ledger.all()
    assert len(all_entries) == 4

    assert all_entries[0].entry_type == LedgerEntryType.EVIDENCE_SNAPSHOT
    assert all_entries[1].entry_type == LedgerEntryType.STATE_CHECKPOINT
    assert all_entries[2].entry_type == LedgerEntryType.AUDIT_RECORD
    assert all_entries[3].entry_type == LedgerEntryType.DISCREPANCY_LOG

    valid, error = ledger.verify_chain()
    assert valid is True
    assert error is None


def test_systemic_genesis_entry_special():
    """Genesis entry (first entry) has special previous_entry_hash"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    genesis = ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"genesis-block",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )

    assert genesis.sequence_number == 1
    assert genesis.previous_entry_hash == "0000000000000000000000000000000000000000000000000000000000000000"

    valid, error = ledger.verify_chain()
    assert valid is True
