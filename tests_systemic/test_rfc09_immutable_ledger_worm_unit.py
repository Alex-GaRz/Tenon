"""RFC-09 Immutable Ledger WORM - Unit Tests"""
import pytest
from core.immutable_ledger_worm.v1.ledger_entry import (
    LedgerEntry,
    LedgerEntryType,
    RetentionPolicy,
    sha256_hex,
)
from core.immutable_ledger_worm.v1.worm_ledger import WORMLedger


def test_sha256_hex():
    """sha256_hex computes correct hash"""
    data = b"test-content"
    hash_result = sha256_hex(data)
    assert len(hash_result) == 64
    assert hash_result == "0a3666a0710c08aa6d0de92ce72beeb5b93124cce1bf3701c9d6cdeb543cb73e"


def test_retention_policy_valid_utc():
    """RetentionPolicy accepts valid UTC timestamp"""
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )
    assert policy.immutable_until == "2033-01-23T10:00:00Z"


def test_retention_policy_invalid_utc():
    """RetentionPolicy rejects non-UTC timestamp"""
    with pytest.raises(ValueError, match="ISO-8601 UTC format ending in Z"):
        RetentionPolicy(
            retention_period="P7Y",
            immutable_until="2033-01-23T10:00:00"
        )


def test_ledger_entry_immutable():
    """LedgerEntry is immutable"""
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )
    entry = LedgerEntry(
        sequence_number=1,
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"test",
        content_hash="a" * 64,
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy,
        previous_entry_hash="0" * 64,
        entry_header_hash="b" * 64
    )

    with pytest.raises(AttributeError):
        entry.content = b"modified"


def test_worm_ledger_genesis_entry():
    """First entry in WORM ledger has previous_entry_hash of 64 zeros"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    entry = ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"genesis-content",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )

    assert entry.sequence_number == 1
    assert entry.previous_entry_hash == "0" * 64


def test_worm_ledger_chain_linking():
    """Subsequent entries link to previous entry's header hash"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    entry1 = ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"content-1",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )

    entry2 = ledger.append(
        entry_type=LedgerEntryType.STATE_CHECKPOINT,
        content=b"content-2",
        written_at="2026-01-23T10:00:01Z",
        retention_policy=policy
    )

    assert entry2.previous_entry_hash == entry1.entry_header_hash


def test_worm_ledger_sequence_monotonic():
    """Sequence numbers are monotonic starting from 1"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    entry1 = ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=b"content-1",
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )
    entry2 = ledger.append(
        entry_type=LedgerEntryType.AUDIT_RECORD,
        content=b"content-2",
        written_at="2026-01-23T10:00:01Z",
        retention_policy=policy
    )

    assert entry1.sequence_number == 1
    assert entry2.sequence_number == 2


def test_worm_ledger_content_hash_computed():
    """Content hash is computed from content"""
    ledger = WORMLedger()
    policy = RetentionPolicy(
        retention_period="P7Y",
        immutable_until="2033-01-23T10:00:00Z"
    )

    content = b"test-content"
    entry = ledger.append(
        entry_type=LedgerEntryType.EVIDENCE_SNAPSHOT,
        content=content,
        written_at="2026-01-23T10:00:00Z",
        retention_policy=policy
    )

    expected_hash = sha256_hex(content)
    assert entry.content_hash == expected_hash


def test_worm_ledger_verify_chain_valid():
    """verify_chain returns True for valid chain"""
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
