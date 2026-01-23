"""
Systemic test: Replay determinism for identity and lineage.
RFC-01 + RFC-01A implementation.

Oracle: Same inputs + same versions → same identity decisions + same lineage.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from core.canonical_event.invariant_validator import InvariantValidator
from core.canonical_event.schema_validator import SchemaValidator
from core.canonical_ids.identity_decider import IdentityDecider, IdentityDecision
from core.canonical_ids.idempotency_key import IdempotencyKeyGenerator
from core.canonical_ids.lineage_validator import LineageValidator


class CanonicalEventProcessor:
    """Simulates end-to-end canonical event processing for systemic tests."""

    def __init__(
        self,
        normalizer_version="1.0.0",
        adapter_version="1.0.0",
        schema_version="1.0.0",
    ):
        self.normalizer_version = normalizer_version
        self.adapter_version = adapter_version
        self.schema_version = schema_version

        self.schema_validator = SchemaValidator()
        self.event_store_ids = set()  # For uniqueness validation
        self.invariant_validator = InvariantValidator(event_store=self.event_store_ids)
        self.key_generator = IdempotencyKeyGenerator(version="1.0.0")
        self.identity_decider = IdentityDecider(version="1.0.0")
        self.lineage_validator = LineageValidator(version="1.0.0")

        self.canonical_events = {}  # idempotency_key -> event
        self.identity_decisions = []  # List of all decisions
        self.event_counter = 0

    def canonicalize_raw_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw event to canonical format."""
        self.event_counter += 1

        # Map source to source_system enum
        source_map = {
            "BANK": "BANK",
            "PSP": "PSP",
            "ERP": "ERP",
            "MARKETPLACE": "MARKETPLACE",
        }

        # Map type to event_type enum
        type_map = {
            "payment": "PAYMENT_CAPTURED",
            "refund": "REFUND_SETTLED",
            "invoice": "PAYMENT_INITIATED",
            "adjustment": "ADJUSTMENT_POSTED",
        }

        # Map direction
        direction_map = {
            "inbound": "IN",
            "outbound": "OUT",
        }

        canonical = {
            "event_id": f"evt_systemic_{self.event_counter:04d}",
            "source_event_id": raw_event.get("transaction_id") or raw_event.get("invoice_id"),
            # FIX: Ensure external_reference is string (empty if None)
            "external_reference": raw_event.get("external_ref") or "",
            "source_system": source_map.get(raw_event.get("source"), "OTHER"),
            "source_connector": f"{raw_event.get('source', 'unknown').lower()}_connector",
            "source_environment": "PROD",
            "observed_at": raw_event.get("observed") or raw_event.get("timestamp"),
            "source_timestamp": raw_event.get("timestamp"),
            "event_type": type_map.get(raw_event.get("type"), "UNKNOWN"),
            "direction": direction_map.get(raw_event.get("direction"), "UNKNOWN"),
            "amount": raw_event.get("amount"),
            "currency": raw_event.get("currency", "UNKNOWN"),
            "raw_payload_hash": f"hash_{self.event_counter}",
            "raw_pointer": f"s3://bucket/raw/evt_{self.event_counter}.json",
            "raw_format": "JSON",
            "normalizer_version": self.normalizer_version,
            "adapter_version": self.adapter_version,
            "schema_version": self.schema_version,
            "idempotency_key": "",
            "idempotency_decision": "",  # Will be filled by process_event
            "lineage_links": [],
        }

        # Add lineage if related_to present
        if "related_to" in raw_event:
            # Find related event by source_event_id
            for key, existing in self.canonical_events.items():
                if existing.get("source_event_id") == raw_event["related_to"]:
                    link_type = "REFUND_OF" if raw_event.get("type") == "refund" else "ADJUSTMENT_OF"
                    canonical["lineage_links"].append(
                        {
                            "type": link_type,
                            "target_event_id": existing["event_id"],
                            "evidence": f"Related to {raw_event['related_to']}",
                            "version": "1.0.0",
                        }
                    )

        return canonical

    def process_event(self, canonical: Dict[str, Any]) -> Dict[str, Any]:
        """Process canonical event through identity decision."""

        # Invariant validation (Checks business rules, not schema strictness yet)
        inv_result = self.invariant_validator.validate(canonical)
        assert inv_result.valid, f"Invariant validation failed: {inv_result.violations}"

        # Generate idempotency key with version context
        key_event = canonical.copy()
        key_event["_canonicalization_context"] = (
            f"{self.normalizer_version}|{self.adapter_version}|{self.schema_version}"
        )
        idempotency_key = self.key_generator.generate(key_event)
        canonical["idempotency_key"] = idempotency_key

        # Make identity decision
        match = self.identity_decider.decide(
            idempotency_key,
            canonical,
            self.canonical_events,
        )

        canonical["idempotency_decision"] = match.decision.value

        # FIX: Validate Schema AFTER decision is populated
        schema_result = self.schema_validator.validate(canonical)
        assert schema_result.valid, f"Schema validation failed: {schema_result.errors}"

        # Record decision
        decision_record = self.identity_decider.build_identity_decision_record(
            idempotency_key,
            canonical["event_id"],
            match,
        )
        self.identity_decisions.append(decision_record)

        # Store if ACCEPT
        if match.decision == IdentityDecision.ACCEPT:
            self.canonical_events[idempotency_key] = canonical
            # Add to event store for uniqueness tracking
            self.event_store_ids.add(canonical["event_id"])

        return canonical

    def replay(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process all events and return results."""
        results = {
            "canonical_events": [],
            "decisions": [],
            "accept_count": 0,
            "reject_duplicate_count": 0,
            "flag_ambiguous_count": 0,
        }

        for raw in raw_events:
            canonical = self.canonicalize_raw_event(raw)
            processed = self.process_event(canonical)

            results["canonical_events"].append(processed)

            if processed["idempotency_decision"] == "ACCEPT":
                results["accept_count"] += 1
            elif processed["idempotency_decision"] == "REJECT_DUPLICATE":
                results["reject_duplicate_count"] += 1
            elif processed["idempotency_decision"] == "FLAG_AMBIGUOUS":
                results["flag_ambiguous_count"] += 1

        results["decisions"] = self.identity_decisions.copy()
        return results


# ... (El resto de la clase TestReplayIdentityAndLineageDeterminism se mantiene igual)
class TestReplayIdentityAndLineageDeterminism:
    """Test replay determinism for identity and lineage decisions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fixtures_dir = Path(__file__).parent / "fixtures" / "rfc01_rfc01a"

    def _load_scenario(self, filename: str) -> Dict[str, Any]:
        """Load scenario fixture from JSON."""
        filepath = self.fixtures_dir / filename
        with open(filepath, "r") as f:
            return json.load(f)

    def test_replay_multiple_sources_deterministic(self):
        scenario = self._load_scenario("scenario_multiple_sources.json")

        processor1 = CanonicalEventProcessor()
        results1 = processor1.replay(scenario["raw_events"])

        processor2 = CanonicalEventProcessor()
        results2 = processor2.replay(scenario["raw_events"])

        assert results1["accept_count"] == results2["accept_count"]
        assert results1["reject_duplicate_count"] == results2["reject_duplicate_count"]
        assert results1["accept_count"] == scenario["expected_accept_count"]

        keys1 = [d["idempotency_key"] for d in results1["decisions"]]
        keys2 = [d["idempotency_key"] for d in results2["decisions"]]
        assert keys1 == keys2

        decisions1 = [d["decision"] for d in results1["decisions"]]
        decisions2 = [d["decision"] for d in results2["decisions"]]
        assert decisions1 == decisions2

    def test_replay_out_of_order_deterministic(self):
        scenario = self._load_scenario("scenario_out_of_order.json")

        processor1 = CanonicalEventProcessor()
        results1 = processor1.replay(scenario["raw_events"])

        processor2 = CanonicalEventProcessor()
        results2 = processor2.replay(scenario["raw_events"])

        assert results1["accept_count"] == results2["accept_count"]
        assert results1["accept_count"] == scenario["expected_accept_count"]

        for event in results1["canonical_events"]:
            assert event["idempotency_decision"] == "ACCEPT"

    def test_replay_duplicate_retries_idempotent(self):
        scenario = self._load_scenario("scenario_duplicate_retries.json")

        processor1 = CanonicalEventProcessor()
        results1 = processor1.replay(scenario["raw_events"])

        processor2 = CanonicalEventProcessor()
        results2 = processor2.replay(scenario["raw_events"])

        assert results1["accept_count"] == scenario["expected_accept_count"]
        assert results1["reject_duplicate_count"] == scenario["expected_reject_duplicate_count"]
        assert results1["accept_count"] == results2["accept_count"]
        assert results1["reject_duplicate_count"] == results2["reject_duplicate_count"]

        decisions1 = [d["decision"] for d in results1["decisions"]]
        decisions2 = [d["decision"] for d in results2["decisions"]]
        assert decisions1 == decisions2
        assert decisions1 == ["ACCEPT", "REJECT_DUPLICATE", "REJECT_DUPLICATE"]

    def test_replay_ambiguous_collision_flagged(self):
        scenario = self._load_scenario("scenario_ambiguous_collision.json")

        processor1 = CanonicalEventProcessor()
        results1 = processor1.replay(scenario["raw_events"])

        processor2 = CanonicalEventProcessor()
        results2 = processor2.replay(scenario["raw_events"])

        assert results1["accept_count"] == scenario["expected_accept_count"]
        assert results1["flag_ambiguous_count"] == scenario["expected_flag_ambiguous_count"]
        assert results1["accept_count"] == results2["accept_count"]
        assert results1["flag_ambiguous_count"] == results2["flag_ambiguous_count"]

        decisions1 = [d["decision"] for d in results1["decisions"]]
        decisions2 = [d["decision"] for d in results2["decisions"]]
        assert decisions1 == decisions2

    def test_replay_lineage_append_only(self):
        scenario = self._load_scenario("scenario_lineage_chain.json")

        processor1 = CanonicalEventProcessor()
        results1 = processor1.replay(scenario["raw_events"])

        processor2 = CanonicalEventProcessor()
        results2 = processor2.replay(scenario["raw_events"])

        links1 = sum(len(e.get("lineage_links", [])) for e in results1["canonical_events"])
        links2 = sum(len(e.get("lineage_links", [])) for e in results2["canonical_events"])

        assert links1 == scenario["expected_lineage_links"]
        assert links1 == links2

        for e1, e2 in zip(results1["canonical_events"], results2["canonical_events"]):
            links1_types = [link["type"] for link in e1.get("lineage_links", [])]
            links2_types = [link["type"] for link in e2.get("lineage_links", [])]
            assert links1_types == links2_types

    def test_replay_with_different_versions_produces_different_keys(self):
        scenario = self._load_scenario("scenario_multiple_sources.json")

        processor_v1 = CanonicalEventProcessor(
            normalizer_version="1.0.0",
            adapter_version="1.0.0",
            schema_version="1.0.0",
        )
        results_v1 = processor_v1.replay(scenario["raw_events"])

        processor_v2 = CanonicalEventProcessor(
            normalizer_version="2.0.0",
            adapter_version="1.0.0",
            schema_version="1.0.0",
        )
        results_v2 = processor_v2.replay(scenario["raw_events"])

        assert len(results_v1["canonical_events"]) == len(results_v2["canonical_events"])

        for e1, e2 in zip(results_v1["canonical_events"], results_v2["canonical_events"]):
            assert e1["normalizer_version"] != e2["normalizer_version"]

        keys_v1 = [e["idempotency_key"] for e in results_v1["canonical_events"]]
        keys_v2 = [e["idempotency_key"] for e in results_v2["canonical_events"]]
        assert keys_v1 != keys_v2, "Different normalizer versions must produce different idempotency keys"

        processor_v2b = CanonicalEventProcessor(
            normalizer_version="2.0.0",
            adapter_version="1.0.0",
            schema_version="1.0.0",
        )
        results_v2b = processor_v2b.replay(scenario["raw_events"])

        keys_v2b = [e["idempotency_key"] for e in results_v2b["canonical_events"]]
        assert keys_v2 == keys_v2b, "Same version context must produce identical idempotency keys"

    def test_full_replay_end_to_end(self):
        scenario = self._load_scenario("scenario_multiple_sources.json")

        processor = CanonicalEventProcessor()
        results = processor.replay(scenario["raw_events"])

        validator = SchemaValidator()
        for event in results["canonical_events"]:
            schema_result = validator.validate(event)
            assert schema_result.valid, f"Schema validation failed: {schema_result.errors}"

        accepted_keys = [
            e["idempotency_key"]
            for e in results["canonical_events"]
            if e["idempotency_decision"] == "ACCEPT"
        ]
        assert len(accepted_keys) == len(set(accepted_keys)), "Duplicate keys in ACCEPT events"

        for decision in results["decisions"]:
            assert "evidence" in decision
            assert "reason" in decision["evidence"]

    def test_replay_missing_amount_rejected_explicitly(self):
        raw_event_missing_amount = {
            "source": "BANK",
            "transaction_id": "missing_amount_txn",
            "currency": "USD",
            "timestamp": "2026-01-22T10:00:00Z",
            "type": "payment",
        }

        processor = CanonicalEventProcessor()

        with pytest.raises(AssertionError) as exc_info:
            canonical = processor.canonicalize_raw_event(raw_event_missing_amount)
            processor.process_event(canonical)

        assert "Schema validation failed" in str(exc_info.value) or "validation" in str(exc_info.value).lower()
