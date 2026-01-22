# Tenon — Sistema de Verdad Financiera Operativa

**Constitución del Repositorio:** [RFC-00 — MANIFEST](docs/rfcs/RFC-00_MANIFEST.md)

Tenon es un sistema de verdad financiera operativa diseñado para observar, correlacionar y reconstruir eventos financieros de múltiples fuentes, detectar discrepancias, explicar causalidad y producir evidencia forense reproducible.

**Promesa fundamental:** Tenon puede demostrar "cómo sabe lo que sabe" y reproducirlo.

---

## Invariantes Constitucionales

Este sistema está regido por invariantes y no-goals definidos en el **RFC-00 — MANIFEST**:

- **Append-only:** ningún dato se borra ni sobrescribe
- **Trazabilidad total:** todo artefacto derivado referencia su origen + transformaciones + versiones
- **Determinismo:** mismo input histórico → mismo output
- **Idempotencia obligatoria:** reintentos no producen duplicados
- **Fallos explícitos:** el sistema nunca asume verdad sin evidencia

**No-Goals:** Tenon NO es sistema de pagos, contabilidad oficial, ERP, ni ejecuta transferencias.

Ver documentación completa: [docs/rfcs/RFC-00_MANIFEST.md](docs/rfcs/RFC-00_MANIFEST.md)

---

## Gobernanza y Control de Cambios

Este repositorio está protegido por políticas de gobernanza que aseguran que los invariantes se respeten:

- **Rutas protegidas:** `/core` y `/contracts` requieren protocolo de cambios
- **Inmutabilidad constitucional:** RFC-00 solo cambia vía RFC-00A_* (enmiendas)
- **CI enforcement:** todos los PRs pasan validaciones automáticas de invariantes

Ver políticas: [docs/governance/](docs/governance/)

---

## Tenon