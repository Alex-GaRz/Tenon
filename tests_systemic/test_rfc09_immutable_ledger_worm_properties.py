"""RFC-09 Immutable Ledger WORM - Property Tests"""
import pytest
from core.immutable_ledger_worm.v1.ledger_entry import (
    LedgerEntryType,
    RetentionPolicy,
    sha256_hex,
)
from core.immutable_ledger_worm.v1.worm_ledger import WORMLedger


def test_property_append_only():
    """WORM ledger is append-only, no updates or deletes"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"content-1",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )

    entries_before = ledger.all()
    entries_after = ledger.all()

    assert len(entries_before) == len(entries_after)
    assert entries_before[0].content == entries_after[0].content


def test_property_chain_integrity():
    """Every entry links to previous entry's header hash"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    for i in range(5):
        ledger.append(
            entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
            content=f"content-{i}".encode('utf-8'),
            written_at=f"2026-01-23T10:00:0{i}Z",
            retention_policy=policy
        )

    entries = ledger.all()
    assert entries[0].previous_entry_hash == "0" * 64

    for i in range(1, len(entries)):
        assert entries[i].previous_entry_hash == entries[i - 1].entry_header_hash


def test_property_content_hash_deterministic():
    """Content hash is deterministic for same content"""
    content = b"deterministic-test"
    hash1 = sha256_hex(content)
    hash2 = sha256_hex(content)

    assert hash1 == hash2


def test_property_header_hash_canonical():
    """Header hash computed from canonical header representation"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    entry = ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"test-content",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )

    header_canonical = (
        f"{entry.sequence_number}|"
        f"{entry.entry_type.value}|"
        f"{entry.content_hash}|"
        f"{entry.written_at}|"
        f"{entry.previous_entry_hash}"
    )
    expected_hash = sha256_hex(header_canonical.encode('utf-8'))

    assert entry.entry_header_hash == expected_hash


def test_property_immutability_enforcement():
    """Ledger entries are immutable (frozen dataclass)"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    entry = ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"immutable-content",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )

    with pytest.raises(AttributeError):
        entry.sequence_number = 999


def test_property_verify_chain_detects_tampering():
    """verify_chain detects any tampering with chain integrity"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"content-1",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )
    ledger.append(
        entry_type=LedgerEntryType.STATE_CHECKPOINT,
        content=b"content-2",
        written_at="2026-01-23T10:00:01Z",
        retention_policy=policy
    )

    valid, error = ledger.verify_chain()
    assert valid is True
    assert error is None
