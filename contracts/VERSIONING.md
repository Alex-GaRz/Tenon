# Contract Versioning Rules
- Semantic Versioning: MAJOR.MINOR.PATCH
- MAJOR: breaking change (requiere RFC de cambio)
- MINOR: extensión backward-compatible
- PATCH: corrección sin cambio semántico
Regla:
Todo cambio MAJOR requiere RFC aprobado y pruebas sistémicas.

---

## Registered Contracts

### CanonicalEvent
- **Current Version**: v1.0.0
- **Schema Location**: `contracts/canonical_event/v1.0.0/CanonicalEvent.schema.json`
- **RFC**: RFC-01 (CANONICAL EVENT) + RFC-01A (CANONICAL IDS & LINEAGE)
- **Status**: Initial release
- **Breaking Change Policy**:
  - Removing/renaming required fields → MAJOR bump + RFC required
  - Changing semantics of existing fields (e.g., `direction`, `amount`) → MAJOR bump + RFC required
  - Hardening validation (making optional fields required) → MAJOR bump + RFC required
  - Changes to closed enums (especially `event_type`) → MAJOR bump + RFC required
- **Non-Breaking Changes**:
  - Adding new optional fields → MINOR bump
  - Adding new metadata/records without affecting CanonicalEvent → MINOR/PATCH bump

### LineageLink
- **Current Version**: v1.0.0
- **Schema Location**: `contracts/canonical_ids/v1.0.0/LineageLink.schema.json`
- **RFC**: RFC-01A (CANONICAL IDS & LINEAGE)
- **Status**: Initial release
- **Breaking Change Policy**:
  - Changes to lineage type enum → MAJOR bump + RFC required
  - Removing required fields (`type`, `target_event_id`, `evidence`, `version`) → MAJOR bump + RFC required
- **Non-Breaking Changes**:
  - Adding new lineage types to enum → MINOR bump (with RFC approval)

### IdentityDecision
- **Current Version**: v1.0.0
- **Schema Location**: `contracts/canonical_ids/v1.0.0/IdentityDecision.schema.json`
- **RFC**: RFC-01A (CANONICAL IDS & LINEAGE)
- **Status**: Initial release (append-only metadata)
- **Breaking Change Policy**:
  - Changes to decision enum (`ACCEPT`, `REJECT_DUPLICATE`, `FLAG_AMBIGUOUS`) → MAJOR bump + RFC required
  - Removing required fields → MAJOR bump + RFC required
- **Non-Breaking Changes**:
  - Adding new optional evidence fields → MINOR bump
  - Extending evidence structure → MINOR bump

---

## Compatibility Matrix

| Contract | v1.0.0 | Future Versions |
|----------|--------|-----------------|
| CanonicalEvent | ✓ Initial | TBD |
| LineageLink | ✓ Initial | TBD |
| IdentityDecision | ✓ Initial | TBD |

**Note**: All validators MUST specify `schema_version` to ensure deterministic validation across replays.
