# TENON — RFC EXECUTION STATUS
> Documento vivo de gobernanza institucional  
> Última actualización: 2026-01-22

Este documento registra el estado **ejecutable y verificable** de cada RFC del sistema TENON.
Un RFC **NO se considera completado** si no existe:
- Commit verificable
- Evidencia de tests
- Compatibilidad contractual documentada

---

## Leyenda de Estados
- **TODO**: RFC definido, no iniciado
- **IN-PROGRESS**: implementación en curso, no aprobada
- **PASS**: RFC ejecutado, auditado y aprobado por Control Tower

---

## Estado Global de RFCs

| RFC | Título | Estado | Rama / PR | Commit Hash | Evidencia de Tests | Notas de Compatibilidad |
|----|------|--------|-----------|-------------|--------------------|-------------------------|
| RFC-00 | Manifest & Governance | PASS | #1 | <82d40f8> | checks passed en PR #1 | Branch protection sin codeowners required (solo dev) |
| RFC-01 | Canonical Event | PASS | PR #2 → release/v1-tenon | <7341144> | ci-core + systemic replay OK | Compatible con contracts v1.0.0 |
| RFC-01A | Canonical IDs & Lineage | PASS | PR #2 → release/v1-tenon | <7341144> | identity + lineage tests OK | No breaking changes |
| RFC-02 | Ingest Append-Only | PASS | PR #6 → release/v1-tenon | <AD46884> | pytest tests_systemic/test_rfc02_ingest_append_only_* (PASS) | Contrato ingest v1 append-only. Compatible con Canon v1 |
| RFC-03 | Normalization Rules | PASS | PR #6 → release/v1-tenon | <AD46884> | pytest tests_systemic/test_rfc03_normalization_rules_* (PASS) | Normalization v1 determinística. Sin breaking changes |
| RFC-04 | Correlation Engine | TODO | — | — | — | — |
| RFC-05 | Money State Machine | TODO | — | — | — | — |
| RFC-06 | Discrepancy Taxonomy | TODO | — | — | — | — |
| RFC-07 | Causality Model | TODO | — | — | — | — |
| RFC-08 | Evidence Events | PASS | PR #8 → release/v1-tenon | <539AABC> | pytest tests_systemic/test_rfc08_event_sourcing_evidence_* (PASS) | Evidence events v1 append-only. Orden total y replay determinista |
| RFC-09 | Immutable Ledger (WORM) | PASS | PR #8 → release/v1-tenon | <539AABC> | pytest tests_systemic/test_rfc09_immutable_ledger_worm_* (PASS) | WORM ledger v1 con encadenamiento criptográfico canónico |
| RFC-10 | Idempotency Guardian | PASS | PR #5 → release/v1-tenon | <67b08a1> | python -m pytest tests_systemic\rfc10_idempotency_guardian -v (40 passed) | Contracts idempotency_guardian v1 (append-only; decisiones explícitas) |
| RFC-11 | Adapter Contracts | PASS | PR #9 → release/v1-tenon | <30b80db> | pytest tests_systemic/test_rfc11_adapter_contracts_registry.py tests_systemic/test_rfc11_adapter_contracts_conformance.py -v (PASS) | Boundary + registry + conformance suite v1. Contracts v1 schema-first |
| RFC-12 | Change Control | PASS | PR #4 → release/v1-tenon | <b175f32> | pytest tests_systemic/ -k rfc12 (7 passed) | Append-only. Nuevo contrato v1. Sin impacto en contratos existentes |
| RFC-13 | Risk Observability | TODO | — | — | — | — |

---

## Reglas de Actualización
- Solo se cambia a **PASS** desde la Control Tower
- Todo cambio debe incluir:
  - commit hash
  - comando de tests ejecutado
  - resultado resumido
- Cambios a `/contracts` deben reflejar versión y compatibilidad

---

## Autoridad
Este documento es gobernado por:
**TENON — CONTROL TOWER**

Ningún RFC se considera parte del producto si aquí no figura como **PASS**.
