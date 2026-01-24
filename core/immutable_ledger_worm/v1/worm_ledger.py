"""RFC-09 Immutable Ledger WORM - WORM Ledger"""
from typing import Optional
from core.immutable_ledger_worm.v1.ledger_entry import (
    LedgerEntry,
    LedgerEntryType,
    RetentionPolicy,
    sha256_hex,
)


class WORMLedger:
    def __init__(self):
        self._entries: list[LedgerEntry] = []
        self._next_sequence: int = 1

    def append(
        self,
        entry_type: LedgerEntryType,
        content: bytes,
        written_at: str,
        retention_policy: RetentionPolicy,
    ) -> LedgerEntry:
        content_hash = sha256_hex(content)

        if self._next_sequence == 1:
            previous_entry_hash = "0" * 64
        else:
            previous_entry_hash = self._entries[-1].entry_header_hash

        header_canonical = (
            f"{self._next_sequence}|"
            f"{entry_type.value}|"
            f"{content_hash}|"
            f"{written_at}|"
            f"{previous_entry_hash}"
        )
        entry_header_hash = sha256_hex(header_canonical.encode('utf-8'))

        entry = LedgerEntry(
            sequence_number=self._next_sequence,
            entry_type=entry_type,
            content=content,
            content_hash=content_hash,
            written_at=written_at,
            retention_policy=retention_policy,
            previous_entry_hash=previous_entry_hash,
            entry_header_hash=entry_header_hash,
        )

        self._entries.append(entry)
        self._next_sequence += 1

        return entry

    def all(self) -> list[LedgerEntry]:
        return list(self._entries)

    def verify_chain(self) -> tuple[bool, Optional[str]]:
        if len(self._entries) == 0:
            return (True, None)

        for i, entry in enumerate(self._entries):
            computed_content_hash = sha256_hex(entry.content)
            if computed_content_hash != entry.content_hash:
                return (False, f"Content hash mismatch at sequence {entry.sequence_number}")

            if i == 0:
                expected_previous = "0" * 64
            else:
                expected_previous = self._entries[i - 1].entry_header_hash

            if entry.previous_entry_hash != expected_previous:
                return (False, f"Chain break at sequence {entry.sequence_number}")

            header_canonical = (
                f"{entry.sequence_number}|"
                f"{entry.entry_type.value}|"
                f"{entry.content_hash}|"
                f"{entry.written_at}|"
                f"{entry.previous_entry_hash}"
            )
            computed_header_hash = sha256_hex(header_canonical.encode('utf-8'))
            if computed_header_hash != entry.entry_header_hash:
                return (False, f"Header hash mismatch at sequence {entry.sequence_number}")

        return (True, None)
