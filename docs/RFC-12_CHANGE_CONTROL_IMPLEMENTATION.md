# RFC-12 Change Control — Early Implementation

**Status**: EARLY  
**RFC**: RFC-12_CHANGE_CONTROL  
**Phase**: Minimal Operable Change Control

---

## SCOPE — EARLY PHASE

### What Is IN SCOPE

1. **Change Control Minimum Operable**
   - Classification of changes by type and compatibility
   - Effective date mechanism (`effective_at`)
   - Deterministic version resolution based on timestamp

2. **Versioned Coexistence**
   - Multiple versions of components coexist in `/contracts`
   - Version directories: `v1/`, `v2/`, etc.

3. **ChangeEvent Contract (Evidence)**
   - Structured schema for change declarations
   - Minimal required fields
   - Version 1.0.0 schema in `/contracts/change_control/v1/`

4. **Deterministic Version Resolution**
   - Resolution logic based on `effective_at` timestamp
   - Replay-safe: same input timestamp → same version

---

## NO-GOALS (OUT OF SCOPE)

1. **WORM Ledger Integration** — Persistence layer deferred to future RFC
2. **EvidenceEvent Persistence** — ChangeEvents are built but not persisted
3. **External Tooling** — No GitHub/Jira/Confluence integration
4. **Process Enforcement** — CI/CD pipeline modifications excluded
5. **Retroactive Operations** — No history rewriting, no backfills

---

## CHANGE TYPES

Changes are classified following semantic versioning:

- **Patch**: Bug fixes, documentation corrections (always backward-compatible)
- **Minor**: New functionality, non-breaking additions (backward-compatible)
- **Major**: Breaking changes, API modifications (explicitly breaking)

---

## COMPATIBILITY CLASSIFICATION

Every change must declare its compatibility impact:

- **backward-compatible**: Old code works with new version
- **forward-compatible**: New code can handle old data/schemas
- **breaking**: Requires migration, not compatible with previous versions

**RULE**: If `change_type == Major`, then `compatibility` MUST be `breaking`.

---

## EFFECTIVE DATE MECHANISM

All changes governed by `effective_at` timestamp (ISO 8601 UTC).

### Resolution Logic

```
if event.timestamp < change.effective_at:
    use original_version
else:
    use new_version
```

### Determinism Guarantee

- Same timestamp input → same version resolution
- Replay-safe: reprocessing historical events uses correct historical version

---

## CHANGE EVENT CONTRACT (v1)

### Required Fields

- `rfc_id` (string): RFC identifier authorizing the change
- `effective_at` (ISO 8601 UTC): Timestamp when change becomes active
- `components_impacted` (array): List of affected system components
- `versions_affected` (array): Version identifiers involved
- `change_type` (enum): Patch | Minor | Major
- `compatibility` (enum): backward-compatible | forward-compatible | breaking

### Schema Location

```
contracts/change_control/v1/change_event.schema.json
```

---

## EVIDENCE REQUIREMENTS

Every change MUST provide:

1. **RFC Authorization** — Valid RFC identifier
2. **Effective Date** — Explicit `effective_at` timestamp
3. **Impact Declaration** — Components affected, versions involved
4. **Audit Trail** — ChangeEvent evidence generated (no persistence required in early phase)

---

## LIMITS OF THIS IMPLEMENTATION

This early-phase implementation is **intentionally minimal**:

- ✅ Provides change governance framework
- ✅ Enables deterministic version resolution
- ✅ Establishes evidence contracts
- ❌ Does NOT persist evidence to ledger
- ❌ Does NOT integrate with CI/CD pipelines
- ❌ Does NOT enforce human approval workflows

---

**END OF IMPLEMENTATION DOCUMENT**
